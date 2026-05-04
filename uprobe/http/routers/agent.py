import os
import re
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Awaitable, AsyncIterator
from pathlib import Path
from urllib.parse import urlparse, unquote

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from uprobe.core.agent.output_sandbox import apply_agent_runtime_env, resolve_agent_paths
from uprobe.core.agent.session_manager import get_session_manager
from uprobe.http.utils.paths import get_output_dir, get_data_dir, get_server_root, get_workspace_outputs_dir
from uprobe.http.utils.agent_store import AgentStore
from uprobe.http.routers.auth import get_current_active_user, User

agent_router = APIRouter(prefix="/agent", tags=["agent"])

DATA_DIR = get_data_dir()
OUTPUT_DIR = get_output_dir()


def apply_agent_resource_environment(output_dir: Path, memory_dir: Path) -> None:
    """Expose canonical project/resource/output paths to the agent runtime."""
    paths = resolve_agent_paths(
        entrypoint="web",
        workspace=get_server_root(),
        output_dir=output_dir,
        memory_dir=memory_dir,
    )
    apply_agent_runtime_env(paths)


def _clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        v = v[1:-1].strip()
    return v or None


def _validate_proxy(proxy: Optional[str]) -> Optional[str]:
    p = _clean_optional(proxy)
    if not p:
        return None
    parsed = urlparse(p)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Proxy must be a valid URL starting with http:// or https://")
    return p


def _require_agent_runtime_config(model: Optional[str], api_key: Optional[str], proxy: Optional[str]) -> tuple[str, str, Optional[str]]:
    resolved_model = _clean_optional(model)
    resolved_api_key = _clean_optional(api_key)
    if not resolved_model or not resolved_api_key:
        raise HTTPException(
            status_code=400,
            detail="Agent model and API key are required for this request. Configure them in Agent Configuration.",
        )
    return resolved_model, resolved_api_key, _validate_proxy(proxy)


async def _run_chat_with_client_disconnect(
    request: Request,
    sm,
    session_id: str,
    chat_runner: Callable[[], Awaitable[Any]],
) -> Any:
    """Run a long pantheon chat coroutine; stop the chat if the HTTP client disconnects."""
    chat_task = asyncio.create_task(chat_runner())

    async def disconnect_watcher() -> None:
        try:
            while True:
                if chat_task.done():
                    return
                try:
                    if await request.is_disconnected():
                        logging.info(
                            "Agent HTTP client disconnected; stopping pantheon chat %s",
                            session_id,
                        )
                        try:
                            await sm.chatroom.stop_chat(session_id)
                        except Exception as exc:
                            logging.warning("stop_chat after disconnect failed: %s", exc)
                        chat_task.cancel()
                        return
                except Exception:
                    pass
                await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            pass

    watcher_task = asyncio.create_task(disconnect_watcher())
    try:
        return await chat_task
    except asyncio.CancelledError:
        logging.info("Agent chat task cancelled for session %s", session_id)
        try:
            await sm.chatroom.stop_chat(session_id)
        except Exception:
            pass
        raise HTTPException(status_code=499, detail="Client disconnected")
    finally:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass


def _http_error_detail(text: str, max_len: int = 2500) -> str:
    t = (text or "").strip() or "Error"
    if len(t) > max_len:
        return t[: max_len - 1] + "…"
    return t


def _safe_resolved_file_under_root(output_root: Path, candidate: Path) -> Path | None:
    """Return candidate if it is a regular file under output_root; else None."""

    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved.is_file():
        return None
    try:
        resolved.relative_to(output_root)
    except ValueError:
        return None
    return resolved


