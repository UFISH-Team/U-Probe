"""
JSON-backed storage for per-user agent conversations.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import fcntl


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""

    return datetime.now(timezone.utc).isoformat()


def safe_path_component(value: str) -> str:
    """Convert arbitrary user-controlled text into a safe path segment."""

    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return cleaned or "unknown"


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    """Provide an exclusive file lock for atomic JSON writes."""

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_json_file(path: Path, default: Any) -> Any:
    """Read a JSON file and gracefully fall back to a default value."""

    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON atomically to avoid corrupting files on concurrent writes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


class AgentStore:
    """Persist agent conversations, attachments, and session mappings by user."""

    def __init__(self, data_dir: Path, output_dir: Path, username: str):
        self.username = username
        self.user_key = safe_path_component(username)
        self.user_data_dir = data_dir / "agent" / "users" / self.user_key
        self.conversations_dir = self.user_data_dir / "conversations"
        self.index_file = self.conversations_dir / "index.json"
        self.sessions_file = self.user_data_dir / "sessions.json"
        self.user_output_dir = output_dir / "users" / self.user_key
        self.lock_file = self.user_data_dir / ".lock"

        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.user_output_dir.mkdir(parents=True, exist_ok=True)

    def conversation_file(self, conversation_id: str) -> Path:
        """Return the JSON path for a single conversation."""

        return self.conversations_dir / f"{conversation_id}.json"

    def conversation_output_dir(self, conversation_id: str) -> Path:
        """Return the output directory for one conversation."""

        path = self.user_output_dir / safe_path_component(conversation_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def conversation_upload_dir(self, conversation_id: str) -> Path:
        """Return the upload directory for one conversation."""

        path = self.conversation_output_dir(conversation_id) / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def conversation_memory_dir(self, conversation_id: str) -> Path:
        """Return the Pantheon memory directory for one conversation."""

        path = self.user_data_dir / "memory" / safe_path_component(conversation_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_conversations(self) -> list[dict[str, Any]]:
        """Return conversation summaries for the current user."""

        payload = read_json_file(
            self.index_file,
            {"user_id": self.user_key, "conversations": []},
        )
        return payload.get("conversations", [])

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Load one conversation document."""

        return read_json_file(self.conversation_file(conversation_id), None)

    def create_conversation(self, title: str = "New Conversation") -> dict[str, Any]:
        """Create and persist a new empty conversation."""

        conversation_id = f"conv_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        now = utc_now_iso()
        conversation = {
            "id": conversation_id,
            "title": title,
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "sessionId": None,
            "attachments": [],
            "tags": [],
            "version": 1,
        }
        self.save_conversation(conversation)
        return conversation

    def save_conversation(self, conversation: dict[str, Any]) -> dict[str, Any]:
        """Persist a full conversation and refresh its summary."""

        conversation = dict(conversation)
        conversation.setdefault("messages", [])
        conversation.setdefault("attachments", [])
        conversation.setdefault("tags", [])
        conversation.setdefault("version", 1)
        conversation.setdefault("createdAt", utc_now_iso())
        conversation["updatedAt"] = utc_now_iso()

        with file_lock(self.lock_file):
            atomic_write_json(self.conversation_file(conversation["id"]), conversation)
            index_payload = read_json_file(
                self.index_file,
                {"user_id": self.user_key, "conversations": []},
            )
            summaries = [
                summary
                for summary in index_payload.get("conversations", [])
                if summary.get("id") != conversation["id"]
            ]
            summaries.insert(0, self._build_summary(conversation))
            index_payload["user_id"] = self.user_key
            index_payload["conversations"] = sorted(
                summaries,
                key=lambda item: item.get("updatedAt", ""),
                reverse=True,
            )
            atomic_write_json(self.index_file, index_payload)
        return conversation

    def delete_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Delete one conversation and its related output directory."""

        conversation = self.get_conversation(conversation_id)
        with file_lock(self.lock_file):
            convo_file = self.conversation_file(conversation_id)
            if convo_file.exists():
                convo_file.unlink()
            index_payload = read_json_file(
                self.index_file,
                {"user_id": self.user_key, "conversations": []},
            )
            index_payload["conversations"] = [
                item
                for item in index_payload.get("conversations", [])
                if item.get("id") != conversation_id
            ]
            atomic_write_json(self.index_file, index_payload)
            sessions = read_json_file(self.sessions_file, {})
            if conversation_id in sessions:
                sessions.pop(conversation_id, None)
                atomic_write_json(self.sessions_file, sessions)
        output_dir = self.user_output_dir / safe_path_component(conversation_id)
        if output_dir.exists():
            import shutil

            shutil.rmtree(output_dir, ignore_errors=True)
        return conversation

    def update_title(self, conversation_id: str, title: str) -> dict[str, Any]:
        """Update the title of a conversation."""

        conversation = self.require_conversation(conversation_id)
        conversation["title"] = title.strip() or conversation["title"]
        return self.save_conversation(conversation)

    def clear_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Remove messages and pending attachments from a conversation."""

        conversation = self.require_conversation(conversation_id)
        conversation["messages"] = []
        conversation["attachments"] = []
        conversation["version"] = int(conversation.get("version", 1)) + 1
        self.clear_session(conversation_id)
        return self.save_conversation(conversation)

    def add_pending_attachment(
        self,
        conversation_id: str,
        attachment: dict[str, Any],
    ) -> dict[str, Any]:
        """Append an uploaded attachment to the pending conversation list."""

        conversation = self.require_conversation(conversation_id)
        attachments = [
            item
            for item in conversation.get("attachments", [])
            if item.get("id") != attachment.get("id")
        ]
        attachments.append(attachment)
        conversation["attachments"] = attachments
        conversation["version"] = int(conversation.get("version", 1)) + 1
        return self.save_conversation(conversation)

    def remove_pending_attachment(
        self,
        conversation_id: str,
        attachment_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Remove a pending attachment from a conversation."""

        conversation = self.require_conversation(conversation_id)
        removed = None
        remaining = []
        for attachment in conversation.get("attachments", []):
            if attachment.get("id") == attachment_id and removed is None:
                removed = attachment
                continue
            remaining.append(attachment)
        conversation["attachments"] = remaining
        conversation["version"] = int(conversation.get("version", 1)) + 1
        return self.save_conversation(conversation), removed

    def get_pending_attachment(
        self,
        conversation_id: str,
        attachment_id: str,
    ) -> dict[str, Any] | None:
        """Return one pending attachment by id."""

        conversation = self.require_conversation(conversation_id)
        for attachment in conversation.get("attachments", []):
            if attachment.get("id") == attachment_id:
                return attachment
        return None

    def get_attachments_by_ids(
        self,
        conversation_id: str,
        attachment_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Return attachments by id from both pending and persisted messages."""

        if not attachment_ids:
            return []
        wanted = set(attachment_ids)
        conversation = self.require_conversation(conversation_id)
        found: dict[str, dict[str, Any]] = {}
        for attachment in conversation.get("attachments", []):
            attachment_id = attachment.get("id")
            if attachment_id in wanted:
                found[str(attachment_id)] = attachment
        for message in conversation.get("messages", []):
            for attachment in message.get("attachments", []) or []:
                attachment_id = attachment.get("id")
                if attachment_id in wanted and str(attachment_id) not in found:
                    found[str(attachment_id)] = attachment
        return [found[attachment_id] for attachment_id in attachment_ids if attachment_id in found]

    def replace_messages(
        self,
        conversation_id: str,
        messages: list[dict[str, Any]],
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Replace messages and optionally pending attachments."""

        conversation = self.require_conversation(conversation_id)
        conversation["messages"] = messages
        if attachments is not None:
            conversation["attachments"] = attachments
        if conversation["title"] == "New Conversation":
            for message in messages:
                if message.get("sender") == "user" and message.get("content"):
                    content = str(message["content"]).strip()
                    if content:
                        conversation["title"] = (
                            content[:50] + ("..." if len(content) > 50 else "")
                        )
                        break
        conversation["version"] = int(conversation.get("version", 1)) + 1
        return self.save_conversation(conversation)

    def set_session(self, conversation_id: str, session_id: str) -> None:
        """Associate a backend agent session with one conversation."""

        conversation = self.require_conversation(conversation_id)
        with file_lock(self.lock_file):
            sessions = read_json_file(self.sessions_file, {})
            sessions[conversation_id] = {
                "session_id": session_id,
                "updatedAt": utc_now_iso(),
            }
            atomic_write_json(self.sessions_file, sessions)
        conversation["sessionId"] = session_id
        self.save_conversation(conversation)

    def get_session(self, conversation_id: str) -> str | None:
        """Return the backend session id for one conversation."""

        sessions = read_json_file(self.sessions_file, {})
        session = sessions.get(conversation_id) or {}
        session_id = session.get("session_id")
        if session_id:
            return str(session_id)
        conversation = self.get_conversation(conversation_id)
        if conversation:
            return conversation.get("sessionId")
        return None

    def clear_session(self, conversation_id: str) -> None:
        """Remove the backend session mapping for one conversation."""

        with file_lock(self.lock_file):
            sessions = read_json_file(self.sessions_file, {})
            if conversation_id in sessions:
                sessions.pop(conversation_id, None)
                atomic_write_json(self.sessions_file, sessions)
        conversation = self.get_conversation(conversation_id)
        if conversation is not None:
            conversation["sessionId"] = None
            self.save_conversation(conversation)

    def require_conversation(self, conversation_id: str) -> dict[str, Any]:
        """Load one conversation or raise a file-style error."""

        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            raise FileNotFoundError(conversation_id)
        return conversation

    def _build_summary(self, conversation: dict[str, Any]) -> dict[str, Any]:
        """Build a compact summary for the conversation index."""

        preview = ""
        for message in reversed(conversation.get("messages", [])):
            content = str(message.get("content") or "").strip()
            if content:
                preview = content[:120]
                break
        return {
            "id": conversation["id"],
            "title": conversation.get("title", "New Conversation"),
            "createdAt": conversation.get("createdAt"),
            "updatedAt": conversation.get("updatedAt"),
            "sessionId": conversation.get("sessionId"),
            "attachments": conversation.get("attachments", []),
            "tags": conversation.get("tags", []),
            "lastMessagePreview": preview,
            "messageCount": len(conversation.get("messages", [])),
            "version": conversation.get("version", 1),
        }
