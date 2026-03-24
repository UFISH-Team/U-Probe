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
    
    # 更新任务状态为运行中
    task.status = "running"
    task.progress = 10
    task.updated_at = datetime.now()
    update_task_in_db(current_user.username, task)
    
    # 异步运行uprobe任务
    asyncio.create_task(_run_uprobe_task(current_user.username, task_id))
    
    return task

async def _run_uprobe_task(username: str, task_id: str):
    """
    异步运行uprobe任务的内部函数
    """
    task = find_task_by_id(username, task_id)
    if not task:
        return
    
    try:
        logging.info(f"开始运行任务 {task_id} for user {username}")
        
        from uprobe.http.utils.paths import get_genomes_yaml, get_user_genomes_yaml
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            protocol_filepath = temp_dir_path / "protocol.yaml"
            
            # 写入YAML内容到临时文件
            protocol_filepath.write_text(task.yaml_content)
            
            # 合并 public_genomes.yaml 和 user_genomes.yaml
            merged_genomes = {}
            
            public_yaml = get_genomes_yaml()
            if public_yaml.exists():
                try:
                    with open(public_yaml, 'r', encoding='utf-8') as f:
                        public_data = yaml.safe_load(f) or {}
                        merged_genomes.update(public_data)
                except Exception as e:
                    logging.error(f"Error loading public genomes.yaml: {e}")
                    
            user_yaml = get_user_genomes_yaml(username)
            if user_yaml.exists():
                try:
                    with open(user_yaml, 'r', encoding='utf-8') as f:
                        user_data = yaml.safe_load(f) or {}
                        merged_genomes.update(user_data)
                except Exception as e:
                    logging.error(f"Error loading user genomes.yaml: {e}")
            
            merged_genomes_path = temp_dir_path / "merged_genomes.yaml"
            with open(merged_genomes_path, 'w', encoding='utf-8') as f:
                yaml.dump(merged_genomes, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            output_dir = temp_dir_path / "results"
            output_dir.mkdir()
            
            # 构建uprobe命令
            cmd = [
                "python", "-m", "uprobe", "run",
                "--protocol", str(protocol_filepath),
                "--genomes", str(merged_genomes_path),
                "--output", str(output_dir),
                "--raw"
            ]
            
            logging.info(f"Running command: {' '.join(cmd)}")
            
            # 更新进度
            task.progress = 30
            
            # 执行uprobe命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            task.progress = 50
            update_task_in_db(username, task)
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_message = stderr.decode()
                stdout_message = stdout.decode()
                logging.error(f"Uprobe CLI failed with code {process.returncode}")
                logging.error(f"STDERR: {error_message}")
                logging.error(f"STDOUT: {stdout_message}")
                task.status = "failed"
                task.progress = 0
                task.updated_at = datetime.now()
                update_task_in_db(username, task)
                return
            
            # 检查输出文件
            csv_files = list(output_dir.glob('*.csv'))
            html_files = list(output_dir.glob('*.html'))
            
            if not csv_files and not html_files:
                log_output = stdout.decode()
                logging.warning(f"Uprobe command stdout: {log_output}")
                task.status = "failed"
                task.progress = 0
                task.updated_at = datetime.now()
                update_task_in_db(username, task)
                return
            
            # 创建任务专用的结果目录
            results_base_dir = get_results_dir()
            task_results_dir = results_base_dir / task_id
            task_results_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制所有结果文件到持久化存储目录
            result_files = []
            for csv_file in csv_files:
                dest_path = task_results_dir / csv_file.name
                shutil.copy2(csv_file, dest_path)
                result_files.append(csv_file.name)
                
            for html_file in html_files:
                dest_path = task_results_dir / html_file.name
                shutil.copy2(html_file, dest_path)
                result_files.append(html_file.name)
            
            # 创建压缩包包含所有结果文件
            zip_path = task_results_dir / f"{task_id}_results.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_name in result_files:
                    file_path = task_results_dir / file_name
                    zipf.write(file_path, file_name)
            
            # 任务完成，设置结果URL
            task.status = "completed"
            task.progress = 100
            task.result_url = str(zip_path.relative_to(results_base_dir))
            task.updated_at = datetime.now()
            update_task_in_db(username, task)
            
            logging.info(f"task {task_id} completed! Results saved to {task_results_dir}")
            
    except Exception as e:
        logging.error(f"task {task_id} failed: {str(e)}")
        task.status = "failed"
        task.progress = 0
        task.updated_at = datetime.now()
        update_task_in_db(username, task)

@router.get("/{task_id}/download")
async def download_task_result(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    下载任务结果文件（压缩包格式）
    """
    task = find_task_by_id(current_user.username, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "completed":
         raise HTTPException(status_code=400, detail="Task is not completed yet")
         
    if not task.result_url:
        raise HTTPException(status_code=404, detail="Result file not available for this task")

    # 构建实际的文件路径
    results_base_dir = get_results_dir()
    file_path = results_base_dir / task.result_url
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found on disk")
    
    # 返回文件下载响应
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
    列出任务的所有结果文件
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
    下载任务的单个结果文件
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
    
    # 确保文件在任务目录内（安全检查）
    if not str(file_path.resolve()).startswith(str(task_results_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    media_type = "text/csv" if filename.endswith('.csv') else "text/html" if filename.endswith('.html') else "application/octet-stream"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )
