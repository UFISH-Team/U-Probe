import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, BinaryIO

from pantheon.chatroom import ChatRoom
from pantheon.factory.template_io import UnifiedMarkdownParser
from pantheon.utils.vision import parse_image_mentions

logger = logging.getLogger(__name__)


class AgentSessionManager:
    """Manages agent sessions using Pantheon ChatRoom."""

    def __init__(self, workspace_root: Path | None = None):
        if workspace_root is None:
            workspace_root = Path(__file__).resolve().parents[2]
        self.workspace_root = workspace_root
        self.template_path = self.workspace_root / "uprobe" / "agent" / "templates" / "uprobe_team.md"
        self.protocol_template_path = self.workspace_root / "uprobe" / "agent" / "templates" / "DEFAULT_PROTOCOL.yaml"
        self.pantheon_memory_dir = self.workspace_root / ".pantheon" / "memory"
        self.output_dir = Path(os.environ.get("UPROBE_OUTPUT_DIR", str(self.workspace_root / "uprobe-http" / "outputs")))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chatroom = ChatRoom(memory_dir=str(self.pantheon_memory_dir), workspace_path=str(self.workspace_root))
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the ChatRoom and background services."""
        self._ensure_team_template_registered()
        self._ensure_protocol_template_installed()
        await self.chatroom.run_setup()

    def _load_team_template(self, model: Optional[str]) -> Dict[str, Any]:
        """Load and configure the team template."""
        # Template is already ensured in initialize(), but we resolve the path again to be safe
        team_template_path = self.workspace_root / ".pantheon" / "teams" / "uprobe_team.md"
        if not team_template_path.exists():
             # Fallback if initialize wasn't called or file was deleted
             team_template_path = self._ensure_team_template_registered()
             
        parser = UnifiedMarkdownParser()
        team_config = parser.parse_file(team_template_path)
        team_dict = team_config.to_dict()
        team_dict["type"] = "team"
        team_dict["source_path"] = str(team_template_path)
        if model:
            for agent_cfg in team_dict.get("agents", []):
                if isinstance(agent_cfg, dict):
                    agent_cfg["model"] = model
        return team_dict

    def _ensure_team_template_registered(self) -> Path:
        """Ensure uprobe_team.md is registered under .pantheon/teams."""
        dest_dir = self.workspace_root / ".pantheon" / "teams"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "uprobe_team.md"
        if not dest.exists():
            shutil.copy2(self.template_path, dest)
        return dest

    def _ensure_protocol_template_installed(self) -> Path:
        """Ensure DEFAULT_PROTOCOL.yaml is present in the workspace root."""
        dest = self.workspace_root / "DEFAULT_PROTOCOL.yaml"
        if not dest.exists() and self.protocol_template_path.exists():
            shutil.copy2(self.protocol_template_path, dest)
            logger.info(f"Installed protocol template to {dest}")
        return dest

    def _build_chat_message(self, content: str) -> List[dict]:
        """Build chat message with image support."""
        return parse_image_mentions(content)

    async def upload_file(self, session_id: str, file_obj: BinaryIO, filename: str) -> Dict[str, Any]:
        """Save an uploaded file and return its metadata."""
        upload_dir = self.output_dir / "uploads" / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        safe_filename = Path(filename).name
        file_path = upload_dir / safe_filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file_obj, f)
        size = file_path.stat().st_size
        logger.info(f"Saved uploaded file to {file_path}")
        if session_id in self.sessions:
            if "uploads" not in self.sessions[session_id]:
                self.sessions[session_id]["uploads"] = {}
            self.sessions[session_id]["uploads"][file_id] = {"path": str(file_path), "filename": safe_filename, "size": size}
        return {"id": file_id, "filename": safe_filename, "path": str(file_path), "size": size}

    async def create_session(self, model: str = "gpt-4", api_key: Optional[str] = None, proxy: Optional[str] = None) -> str:
        """Start a new agent session."""
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        if proxy:
            os.environ["http_proxy"] = proxy
            os.environ["https_proxy"] = proxy
        await self.initialize()
        create_res = await self.chatroom.create_chat("http-session")
        if not create_res.get("success"):
            raise RuntimeError(f"Failed to create chat: {create_res.get('message')}")
        chat_id = create_res["chat_id"]
        try:
            template = self._load_team_template(model)
            setup_res = await self.chatroom.setup_team_for_chat(chat_id, template)
            if not setup_res.get("success"):
                raise RuntimeError(f"Failed to setup team: {setup_res.get('message')}")
        except Exception as e:
            await self.chatroom.delete_chat(chat_id)
            raise e
        self.sessions[chat_id] = {"chat_id": chat_id, "model": model}
        logger.info(f"Started agent session {chat_id} with model={model}")
        return chat_id

    async def chat(self, session_id: str, content: str, attachment_ids: Optional[List[str]] = None, process_step_message=None) -> Dict[str, Any]:
        """Send a message to an active session."""
        if session_id not in self.sessions:
            pass
        if attachment_ids is None:
            attachment_ids = []
        if attachment_ids and session_id in self.sessions:
            uploads = self.sessions[session_id].get("uploads", {})
            attached_files = []
            for aid in attachment_ids:
                if aid in uploads:
                    attached_files.append(uploads[aid])
            if attached_files:
                file_context = "\n\nUser uploaded the following files:\n"
                for f in attached_files:
                    file_context += f"- {f['filename']} (Path: {f['path']})\n"
                content += file_context
        chat_message = self._build_chat_message(content)
        response = await self.chatroom.chat(session_id, chat_message, process_step_message=process_step_message)
        return response

    async def rewind_and_rerun(self, session_id: str, user_turn_index: int, content: str, attachment_ids: Optional[List[str]] = None, process_step_message=None) -> Dict[str, Any]:
        """Rewind chat history to a user turn and rerun from edited content."""
        if session_id not in self.sessions:
            pass
        if attachment_ids is None:
            attachment_ids = []
        try:
            await self.chatroom.stop_chat(session_id)
        except Exception:
            pass
        memory = self.chatroom.memory_manager.get_memory(session_id)
        user_turns = memory.get_user_turns()
        if user_turn_index < 0 or user_turn_index >= len(user_turns):
            raise ValueError("Invalid user_turn_index")
        target_index = user_turns[user_turn_index][0]
        memory.revert_to_message(target_index)
        try:
            await memory.flush()
        except Exception:
            pass
        return await self.chat(session_id, content, attachment_ids, process_step_message=process_step_message)

    async def delete_upload(self, session_id: str, attachment_id: str) -> bool:
        """Delete an uploaded file by attachment id."""
        uploads = self.sessions.get(session_id, {}).get("uploads", {})
        meta = uploads.pop(attachment_id, None)
        if not meta:
            return False
        file_path = Path(meta.get("path", ""))
        if file_path.exists():
            file_path.unlink()
        return True

    async def stop_session(self, session_id: str) -> bool:
        """Stop and clean up a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        try:
            await self.chatroom.stop_chat(session_id)
        except Exception:
            pass
        result = await self.chatroom.delete_chat(session_id)
        return result.get("success", False)


_INSTANCE: Optional[AgentSessionManager] = None


def get_session_manager() -> AgentSessionManager:
    """Get or create the global session manager instance."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = AgentSessionManager()
    return _INSTANCE
