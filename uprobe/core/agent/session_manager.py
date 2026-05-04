import os
import uuid
import shutil
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, BinaryIO
from contextlib import contextmanager
from urllib.parse import urlparse

from pantheon.chatroom import ChatRoom
from pantheon.factory.template_io import UnifiedMarkdownParser
from pantheon.utils.vision import parse_image_mentions
from uprobe.core.agent.output_sandbox import apply_agent_runtime_env, resolve_agent_paths

logger = logging.getLogger(__name__)

_RUNTIME_ENV_KEYS = {
    "API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "http_proxy",
    "https_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
}
_RUNTIME_ENV_LOCK = asyncio.Lock()


def _clean_env_value(value: str) -> str:
    v = str(value).strip()
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        return v[1:-1]
    return v


def apply_model_api_key(model: str, api_key: Optional[str]) -> None:
    """Apply a user-provided API key to the environment variable used by the selected model."""
    if not api_key:
        return
    key = _clean_env_value(api_key)
    model_l = (model or "").lower()
    if "gemini" in model_l:
        os.environ["GEMINI_API_KEY"] = key
    elif "gpt" in model_l or "openai" in model_l:
        os.environ["OPENAI_API_KEY"] = key
    else:
        provider = model.split("/", 1)[0].upper() if "/" in model else ""
        os.environ[f"{provider}_API_KEY" if provider else "API_KEY"] = key


def resolve_agent_model(explicit: Optional[str]) -> str:
    m = (explicit or "").strip()
    if m:
        return m
    return "gpt-5.4"


def apply_proxy_environment(proxy: Optional[str]) -> None:
    """write proxy environment variables for httpx/LiteLLM etc. (including case sensitivity)."""
    if not proxy:
        return
    p = _clean_env_value(proxy)
    if not p:
        return
    parsed = urlparse(p)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Proxy must be a valid URL starting with http:// or https://")
    os.environ["http_proxy"] = p
    os.environ["https_proxy"] = p
    os.environ["HTTP_PROXY"] = p
    os.environ["HTTPS_PROXY"] = p
    os.environ["ALL_PROXY"] = p


@contextmanager
def agent_runtime_environment(
    model: str,
    api_key: Optional[str],
    api_base: Optional[str] = None,
    proxy: Optional[str] = None,
):
    """Temporarily apply per-request LLM credentials and proxy settings."""
    provider = model.split("/", 1)[0].upper() if model and "/" in model else ""
    keys = set(_RUNTIME_ENV_KEYS)
    if provider:
        keys.add(f"{provider}_API_KEY")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        apply_model_api_key(model, api_key)
        if api_base:
            os.environ["OPENAI_API_BASE"] = _clean_env_value(api_base)
        apply_proxy_environment(proxy)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class AgentSessionManager:
    """Manages agent sessions using Pantheon ChatRoom."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        output_dir: Path | None = None,
        memory_dir: Path | None = None,
    ):
        if workspace_root is None:
            workspace_root = Path(__file__).resolve().parents[3]
        entrypoint = "web" if output_dir is not None and memory_dir is not None else "cli"
        self.runtime_paths = resolve_agent_paths(
            entrypoint=entrypoint,
            workspace=workspace_root,
            output_dir=output_dir,
            memory_dir=memory_dir,
        )
        apply_agent_runtime_env(self.runtime_paths)
        self.workspace_root = self.runtime_paths.workspace_root
        # Use absolute path to the template file in the source code
        self.template_path = Path(__file__).resolve().parent / "templates" / "uprobe_team.md"
        self.protocol_template_path = Path(__file__).resolve().parent / "templates" / "DEFAULT_PROTOCOL.yaml"
        self.pantheon_memory_dir = self.runtime_paths.memory_root
        self.output_dir = self.runtime_paths.output_root
        self.chatroom = ChatRoom(memory_dir=str(self.pantheon_memory_dir), workspace_path=str(self.workspace_root))
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the ChatRoom and background services."""
        self._ensure_team_template_registered()
        # self._ensure_protocol_template_installed()
        
        # Set pantheon log level to DEBUG to print full agent execution output
        from pantheon.utils.log import set_level
        set_level("DEBUG")
        
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
            for aid in team_dict.get("agents") or []:
                if isinstance(aid, str) and isinstance(team_dict.get(aid), dict):
                    team_dict[aid]["model"] = model
                elif isinstance(aid, dict) and aid.get("id"):
                    aid["model"] = model
        return team_dict

    def _ensure_team_template_registered(self) -> Path:
        """Ensure uprobe_team.md is registered under .pantheon/teams."""
        dest_dir = self.workspace_root / ".pantheon" / "teams"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "uprobe_team.md"
        if not dest.exists() or self.template_path.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(self.template_path, dest)
        return dest

    def _ensure_protocol_template_installed(self) -> Path:
        """Ensure DEFAULT_PROTOCOL.yaml is present in the workspace root."""
        dest = self.workspace_root / "DEFAULT_PROTOCOL.yaml"
        # Skip copying DEFAULT_PROTOCOL.yaml to avoid cluttering the workspace
        # if not dest.exists() and self.protocol_template_path.exists():
        #     shutil.copy2(self.protocol_template_path, dest)
        #     logger.info(f"Installed protocol template to {dest}")
        return dest

    def _build_chat_message(self, content: str) -> List[dict]:
        """Build chat message with image support."""
        return parse_image_mentions(content)

    async def upload_file(self, session_id: str, file_obj: BinaryIO, filename: str, upload_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Save an uploaded file and return its metadata."""
        if upload_dir is None:
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

    async def create_session(self, model: Optional[str] = None, api_key: Optional[str] = None, api_base: Optional[str] = None, proxy: Optional[str] = None) -> str:
        """Start a new agent session with per-request model configuration."""
        resolved = resolve_agent_model(model)
        async with _RUNTIME_ENV_LOCK:
            with agent_runtime_environment(resolved, api_key, api_base, proxy):
                await self.initialize()
                create_res = await self.chatroom.create_chat("http-session")
                if not create_res.get("success"):
                    raise RuntimeError(f"Failed to create chat: {create_res.get('message')}")
                chat_id = create_res["chat_id"]
                try:
                    template = self._load_team_template(resolved)
                    setup_res = await self.chatroom.setup_team_for_chat(chat_id, template)
                    if not setup_res.get("success"):
                        raise RuntimeError(f"Failed to setup team: {setup_res.get('message')}")
                except Exception as e:
                    await self.chatroom.delete_chat(chat_id)
                    raise e
        self.sessions[chat_id] = {"chat_id": chat_id, "model": resolved}
        logger.info(f"Started agent session {chat_id} with model={resolved}")
        return chat_id

    async def chat(
        self,
        session_id: str,
        content: str,
        attachment_ids: Optional[List[str]] = None,
        process_step_message=None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        runtime_model = model or self.sessions.get(session_id, {}).get("model") or resolve_agent_model(None)
        async with _RUNTIME_ENV_LOCK:
            with agent_runtime_environment(runtime_model, api_key, api_base, proxy):
                response = await self.chatroom.chat(session_id, chat_message, process_step_message=process_step_message)
        return response

    async def rewind_and_rerun(
        self,
        session_id: str,
        user_turn_index: int,
        content: str,
        attachment_ids: Optional[List[str]] = None,
        process_step_message=None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        return await self.chat(
            session_id,
            content,
            attachment_ids,
            process_step_message=process_step_message,
            model=model,
            api_key=api_key,
            api_base=api_base,
            proxy=proxy,
        )

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


_INSTANCES: Dict[tuple[str, str, str], AgentSessionManager] = {}


def get_session_manager(workspace_root: Path | None = None, output_dir: Path | None = None, memory_dir: Path | None = None) -> AgentSessionManager:
    """Get or create the global session manager instance."""
    resolved_workspace = (workspace_root or Path(__file__).resolve().parents[3]).expanduser().resolve()
    entrypoint = "web" if output_dir is not None and memory_dir is not None else "cli"
    runtime_paths = resolve_agent_paths(
        entrypoint=entrypoint,
        workspace=resolved_workspace,
        output_dir=output_dir,
        memory_dir=memory_dir,
    )
    resolved_workspace = runtime_paths.workspace_root
    resolved_output = runtime_paths.output_root
    resolved_memory = runtime_paths.memory_root
    key = (str(resolved_workspace), str(resolved_output), str(resolved_memory))
    if key not in _INSTANCES:
        _INSTANCES[key] = AgentSessionManager(
            workspace_root=resolved_workspace,
            output_dir=resolved_output,
            memory_dir=resolved_memory,
        )
    manager = _INSTANCES[key]
    apply_agent_runtime_env(manager.runtime_paths)
    return manager
