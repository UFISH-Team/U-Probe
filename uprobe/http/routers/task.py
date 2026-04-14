import uuid
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import asyncio
import yaml
import tempfile
from pathlib import Path
import logging
import shutil
import zipfile
import os
import json
import re
from collections import deque
import functools
from uprobe.http.utils.process_pool import get_process_pool
from uprobe.http.routers.auth import get_current_active_user, User
from uprobe.http.utils.paths import get_data_dir, get_tasks_dir, get_results_dir

router = APIRouter(
    prefix="/task",
    tags=["task"],
    responses={404: {"description": "Not found"}},
)

def get_user_tasks_file(username: str) -> Path:
    user_dir = get_tasks_dir() / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "tasks.json"

def load_user_tasks(username: str) -> List[Dict[str, Any]]:
    file_path = get_user_tasks_file(username)
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading tasks for {username}: {e}")
        return []

def save_user_tasks(username: str, tasks: List[Dict[str, Any]]):
    file_path = get_user_tasks_file(username)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving tasks for {username}: {e}")

# --- Pydantic Models ---

class TaskParameters(BaseModel):
    target_regions: Optional[str] = None
    target_genes: Optional[str] = None
    whole_genome: Optional[bool] = None
    probe_length: int
    probe_type: Optional[str] = None
    probe_name: Optional[str] = None

class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    genome: str
    parameters: TaskParameters

class TaskCreateBody(BaseModel):
    # Fields directly from the frontend form for creation
    name: str
    description: Optional[str] = None
    genome: str
    target_type: Literal["regions", "genes", "whole_genome"]
    target_value: Optional[str] = None # For regions or genes
    probe_length: int
    tm_range: str
    gc_range: str

