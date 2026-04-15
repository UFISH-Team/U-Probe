import os
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from uprobe.core.agent.session_manager import get_session_manager, apply_proxy_environment
from uprobe.http.utils.paths import get_output_dir, get_data_dir
from uprobe.http.utils.agent_store import AgentStore
from uprobe.http.routers.auth import get_current_active_user, User

agent_router = APIRouter(prefix="/agent", tags=["agent"])

DATA_DIR = get_data_dir()
OUTPUT_DIR = get_output_dir()

def _http_error_detail(text: str, max_len: int = 2500) -> str:
    t = (text or "").strip() or "Error"
    if len(t) > max_len:
        return t[: max_len - 1] + "…"
    return t

def get_agent_store(current_user: User = Depends(get_current_active_user)) -> AgentStore:
    return AgentStore(data_dir=DATA_DIR, output_dir=OUTPUT_DIR, username=current_user.username)

def get_conversation_session_manager(store: AgentStore, conversation_id: str):
    workspace_root = store.conversation_output_dir(conversation_id)
    output_dir = store.conversation_output_dir(conversation_id)
    memory_dir = store.conversation_memory_dir(conversation_id)
    return get_session_manager(
        workspace_root=workspace_root,
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
    model: Optional[str] = "gpt-5.4"
    proxy: Optional[str] = None

class RewindRequest(BaseModel):
    user_turn_index: int
    content: str
    attachment_ids: List[str] = []
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = "gpt-5.4"
    proxy: Optional[str] = None

class MessageResponse(BaseModel):
    thinking: List[str]
    message: str

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


def _get_on_step_callback(thinking_steps: List[str]):
    def on_step(step_message: Any):
        try:
            if not isinstance(step_message, dict): return
            if step_message.get("tool_calls") or step_message.get("function_call"): return
            agent_name = step_message.get("agent_name", "")
            if agent_name and agent_name.lower() != "leader": return
            if step_message.get("role") == "assistant" and not step_message.get("content"): return
            if step_message.get("role") != "assistant": return
            content = step_message.get("content")
            if content and isinstance(content, str) and content.strip():
                thinking_steps.append(content.strip())
        except Exception:
            logging.debug("Failed to process step message: %r", step_message)
    return on_step


@agent_router.post("/conversations/{conversation_id}/message", response_model=MessageResponse)
async def send_message(conversation_id: str, req: MessageRequest, store: AgentStore = Depends(get_agent_store)):
    try:
        conv = store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    sm = get_conversation_session_manager(store, conversation_id)
    session_id = store.get_session(conversation_id)

    if not session_id:
        try:
            session_id = await sm.create_session(
                model=req.model,
                api_key=req.api_key,
                api_base=req.api_base,
                proxy=req.proxy
            )
            store.set_session(conversation_id, session_id)
        except Exception as e:
            logging.error(f"Failed to start session: {e}")
            raise HTTPException(status_code=500, detail=_http_error_detail(str(e)))
    else:
        # Update environment variables for existing session
        if req.api_key:
            os.environ["OPENAI_API_KEY"] = req.api_key
        if req.api_base:
            os.environ["OPENAI_API_BASE"] = req.api_base
        apply_proxy_environment(req.proxy)

    attachments = store.get_attachments_by_ids(conversation_id, req.attachment_ids)
    sync_attachments_to_session(sm, session_id, attachments)

    thinking_steps: List[str] = []
    on_step = _get_on_step_callback(thinking_steps)

    final_message = await sm.chat(
        session_id=session_id,
        content=req.content,
        attachment_ids=req.attachment_ids,
        process_step_message=on_step
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
    enhanced_text = _process_thinking_steps(thinking_steps, str(final_text or ""))
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
        "content": enhanced_text,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text",
        "thinking": [],
    }
    messages.append(user_msg)
    messages.append(assistant_msg)
    store.replace_messages(conversation_id, messages)
    
    return MessageResponse(thinking=[], message=enhanced_text)


@agent_router.post("/conversations/{conversation_id}/rewind", response_model=MessageResponse)
async def rewind_message(conversation_id: str, req: RewindRequest, store: AgentStore = Depends(get_agent_store)):
    try:
        conv = store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    session_id = store.get_session(conversation_id)
    if not session_id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    sm = get_conversation_session_manager(store, conversation_id)
    
    if req.api_key:
        os.environ["OPENAI_API_KEY"] = req.api_key
    if req.api_base:
        os.environ["OPENAI_API_BASE"] = req.api_base
    apply_proxy_environment(req.proxy)

    attachments = store.get_attachments_by_ids(conversation_id, req.attachment_ids)
    sync_attachments_to_session(sm, session_id, attachments)
    
    thinking_steps: List[str] = []
    on_step = _get_on_step_callback(thinking_steps)
    
    final_message = await sm.rewind_and_rerun(
        session_id=session_id,
        user_turn_index=req.user_turn_index,
        content=req.content,
        attachment_ids=req.attachment_ids,
        process_step_message=on_step
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
    enhanced_text = _process_thinking_steps(thinking_steps, str(final_text or ""))
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
        "content": enhanced_text,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text",
        "thinking": [],
    }
    messages.append(user_msg)
    messages.append(assistant_msg)
    store.replace_messages(conversation_id, messages)
    
    return MessageResponse(thinking=[], message=enhanced_text)

@agent_router.post("/conversations/{conversation_id}/stop")
async def stop_agent_session(conversation_id: str, store: AgentStore = Depends(get_agent_store)):
    session_id = store.get_session(conversation_id)
    if not session_id:
        raise HTTPException(status_code=404, detail="Session not found")
        
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
    model: Optional[str] = Form("gpt-5.4"),
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
    if session_id:
        sm.sessions.setdefault(session_id, {"chat_id": session_id})
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        if api_base:
            os.environ["OPENAI_API_BASE"] = api_base
        apply_proxy_environment(proxy)
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

@agent_router.get("/conversations/{conversation_id}/files/{filename}")
async def get_agent_file(conversation_id: str, filename: str, store: AgentStore = Depends(get_agent_store)):
    if "/" in filename or ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        store.require_conversation(conversation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    allowed = {".csv", ".html"}
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type")
        
    file_path = store.conversation_output_dir(conversation_id) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    media_type = "text/csv" if suffix == ".csv" else "text/html"
    return FileResponse(str(file_path), media_type=media_type, filename=filename)