def _resolve_conversation_artifact_path(
    output_root: Path,
    file_path: str,
    allowed_suffixes: set[str],
) -> Path | None:
    """
    Resolve a relative URL path to a regular file under ``output_root``.

    Used for each conversation sandbox (under ``results/users/...``) and, on miss, for the
    workspace ``outputs`` tree (see ``get_workspace_outputs_dir``).
    """

    requested = Path(file_path)
    if requested.is_absolute() or any(part == ".." for part in requested.parts):
        return None
    suffix = requested.suffix.lower()
    if suffix not in allowed_suffixes:
        return None

    output_root = output_root.resolve()

    hit = _safe_resolved_file_under_root(output_root, output_root / requested)
    if hit:
        return hit

    parts = requested.parts
    if not parts or parts[0] != "agent_runs":
        hit = _safe_resolved_file_under_root(output_root, output_root / "agent_runs" / requested)
        if hit:
            return hit

    for i, part in enumerate(parts):
        if part == "agent_runs":
            tail = Path(*parts[i:])
            hit = _safe_resolved_file_under_root(output_root, output_root / tail)
            if hit:
                return hit
            break

    s = file_path.replace("\\", "/")
    m = re.search(r"/users/[^/]+/[^/]+/(.+)$", s)
    if m:
        sub = Path(m.group(1))
        if not sub.is_absolute() and ".." not in sub.parts:
            hit = _safe_resolved_file_under_root(output_root, output_root / sub)
            if hit:
                return hit
            hit = _safe_resolved_file_under_root(output_root, output_root / "agent_runs" / sub)
            if hit:
                return hit

    if len(parts) == 1:
        ar = output_root / "agent_runs"
        if ar.is_dir():
            name = requested.name
            matches = [
                p
                for p in ar.glob(f"**/{name}")
                if p.is_file() and p.suffix.lower() in allowed_suffixes
            ]
            if len(matches) == 1:
                return _safe_resolved_file_under_root(output_root, matches[0])

    return None


def get_agent_store(current_user: User = Depends(get_current_active_user)) -> AgentStore:
    return AgentStore(data_dir=DATA_DIR, output_dir=OUTPUT_DIR, username=current_user.username)

def get_conversation_session_manager(store: AgentStore, conversation_id: str):
    output_dir = store.conversation_output_dir(conversation_id)
    memory_dir = store.conversation_memory_dir(conversation_id)
    apply_agent_resource_environment(output_dir, memory_dir)
    return get_session_manager(
        workspace_root=get_server_root(),
        output_dir=output_dir,
        memory_dir=memory_dir
    )


def sync_attachments_to_session(
    manager,
    session_id: str,
    attachments: List[dict[str, Any]],
) -> None:
    """Populate the manager upload registry from persisted attachment metadata."""

    session_meta = manager.sessions.setdefault(session_id, {"chat_id": session_id})
    uploads = session_meta.setdefault("uploads", {})
    for attachment in attachments:
        attachment_id = attachment.get("id")
        path = attachment.get("path")
        filename = attachment.get("filename")
        if not attachment_id or not path or not filename:
            continue
        uploads[str(attachment_id)] = {
            "path": str(path),
            "filename": str(filename),
            "size": int(attachment.get("size", 0)),
        }

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"

class RenameConversationRequest(BaseModel):
    title: str

class MessageRequest(BaseModel):
    content: str
    attachment_ids: List[str] = []
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    proxy: Optional[str] = None

class RewindRequest(BaseModel):
    user_turn_index: int
    content: str
    attachment_ids: List[str] = []
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    proxy: Optional[str] = None

class MessageResponse(BaseModel):
    thinking: List[str]
    message: str
    process: List[Dict[str, Any]] = Field(default_factory=list)

class UploadResponse(BaseModel):
    id: str
    filename: str
    url: str
    mime_type: str
    size: int


@agent_router.get("/conversations")
async def list_conversations(store: AgentStore = Depends(get_agent_store)):
    return store.list_conversations()

@agent_router.post("/conversations")
async def create_conversation(req: CreateConversationRequest, store: AgentStore = Depends(get_agent_store)):
    return store.create_conversation(title=req.title or "New Conversation")

@agent_router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, store: AgentStore = Depends(get_agent_store)):
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@agent_router.patch("/conversations/{conversation_id}")
async def rename_conversation(conversation_id: str, req: RenameConversationRequest, store: AgentStore = Depends(get_agent_store)):
    try:
        return store.update_title(conversation_id, req.title)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

@agent_router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, store: AgentStore = Depends(get_agent_store)):
    session_id = store.get_session(conversation_id)
    if session_id:
        sm = get_conversation_session_manager(store, conversation_id)
        await sm.stop_session(session_id)
    try:
        store.delete_conversation(conversation_id)
        return {"status": "deleted"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")


def _process_thinking_steps(thinking_steps: List[str], final_text: str) -> str:
    def sanitize_text(text: str) -> str:
        if not text: return ""
        return text.strip()
    
    cleaned_final = sanitize_text(str(final_text or ""))
    if thinking_steps and cleaned_final and thinking_steps[-1].strip() == cleaned_final.strip():
        thinking_steps.pop()
    
    def normalize_for_compare(text: str) -> str:
        t = text.replace("\r\n", "\n")
        t = re.sub(r"\\n", "\n", t)
        t = re.sub(r"[\u2018\u2019]", "'", t)
        t = re.sub(r"[\u201C\u201D]", '"', t)
        t = re.sub(r"\s+", " ", t).strip()
        return t
        
    parts: List[str] = []
    if thinking_steps:
        parts.append("\n".join(thinking_steps))
    if cleaned_final:
        parts.append(cleaned_final)
        
    if len(parts) >= 2:
        a, b = normalize_for_compare(parts[0]), normalize_for_compare(parts[1])
        if a == b or a in b or b in a:
            merged = parts[0] if len(a) >= len(b) and a in b else parts[1]
            parts = [merged]
            
    combined = "\n\n".join(parts).replace("\r\n", "\n")
    paragraphs = re.split(r"\n\s*\n+", combined)
    seen = set()
    unique_paragraphs: List[str] = []
    for p in paragraphs:
        key = normalize_for_compare(p)
        if not key or key in seen: continue
        seen.add(key)
        unique_paragraphs.append(p)
        
    display_text = "\n\n".join(unique_paragraphs).strip()
    
    def add_emoji_cues_preserve_code(text: str) -> str:
        if not text: return text
        parts = re.split(r"(```[\s\S]*?```)", text)
        def enhance_segment(seg: str) -> str:
            lines = seg.split('\n')
            enhanced: List[str] = []
            for ln in lines:
                base = ln.lstrip()
                prefix_ws = ln[:len(ln) - len(base)]
                lower = base.lower()
                if re.match(r"^(great[—\-]let['’`]?s|let['’`]?s)", lower):
                    if not base.startswith('🚀'): base = '🚀 ' + base
                if re.match(r"^[-*] ", base):
                    content = base[2:].strip()
                    lc = content.lower()
                    if ('gene' in lc and 'name' in lc) and not content.startswith('🧬'): content = '🧬 ' + content
                    elif ('species' in lc) and not content.startswith('🧫'): content = '🧫 ' + content
                    elif ('barcode' in lc) and not content.startswith('🏷️'): content = '🏷️ ' + content
                    elif any(k in lc for k in ['template', 'structure', 'probes']) and not content.startswith('🧩'): content = '🧩 ' + content
                    elif ('yaml' in lc) and not content.startswith('📄'): content = '📄 ' + content
                    base = '- ' + content
                else:
                    if any(k in lower for k in ['result', 'results', 'success', 'completed']):
                        if not base.startswith('✅'): base = '✅ ' + base
                    if any(k in lower for k in ['error', 'failed', 'failure']):
                        if not base.startswith('❌'): base = '❌ ' + base
                    if 'warning' in lower and not base.startswith('⚠️'):
                        if not base.startswith('⚠️'): base = '⚠️ ' + base
                enhanced.append(prefix_ws + base)
            return '\n'.join(enhanced)
        out_segments: List[str] = []
        for idx, p in enumerate(parts):
            if idx % 2 == 1 and p.startswith('```'): out_segments.append(p)
            else: out_segments.append(enhance_segment(p))
        return ''.join(out_segments)
        
    return add_emoji_cues_preserve_code(display_text)


def _extract_tool_names(tool_calls: Any) -> List[str]:
    names: List[str] = []
    if not isinstance(tool_calls, list):
        return names
    for c in tool_calls:
        if not isinstance(c, dict):
            names.append(str(c)[:120])
            continue
        fn = c.get("function")
        name = None
        if isinstance(fn, dict):
            name = fn.get("name")
        if not name:
            name = c.get("name")
        if name:
            names.append(str(name))
        else:
            names.append(str(c.get("id", "tool"))[:80])
    return names


def _apply_step_messages(step_message: Any, thinking_steps: List[str]) -> List[Dict[str, Any]]:
    """Build SSE payloads for one pantheon step; append leader assistant text to thinking_steps."""
    events: List[Dict[str, Any]] = []
    try:
        if not isinstance(step_message, dict):
            return events
        agent_raw = step_message.get("agent_name", "")
        agent_name = str(agent_raw).strip() or "agent"
        agent_lower = agent_name.lower()

        tool_calls = step_message.get("tool_calls")
        fn_call = step_message.get("function_call")
        has_fn_call = isinstance(fn_call, dict) and bool(fn_call.get("name"))
        has_tools = bool(tool_calls) or has_fn_call

        if tool_calls:
            tool_names = _extract_tool_names(tool_calls)
            if tool_names:
                events.append({"event": "tool", "agent": agent_name, "tools": tool_names})
        elif has_fn_call:
            events.append({"event": "tool", "agent": agent_name, "tools": [str(fn_call["name"])]})

        if step_message.get("role") != "assistant":
            return events

        content = step_message.get("content")
        if not content or not isinstance(content, str) or not content.strip():
            return events

        text = content.strip()
        if not agent_raw or agent_lower == "leader":
            if not has_tools:
                thinking_steps.append(text)
            events.append({"event": "delta", "agent": "leader", "text": text})
        else:
            events.append({"event": "delta", "agent": agent_name, "text": text})
    except Exception:
        logging.debug("Failed to process step message: %r", step_message)
    return events


def _activity_entry_from_event(evt: Dict[str, Any]) -> Dict[str, Any] | None:
    event_type = evt.get("event")
    agent = str(evt.get("agent") or "agent")
    if event_type == "tool":
        tools = [str(t) for t in evt.get("tools") or [] if str(t)]
        return {"kind": "tool", "agent": agent, "tools": tools}
    if event_type == "delta":
        text = str(evt.get("text") or "").strip()
        if text:
            return {"kind": "delta", "agent": agent, "text": text}
    return None


def _activity_log_from_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for evt in events:
        entry = _activity_entry_from_event(evt)
        if entry:
            entries.append(entry)
    return entries


def _get_on_step_callback(thinking_steps: List[str], process_events: Optional[List[Dict[str, Any]]] = None):
    def on_step(step_message: Any):
        for evt in _apply_step_messages(step_message, thinking_steps):
            if process_events is not None:
                process_events.append(evt)

    return on_step


def _final_reply_text(final_message: Any) -> str:
    try:
        if isinstance(final_message, dict):
            return str(final_message.get("response") or final_message.get("message") or "")
        if isinstance(final_message, str):
            return final_message
        return str(final_message)
    except Exception:
        return str(final_message)


async def _sse_chat_event_lines(
    request: Request,
    sm,
    session_id: str,
    thinking_steps: List[str],
    chat_factory: Callable[[Callable], Awaitable[Any]],
    persist_turn: Optional[Callable[[str, List[Dict[str, Any]]], Awaitable[None]]] = None,
) -> AsyncIterator[str]:
    """Drain step-hook queue while pantheon chat runs; yield SSE lines."""
    stream_queue: asyncio.Queue = asyncio.Queue(maxsize=512)
    process_events: List[Dict[str, Any]] = []

    async def on_step(step_message: Any):
        for evt in _apply_step_messages(step_message, thinking_steps):
            process_events.append(evt)
            try:
                stream_queue.put_nowait(evt)
            except asyncio.QueueFull:
                break

    async def pantheon_runner():
        return await chat_factory(on_step)

    chat_task = asyncio.create_task(_run_chat_with_client_disconnect(request, sm, session_id, pantheon_runner))

    try:
        while True:
            while True:
                try:
                    evt = stream_queue.get_nowait()
                    payload = json.dumps(evt, ensure_ascii=False)
                    yield f"data: {payload}\n\n"
                except asyncio.QueueEmpty:
                    break
            if chat_task.done():
                break
            await asyncio.sleep(0.05)

        while True:
            try:
                evt = stream_queue.get_nowait()
                payload = json.dumps(evt, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            except asyncio.QueueEmpty:
                break

        try:
            final_message = chat_task.result()
        except HTTPException as he:
            detail = he.detail if isinstance(he.detail, str) else str(he.detail)
            yield f"data: {json.dumps({'event': 'error', 'detail': detail}, ensure_ascii=False)}\n\n"
            return

        if isinstance(final_message, dict) and not final_message.get("success", True):
            detail = _http_error_detail(str((final_message or {}).get("message", "Chat failed")))
            yield f"data: {json.dumps({'event': 'error', 'detail': detail}, ensure_ascii=False)}\n\n"
            return

        final_text = _final_reply_text(final_message).strip()
        process_log = _activity_log_from_events(process_events)
        if persist_turn:
            await persist_turn(final_text, process_log)
        yield f"data: {json.dumps({'event': 'done', 'message': final_text, 'thinking': [], 'process': process_log}, ensure_ascii=False)}\n\n"
    except Exception as e:
        logging.exception("Agent stream failed")
        yield f"data: {json.dumps({'event': 'error', 'detail': _http_error_detail(str(e))}, ensure_ascii=False)}\n\n"


@agent_router.post("/conversations/{conversation_id}/message", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    req: MessageRequest,
    request: Request,
    store: AgentStore = Depends(get_agent_store),
):
    try:
        conv = store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    sm = get_conversation_session_manager(store, conversation_id)
    session_id = store.get_session(conversation_id)
    model, api_key, proxy = _require_agent_runtime_config(req.model, req.api_key, req.proxy)

    if not session_id:
        try:
            session_id = await sm.create_session(
                model=model,
                api_key=api_key,
                api_base=req.api_base,
                proxy=proxy
            )
            store.set_session(conversation_id, session_id)
        except Exception as e:
            logging.error(f"Failed to start session: {e}")
            raise HTTPException(status_code=500, detail=_http_error_detail(str(e)))
    else:
        apply_agent_resource_environment(
            store.conversation_output_dir(conversation_id),
            store.conversation_memory_dir(conversation_id),
        )

    attachments = store.get_attachments_by_ids(conversation_id, req.attachment_ids)
    sync_attachments_to_session(sm, session_id, attachments)

    thinking_steps: List[str] = []
    process_events: List[Dict[str, Any]] = []
    on_step = _get_on_step_callback(thinking_steps, process_events)

    final_message = await _run_chat_with_client_disconnect(
        request,
        sm,
        session_id,
        lambda: sm.chat(
            session_id=session_id,
            content=req.content,
            attachment_ids=req.attachment_ids,
            process_step_message=on_step,
            model=model,
            api_key=api_key,
            api_base=req.api_base,
            proxy=proxy,
        ),
    )
    
    if not final_message or not final_message.get("success", True):
        raise HTTPException(
            status_code=500,
            detail=_http_error_detail(str((final_message or {}).get("message", "Chat failed"))),
        )
    final_text = None
    try:
        if isinstance(final_message, dict):
            final_text = final_message.get("response") or final_message.get("message")
        elif isinstance(final_message, str):
            final_text = final_message
        else:
            final_text = str(final_message)
    except Exception:
        final_text = str(final_message)
    final_reply = str(final_text or "").strip()
    process_log = _activity_log_from_events(process_events)
    messages = conv.get("messages", [])
    user_msg = {
        "id": f"msg_{os.urandom(4).hex()}",
        "sender": "user",
        "content": req.content,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text",
        "attachments": attachments,
    }
    for aid in req.attachment_ids:
        store.remove_pending_attachment(conversation_id, aid)

    assistant_msg = {
        "id": f"msg_{os.urandom(4).hex()}",
        "sender": "assistant",
        "content": final_reply,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text",
        "thinking": [],
        "activityLog": process_log,
    }
    messages.append(user_msg)
    messages.append(assistant_msg)
    store.replace_messages(conversation_id, messages)
    
    return MessageResponse(thinking=[], message=final_reply, process=process_log)


@agent_router.post("/conversations/{conversation_id}/message/stream")
async def send_message_stream(
    conversation_id: str,
    req: MessageRequest,
    request: Request,
    store: AgentStore = Depends(get_agent_store),
):
    try:
        conv = store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    sm = get_conversation_session_manager(store, conversation_id)
    session_id = store.get_session(conversation_id)
    model, api_key, proxy = _require_agent_runtime_config(req.model, req.api_key, req.proxy)

    if not session_id:
        try:
            session_id = await sm.create_session(
                model=model,
                api_key=api_key,
                api_base=req.api_base,
                proxy=proxy,
            )
            store.set_session(conversation_id, session_id)
        except Exception as e:
            logging.error(f"Failed to start session: {e}")
            raise HTTPException(status_code=500, detail=_http_error_detail(str(e)))
    else:
        apply_agent_resource_environment(
            store.conversation_output_dir(conversation_id),
            store.conversation_memory_dir(conversation_id),
        )

    attachments = store.get_attachments_by_ids(conversation_id, req.attachment_ids)
    sync_attachments_to_session(sm, session_id, attachments)

    thinking_steps: List[str] = []

    async def persist(final_text: str, process_log: List[Dict[str, Any]]) -> None:
        messages = conv.get("messages", [])
        user_msg = {
            "id": f"msg_{os.urandom(4).hex()}",
            "sender": "user",
            "content": req.content,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "text",
            "attachments": attachments,
        }
        for aid in req.attachment_ids:
            store.remove_pending_attachment(conversation_id, aid)
        assistant_msg = {
            "id": f"msg_{os.urandom(4).hex()}",
            "sender": "assistant",
            "content": final_text,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "text",
            "thinking": [],
            "activityLog": process_log,
        }
        messages.append(user_msg)
        messages.append(assistant_msg)
        store.replace_messages(conversation_id, messages)

    async def gen():
        async for line in _sse_chat_event_lines(
            request,
            sm,
            session_id,
            thinking_steps,
            lambda on_step: sm.chat(
                session_id=session_id,
                content=req.content,
                attachment_ids=req.attachment_ids,
                process_step_message=on_step,
                model=model,
                api_key=api_key,
                api_base=req.api_base,
                proxy=proxy,
            ),
            persist_turn=persist,
        ):
            yield line

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@agent_router.post("/conversations/{conversation_id}/rewind", response_model=MessageResponse)
async def rewind_message(
    conversation_id: str,
    req: RewindRequest,
    request: Request,
    store: AgentStore = Depends(get_agent_store),
):
    try:
        conv = store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    session_id = store.get_session(conversation_id)
    if not session_id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    sm = get_conversation_session_manager(store, conversation_id)
    model, api_key, proxy = _require_agent_runtime_config(req.model, req.api_key, req.proxy)
    
    apply_agent_resource_environment(
        store.conversation_output_dir(conversation_id),
        store.conversation_memory_dir(conversation_id),
    )

    attachments = store.get_attachments_by_ids(conversation_id, req.attachment_ids)
    sync_attachments_to_session(sm, session_id, attachments)
    
    thinking_steps: List[str] = []
    process_events: List[Dict[str, Any]] = []
    on_step = _get_on_step_callback(thinking_steps, process_events)
    
    final_message = await _run_chat_with_client_disconnect(
        request,
        sm,
        session_id,
        lambda: sm.rewind_and_rerun(
            session_id=session_id,
            user_turn_index=req.user_turn_index,
            content=req.content,
            attachment_ids=req.attachment_ids,
            process_step_message=on_step,
            model=model,
            api_key=api_key,
            api_base=req.api_base,
            proxy=proxy,
        ),
    )
    
    if not final_message or not final_message.get("success", True):
        raise HTTPException(
            status_code=500,
            detail=_http_error_detail(str((final_message or {}).get("message", "Chat failed"))),
        )
    final_text = None
    try:
        if isinstance(final_message, dict):
            final_text = final_message.get("response") or final_message.get("message")
        elif isinstance(final_message, str):
            final_text = final_message
        else:
            final_text = str(final_message)
    except Exception:
        final_text = str(final_message)
    final_reply = str(final_text or "").strip()
    process_log = _activity_log_from_events(process_events)
    # Update messages in store
    messages = conv.get("messages", [])
    # Find the user message at user_turn_index
    user_msg_indices = [i for i, m in enumerate(messages) if m.get("sender") == "user"]
    if 0 <= req.user_turn_index < len(user_msg_indices):
        cut_index = user_msg_indices[req.user_turn_index]
        messages = messages[:cut_index]
        
    user_msg = {
        "id": f"msg_{os.urandom(4).hex()}",
        "sender": "user",
        "content": req.content,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text",
        "attachments": attachments,
    }
    for aid in req.attachment_ids:
        store.remove_pending_attachment(conversation_id, aid)
        
    assistant_msg = {
        "id": f"msg_{os.urandom(4).hex()}",
        "sender": "assistant",
        "content": final_reply,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text",
        "thinking": [],
        "activityLog": process_log,
    }
    messages.append(user_msg)
    messages.append(assistant_msg)
    store.replace_messages(conversation_id, messages)
    
    return MessageResponse(thinking=[], message=final_reply, process=process_log)


@agent_router.post("/conversations/{conversation_id}/rewind/stream")
async def rewind_message_stream(
    conversation_id: str,
    req: RewindRequest,
    request: Request,
    store: AgentStore = Depends(get_agent_store),
):
    try:
        conv = store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session_id = store.get_session(conversation_id)
    if not session_id:
        raise HTTPException(status_code=404, detail="Session not found")

    sm = get_conversation_session_manager(store, conversation_id)
    model, api_key, proxy = _require_agent_runtime_config(req.model, req.api_key, req.proxy)

    apply_agent_resource_environment(
        store.conversation_output_dir(conversation_id),
        store.conversation_memory_dir(conversation_id),
    )

    attachments = store.get_attachments_by_ids(conversation_id, req.attachment_ids)
    sync_attachments_to_session(sm, session_id, attachments)

    thinking_steps: List[str] = []

    async def persist(final_text: str, process_log: List[Dict[str, Any]]) -> None:
        messages = conv.get("messages", [])
        user_msg_indices = [i for i, m in enumerate(messages) if m.get("sender") == "user"]
        if 0 <= req.user_turn_index < len(user_msg_indices):
            cut_index = user_msg_indices[req.user_turn_index]
            messages = messages[:cut_index]
        user_msg = {
            "id": f"msg_{os.urandom(4).hex()}",
            "sender": "user",
            "content": req.content,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "text",
            "attachments": attachments,
        }
        for aid in req.attachment_ids:
            store.remove_pending_attachment(conversation_id, aid)
        assistant_msg = {
            "id": f"msg_{os.urandom(4).hex()}",
            "sender": "assistant",
            "content": final_text,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "text",
            "thinking": [],
            "activityLog": process_log,
        }
        messages.append(user_msg)
        messages.append(assistant_msg)
        store.replace_messages(conversation_id, messages)

    async def gen():
        async for line in _sse_chat_event_lines(
            request,
            sm,
            session_id,
            thinking_steps,
            lambda on_step: sm.rewind_and_rerun(
                session_id=session_id,
                user_turn_index=req.user_turn_index,
                content=req.content,
                attachment_ids=req.attachment_ids,
                process_step_message=on_step,
                model=model,
                api_key=api_key,
                api_base=req.api_base,
                proxy=proxy,
            ),
            persist_turn=persist,
        ):
            yield line

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@agent_router.post("/conversations/{conversation_id}/stop")
async def stop_agent_session(conversation_id: str, store: AgentStore = Depends(get_agent_store)):
    session_id = store.get_session(conversation_id)
    if not session_id:
        return {"status": "noop", "message": "No active agent session"}
        
    sm = get_conversation_session_manager(store, conversation_id)
    success = await sm.stop_session(session_id)
    if not success:
        logging.warning("Failed to stop chat %s", session_id)
    store.clear_session(conversation_id)
    return {"status": "stopped"}


@agent_router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(conversation_id: str, store: AgentStore = Depends(get_agent_store)):
    try:
        store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session_id = store.get_session(conversation_id)
    if session_id:
        sm = get_conversation_session_manager(store, conversation_id)
        try:
            await sm.stop_session(session_id)
        except Exception:
            logging.warning("Failed to stop chat %s during clear", session_id)
    store.clear_conversation(conversation_id)
    return {"status": "cleared"}

@agent_router.post("/conversations/{conversation_id}/upload", response_model=UploadResponse)
async def upload_file(
    conversation_id: str,
    api_key: Optional[str] = Form(None),
    api_base: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    proxy: Optional[str] = Form(None),
    file: UploadFile = File(...),
    store: AgentStore = Depends(get_agent_store)
):
    try:
        store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    session_id = store.get_session(conversation_id)
    sm = get_conversation_session_manager(store, conversation_id)
    model, api_key, proxy = _require_agent_runtime_config(model, api_key, proxy)
    if session_id:
        sm.sessions.setdefault(session_id, {"chat_id": session_id})
        apply_agent_resource_environment(
            store.conversation_output_dir(conversation_id),
            store.conversation_memory_dir(conversation_id),
        )
    if not session_id:
        # Create a placeholder session or just generate an ID?
        # Actually, session_manager.upload_file needs a session_id to store metadata in memory,
        # but we can also just pass the conversation_id as session_id for upload purposes if session doesn't exist yet.
        # Wait, if we create a session later, it will have a different ID.
        # Let's just create the session now if it doesn't exist.
        try:
            session_id = await sm.create_session(
                model=model,
                api_key=api_key,
                api_base=api_base,
                proxy=proxy
            )
            store.set_session(conversation_id, session_id)
        except Exception as e:
            logging.error(f"Failed to start session for upload: {e}")
            raise HTTPException(status_code=500, detail=_http_error_detail(str(e)))
            
    try:
        upload_dir = store.conversation_upload_dir(conversation_id)
        file_info = await sm.upload_file(
            session_id=session_id,
            file_obj=file.file,
            filename=file.filename,
            upload_dir=upload_dir
        )
        file_url = f"/agent/conversations/{conversation_id}/uploads/{Path(file_info['path']).name}"
        
        attachment = {
            "id": file_info["id"],
            "filename": file_info["filename"],
            "url": file_url,
            "mime_type": file.content_type or "application/octet-stream",
            "size": file_info.get("size", 0),
            "path": file_info["path"],
        }
        store.add_pending_attachment(conversation_id, attachment)
        
        return UploadResponse(
            id=file_info["id"],
            filename=file_info["filename"],
            url=file_url,
            mime_type=file.content_type or "application/octet-stream",
            size=file_info.get("size", 0)
        )
    except Exception as e:
        logging.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=_http_error_detail(str(e)))

@agent_router.delete("/conversations/{conversation_id}/upload/{attachment_id}")
async def delete_upload(conversation_id: str, attachment_id: str, store: AgentStore = Depends(get_agent_store)):
    session_id = store.get_session(conversation_id)
    if session_id:
        sm = get_conversation_session_manager(store, conversation_id)
        await sm.delete_upload(session_id, attachment_id)
        
    _, removed = store.remove_pending_attachment(conversation_id, attachment_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"status": "deleted"}

@agent_router.get("/conversations/{conversation_id}/uploads/{filename}")
async def get_upload_file(conversation_id: str, filename: str, store: AgentStore = Depends(get_agent_store)):
    if "/" in filename or ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    file_path = store.conversation_upload_dir(conversation_id) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path), media_type="application/octet-stream", filename=filename)