class TaskRead(TaskBase):
    id: str
    status: Literal["pending", "running", "completed", "failed", "paused"]
    progress: int = Field(..., ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    result_url: Optional[str] = None
    yaml_content: Optional[str] = None
    error_message: Optional[str] = None

# --- Helper Function ---
def find_task_by_id(username: str, task_id: str) -> Optional[TaskRead]:
    """Finds a task in the user's list by its ID."""
    tasks = load_user_tasks(username)
    for task_dict in tasks:
        if task_dict.get("id") == task_id:
            return TaskRead(**task_dict)
    return None

def update_task_in_db(username: str, updated_task: TaskRead):
    tasks = load_user_tasks(username)
    for i, task_dict in enumerate(tasks):
        if task_dict.get("id") == updated_task.id:
            # Convert datetime to string for JSON serialization
            task_dict_to_save = updated_task.model_dump()
            task_dict_to_save['created_at'] = task_dict_to_save['created_at'].isoformat()
            task_dict_to_save['updated_at'] = task_dict_to_save['updated_at'].isoformat()
            tasks[i] = task_dict_to_save
            save_user_tasks(username, tasks)
            return
    
    # If not found, append
    task_dict_to_save = updated_task.model_dump()
    task_dict_to_save['created_at'] = task_dict_to_save['created_at'].isoformat()
    task_dict_to_save['updated_at'] = task_dict_to_save['updated_at'].isoformat()
    tasks.append(task_dict_to_save)
    save_user_tasks(username, tasks)

def reset_stuck_tasks_on_startup():
    """
    Reset 'running' tasks to 'failed' on server startup.
    Since the queue is memory-based, execution context is lost after restart.
    """
    tasks_dir = get_tasks_dir()
    if not tasks_dir.exists():
        return
        
    for user_dir in tasks_dir.iterdir():
        if user_dir.is_dir():
            username = user_dir.name
            tasks = load_user_tasks(username)
            modified = False
            for task_dict in tasks:
                if task_dict.get("status") == "running":
                    task_dict["status"] = "failed"
                    task_dict["progress"] = 0
                    task_dict["description"] = (task_dict.get("description") or "") + " [System restarted, task failed]"
                    modified = True
            if modified:
                save_user_tasks(username, tasks)
                logging.info(f"Reset stuck tasks for user {username} on startup.")

# --- API Endpoints ---

@router.get("/", response_model=List[TaskRead])
async def get_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a list of tasks, optionally filtering by status and search term.
    Matches frontend filtering logic (status tabs and search input).
    """
    tasks_dicts = load_user_tasks(current_user.username)
    filtered_tasks = [TaskRead(**t) for t in tasks_dicts]
    
    # Filter by status
    if status_filter and status_filter != "all":
        filtered_tasks = [task for task in filtered_tasks if task.status == status_filter]
        
    # Filter by search term (case-insensitive search in name, description, genome)
    if search:
        search_lower = search.lower()
        filtered_tasks = [
            task for task in filtered_tasks 
            if search_lower in task.name.lower() or \
               (task.description and search_lower in task.description.lower()) or \
               search_lower in task.genome.lower()
        ]
        
    return filtered_tasks


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreateBody,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new task based on the provided form data.
    """
    now = datetime.now()
    new_task_id = f"task-{uuid.uuid4()}" # Generate a unique ID
    
    # Construct parameters based on target_type
    params_dict = {
        "probe_length": task_data.probe_length,
        "tm_range": task_data.tm_range,
        "gc_range": task_data.gc_range,
    }
    if task_data.target_type == "regions":
        if not task_data.target_value:
             raise HTTPException(status_code=422, detail="Target value is required for regions type")
        params_dict["target_regions"] = task_data.target_value
    elif task_data.target_type == "genes":
        if not task_data.target_value:
             raise HTTPException(status_code=422, detail="Target value is required for genes type")
        params_dict["target_genes"] = task_data.target_value
    elif task_data.target_type == "whole_genome":
        params_dict["whole_genome"] = True
        
    parameters = TaskParameters(**params_dict)

    new_task = TaskRead(
        id=new_task_id,
        name=task_data.name,
        description=task_data.description,
        genome=task_data.genome,
        parameters=parameters,
        status="pending",
        progress=0,
        created_at=now,
        updated_at=now,
        result_url=None,
    )
    update_task_in_db(current_user.username, new_task)
    return new_task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve details for a specific task by its ID.
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a task by its ID.
    """
    tasks = load_user_tasks(current_user.username)
    initial_length = len(tasks)
    tasks = [t for t in tasks if t.get("id") != task_id]
            
    if len(tasks) == initial_length:
        raise HTTPException(status_code=404, detail="Task not found")
        
    save_user_tasks(current_user.username, tasks)
    return


@router.post("/{task_id}/pause", response_model=TaskRead)
async def pause_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Set the status of a task to 'paused'.
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status not in ["running", "pending"]: # Can only pause running or pending tasks
         raise HTTPException(status_code=400, detail=f"Cannot pause task in '{task.status}' state")

    task.status = "paused"
    task.updated_at = datetime.now()
    update_task_in_db(current_user.username, task)
    return task


@router.post("/{task_id}/resume", response_model=TaskRead)
async def resume_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Set the status of a paused task back to 'running'.
    (Note: Frontend logic sets it to running, even if paused from pending)
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "paused":
        raise HTTPException(status_code=400, detail=f"Cannot resume task in '{task.status}' state")

    # Determine previous state if needed, but frontend implies -> running
    task.status = "running" 
    task.updated_at = datetime.now()
    update_task_in_db(current_user.username, task)
    return task
    

@router.post("/{task_id}/run", response_model=TaskRead)
async def run_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Start running a pending task by calling the uprobe workflow.
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot run task in '{task.status}' state")
    
    if not task.yaml_content:
        raise HTTPException(status_code=400, detail="Task has no YAML configuration")
    
    # Keep pending status, update time to indicate queue entry
    task.status = "pending"
    task.updated_at = datetime.now()
    update_task_in_db(current_user.username, task)
    
    # Run uprobe task asynchronously
    asyncio.create_task(_run_uprobe_task(current_user.username, task_id))
    
    return task

async def _run_uprobe_task(username: str, task_id: str):
    """
    Internal async function to run uprobe task with queue waiting logic.
    """
    from uprobe.http.utils.task_queue import get_task_semaphore, TASK_THREADS
    
    semaphore = get_task_semaphore()
    should_wait = getattr(semaphore, "locked", None) and semaphore.locked()
    if should_wait:
        logging.info(f"Task {task_id} for user {username} is queued, waiting for CPU resources...")
    else:
        logging.info(f"Task {task_id} for user {username} submitted and will start soon.")
    async with semaphore:
        task = find_task_by_id(username, task_id)
        if not task or task.status != "pending":
            logging.info(f"Task {task_id} was cancelled or removed from queue.")
            return
        task.status = "running"
        task.progress = 10
        task.updated_at = datetime.now()
        update_task_in_db(username, task)
        try:
            logging.info(f"Task {task_id} acquired execution slot, dispatching worker.")
            results_base_dir = get_results_dir()
            task_results_dir = results_base_dir / task_id
            task_results_dir.mkdir(parents=True, exist_ok=True)
            log_path = task_results_dir / "run.log"
            try:
                log_path.touch(exist_ok=True)
            except Exception:
                pass
            task.progress = 30
            update_task_in_db(username, task)
            from uprobe.http.utils.uprobe_runner import run_uprobe_workflow
            loop = asyncio.get_running_loop()
            pool = get_process_pool()
            job = functools.partial(run_uprobe_workflow, protocol_yaml=task.yaml_content, username=username, task_id=task_id, output_dir=str(task_results_dir), threads=TASK_THREADS, raw_csv=True, continue_invalid_targets=False, log_path=str(log_path))
            fut = loop.run_in_executor(pool, job)
            tail_buf = deque(maxlen=2000)
            last_progress = [task.progress]
            def _progress_from_line(line: str) -> int:
                if "Building genome index" in line:
                    return 35
                if "Validating targets" in line:
                    return 45
                if "Target validation successful" in line:
                    return 50
                if "Generating target region sequences" in line or "Extracting" in line:
                    return 60
                if "Constructing probes" in line or "Successfully generated" in line:
                    return 70
                if "Adding attributes to probes" in line:
                    return 80
                if "Post-processing probes" in line:
                    return 85
                if "Generating final report" in line or "Generating" in line and "HTML report" in line:
                    return 92
                if "Workflow completed successfully" in line or "U-Probe Workflow Completed" in line:
                    return 100
                return 0
            async def _tail_log():
                try:
                    pos = 0
                    while True:
                        if fut.done():
                            return
                        try:
                            with open(log_path, "r", encoding="utf-8", errors="replace") as rf:
                                rf.seek(pos)
                                chunk = rf.read()
                                pos = rf.tell()
                                if chunk:
                                    for line in chunk.splitlines():
                                        if line.strip():
                                            tail_buf.append(line)
                                            # Clean up redundant core logger prefix for cleaner server logs
                                            clean_line = re.sub(r'^[a-zA-Z0-9_.]+\s+[A-Z]+\s+@\s+\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}:\s*', '', line)
                                            logging.info(f"[{task_id}] {clean_line}")
                                            p = _progress_from_line(line)
                                            if p and p > last_progress[0] and p < 100:
                                                last_progress[0] = p
                                                task.progress = p
                                                task.updated_at = datetime.now()
                                                update_task_in_db(username, task)
                        except Exception:
                            pass
                        await asyncio.sleep(0.5)
                except Exception:
                    return
            tail_task = asyncio.create_task(_tail_log())
            result = await fut
            try:
                tail_task.cancel()
            except Exception:
                pass
            if not isinstance(result, dict) or not result.get("ok"):
                err = (result or {}).get("error") if isinstance(result, dict) else "Unknown error"
                task.status = "failed"
                task.progress = 0
                task.error_message = err or "\n".join(tail_buf)
                task.updated_at = datetime.now()
                update_task_in_db(username, task)
                return
            zip_name = result.get("zip_name")
            zip_path = task_results_dir / zip_name if zip_name else None
            if zip_path is None or not zip_path.exists():
                task.status = "failed"
                task.progress = 0
                task.error_message = "Workflow finished but zip archive is missing.\n\nLog tail:\n" + "\n".join(tail_buf)
                task.updated_at = datetime.now()
                update_task_in_db(username, task)
                return
            task.status = "completed"
            task.progress = 100
            task.result_url = str(zip_path.relative_to(results_base_dir))
            task.updated_at = datetime.now()
            task.error_message = None
            update_task_in_db(username, task)
            logging.info(f"Task {task_id} completed! Results saved to {task_results_dir}")
        except Exception as e:
            logging.error(f"Task {task_id} failed: {str(e)}")
            task.status = "failed"
            task.progress = 0
            task.error_message = f"Internal server error: {str(e)}"
            task.updated_at = datetime.now()
            update_task_in_db(username, task)

@router.get("/{task_id}/download")
async def download_task_result(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download task result files as a zip archive.
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "completed":
         raise HTTPException(status_code=400, detail="Task is not completed yet")
         
    if not task.result_url:
        raise HTTPException(status_code=404, detail="Result file not available for this task")

    # Build actual file path
    results_base_dir = get_results_dir()
    file_path = results_base_dir / task.result_url
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found on disk")
    
    # Return file download response
    return FileResponse(
        path=str(file_path),
        filename=f"{task.name}_{task_id}_results.zip",
        media_type="application/zip"
    )

@router.get("/{task_id}/files")
async def list_task_files(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all result files for a task.
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "completed":
         raise HTTPException(status_code=400, detail="Task is not completed yet")
    
    results_base_dir = get_results_dir()
    task_results_dir = results_base_dir / task_id
    if not task_results_dir.exists():
        return {"files": []}
    
    files = []
    for file_path in task_results_dir.iterdir():
        if file_path.is_file() and not file_path.name.endswith('.zip'):
            file_info = {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": "csv" if file_path.suffix == ".csv" else "html" if file_path.suffix == ".html" else "other",
                "url": f"/task/{task_id}/file/{file_path.name}"
            }
            files.append(file_info)
    
    return {"files": files}

@router.get("/{task_id}/file/{filename}")
async def download_single_file(
    task_id: str, 
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download a single result file for a task.
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "completed":
         raise HTTPException(status_code=400, detail="Task is not completed yet")
    
    results_base_dir = get_results_dir()
    task_results_dir = results_base_dir / task_id
    file_path = task_results_dir / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Ensure file is within task directory (security check)
    if not str(file_path.resolve()).startswith(str(task_results_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    media_type = "text/csv" if filename.endswith('.csv') else "text/html" if filename.endswith('.html') else "application/octet-stream"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )
