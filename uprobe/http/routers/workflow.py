from fastapi import APIRouter, File, UploadFile, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from ..utils.file import load_barcodes_from_csv
import logging
import asyncio
import tempfile
import os
import uuid
import json
from datetime import datetime
from uprobe.http.routers.task import TaskRead, TaskParameters, update_task_in_db
from uprobe.http.routers.auth import get_current_active_user, User
from uprobe.core.api import UProbeAPI
from uprobe.http.utils.paths import get_genomes_yaml, get_barcodes_csv, get_probe_json

CSV_FILE_PATH = get_barcodes_csv()

logging.basicConfig(level=logging.INFO)

workflow = APIRouter(prefix="/workflow", tags=["workflow"])


class QuickBarcodeRequest(BaseModel):
    num_barcodes: int
    length: int
    alphabet: Optional[str] = "ACT"
    rc_free: Optional[bool] = True
    gc_limits: Optional[Tuple[int, int]] = None
    prevent_patterns: Optional[List[str]] = None

class PcrBarcodeRequest(BaseModel):
    num_barcodes: int
    length: int = 8

class SequencingBarcodeRequest(BaseModel):
    num_barcodes: int
    length: int = 12


@workflow.post("/barcodes/quick", response_model=List[str])
async def post_quick_generate_barcodes(request: QuickBarcodeRequest):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = UProbeAPI(
                protocol_config={},
                genomes_config={},
                output_dir=Path(temp_dir),
                require_genome=False
            )
            barcodes = api.quick_generate_barcodes(
                num_barcodes=request.num_barcodes,
                length=request.length,
                alphabet=request.alphabet,
                rc_free=request.rc_free,
                gc_limits=request.gc_limits,
                prevent_patterns=request.prevent_patterns
            )
            return barcodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate barcodes: {e}")

@workflow.post("/barcodes/pcr", response_model=List[str])
async def post_pcr_generate_barcodes(request: PcrBarcodeRequest):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = UProbeAPI(
                protocol_config={},
                genomes_config={},
                output_dir=Path(temp_dir),
                require_genome=False
            )
            # PCR presets can be passed as kwargs
            barcodes = api.quick_generate_barcodes(
                num_barcodes=request.num_barcodes,
                length=request.length,
                alphabet='ACGT',
                gc_limits=(request.length // 4, 3 * request.length // 4),
                prevent_patterns=["AAAA", "TTTT", "CCCC", "GGGG"]
            )
            return barcodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate barcodes: {e}")

@workflow.post("/barcodes/sequencing", response_model=List[str])
async def post_sequencing_generate_barcodes(request: SequencingBarcodeRequest):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            api = UProbeAPI(
                protocol_config={},
                genomes_config={},
                output_dir=Path(temp_dir),
                require_genome=False
            )
            # Sequencing presets can be passed as kwargs
            barcodes = api.quick_generate_barcodes(
                num_barcodes=request.num_barcodes,
                length=request.length,
                alphabet='ACGT',
                gc_limits=(request.length // 3, 2 * request.length // 3),
                prevent_patterns=["AAA", "TTT", "CCC", "GGG"]
            )
            return barcodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate barcodes: {e}")


@workflow.get("/barcodes", response_model=List[str])
async def get_barcodes_list() -> List[str]:
    barcodes_dict = load_barcodes_from_csv(CSV_FILE_PATH)
    return [f"{key}: {value}" for key, value in barcodes_dict.items()]

@workflow.get("/barcodes/{barcode}")
async def get_barcodes_dict(barcode: str):
    barcodes = load_barcodes_from_csv(CSV_FILE_PATH)
    if barcode in barcodes:
        return {barcode: barcodes[barcode]}
        
@workflow.get("/builtin_probes")
async def get_builtin_probes():
    try:
        probe_json_path = get_probe_json()
        if not probe_json_path.exists():
            return {}
        with open(probe_json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load built-in probes: {e}")
        raise HTTPException(status_code=500, detail="Failed to load built-in probes")
    
@workflow.post("/submit_task")
async def submit_task(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    try:
        contents = await file.read()
        yaml_content = yaml.safe_load(contents)
        print("Received yaml content:", yaml_content)
        
        # Generate unique task ID
        task_id = f"task-{uuid.uuid4()}"
        now = datetime.now()
        
        # Extract task info from YAML config
        task_name = yaml_content.get('name', f'Uprobe Task {task_id[:8]}') 
        task_description = yaml_content.get('description', 'Uprobe design task')
        # Try to get species info from multiple possible fields
        genome = yaml_content.get('genome') or yaml_content.get('species', 'Unknown')
        
        # Build task parameters, extract more info from YAML
        probe_length = 120  # Default value
        if yaml_content.get('extracts', {}).get('target_region', {}).get('length'):
            probe_length = yaml_content['extracts']['target_region']['length']
        
        # Extract probe type info
        probe_type = yaml_content.get('probe_type', 'Unknown')
        probe_name = yaml_content.get('probe_name', probe_type)
        
        parameters = TaskParameters(
            probe_length=probe_length,
            tm_range="60-70",  # Default value
            gc_range="40-60",  # Default value
            probe_type=probe_type,
            probe_name=probe_name
        )
        
        # Create task record
        new_task = TaskRead(
            id=task_id,
            name=task_name,
            description=task_description,
            genome=genome,
            parameters=parameters,
            status="pending",
            progress=0,
            created_at=now,
            updated_at=now,
            result_url=None,
        )
        
        # Save YAML content to task (add yaml_content field)
        new_task.yaml_content = yaml.dump(yaml_content, default_style='"', allow_unicode=True)
        
        # Save task to database
        update_task_in_db(current_user.username, new_task)
        
        return {
            "status": "success", 
            "message": "Task created successfully", 
            "data": {"job_id": task_id, "task_id": task_id}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing task: {str(e)}")

@workflow.post("/run_uprobe")
async def run_uprobe(file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    contents = await file.read()
    try:
        yaml.safe_load(contents)
    except yaml.YAMLError:
        raise HTTPException(status_code=400, detail="Invalid YAML file provided.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        protocol_filepath = temp_dir_path / "protocol.yaml"
        protocol_filepath.write_bytes(contents)
        
        # Merge public_genomes.yaml and user_genomes.yaml
        from uprobe.http.utils.paths import get_genomes_yaml, get_user_genomes_yaml
        merged_genomes = {}
        
        public_yaml = get_genomes_yaml()
        if public_yaml.exists():
            try:
                with open(public_yaml, 'r', encoding='utf-8') as f:
                    public_data = yaml.safe_load(f) or {}
                    merged_genomes.update(public_data)
            except Exception as e:
                logging.error(f"Error loading public genomes.yaml: {e}")
                
        user_yaml = get_user_genomes_yaml(current_user.username)
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

        # Build uprobe command with --threads limit
        from uprobe.http.utils.task_queue import TASK_THREADS
        cmd = [
            "python", "-m", "uprobe", "run",
            "--protocol", str(protocol_filepath),
            "--genomes", str(merged_genomes_path),
            "--output", str(output_dir),
            "--raw",
            "--threads", str(TASK_THREADS)
        ]
        
        logging.info(f"Running command: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode()
            logging.error(f"Uprobe CLI failed with code {process.returncode}: {error_message}")
            raise HTTPException(status_code=500, detail=f"Uprobe CLI Error: {error_message}")

        csv_files = list(output_dir.glob('*.csv'))
        if not csv_files:
            log_output = stdout.decode()
            logging.warning(f"Uprobe command stdout: {log_output}")
            raise HTTPException(status_code=404, detail="Uprobe process did not generate an output CSV file.")
        
        result_csv_path = csv_files[0]
        if len(csv_files) > 1:
            logging.warning(f"Multiple CSV files found, returning the first one: {result_csv_path.name}")

        def file_iterator(file_path: Path):
            with open(file_path, 'rb') as f:
                yield from f

        return StreamingResponse(
            file_iterator(result_csv_path),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result_csv_path.name}"}
        )