@agent_router.get("/conversations/{conversation_id}/files/{file_path:path}")
async def get_agent_file(conversation_id: str, file_path: str, store: AgentStore = Depends(get_agent_store)):
    raw = unquote(file_path or "").strip()
    if "\\" in raw:
        raise HTTPException(status_code=400, detail="Invalid file path")

    try:
        store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    allowed = {".csv", ".html", ".yaml", ".yml", ".log", ".txt", ".json", ".png", ".jpg", ".jpeg", ".svg"}
    requested = Path(raw)
    if requested.is_absolute() or any(part == ".." for part in requested.parts):
        raise HTTPException(status_code=400, detail="Invalid file path")
    suffix = requested.suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    output_root = store.conversation_output_dir(conversation_id).resolve()
    resolved_path = _resolve_conversation_artifact_path(output_root, raw, allowed)
    if resolved_path is None:
        user_output_root = store.user_output_dir.resolve()
        if user_output_root.is_dir():
            resolved_path = _resolve_conversation_artifact_path(user_output_root, raw, allowed)
    if resolved_path is None:
        workspace_out = get_workspace_outputs_dir()
        if workspace_out.is_dir():
            resolved_path = _resolve_conversation_artifact_path(workspace_out, raw, allowed)
    if resolved_path is None:
        searched_roots = [str(output_root)]
        user_output_root = store.user_output_dir.resolve()
        if user_output_root.is_dir():
            searched_roots.append(str(user_output_root))
        workspace_out = get_workspace_outputs_dir()
        if workspace_out.is_dir():
            searched_roots.append(str(workspace_out.resolve()))
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Artifact file was not found. The agent may have reported a path that was not created.",
                "path": raw,
                "searched_roots": searched_roots,
            },
        )

    media_types = {
        ".csv": "text/csv",
        ".html": "text/html",
        ".yaml": "application/x-yaml",
        ".yml": "application/x-yaml",
        ".log": "text/plain",
        ".txt": "text/plain",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }
    return FileResponse(
        str(resolved_path),
        media_type=media_types.get(resolved_path.suffix.lower(), "application/octet-stream"),
        filename=resolved_path.name,
    )

