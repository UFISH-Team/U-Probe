from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
from pathlib import Path
from datetime import datetime
from uprobe.http.routers.auth import get_current_active_user, User
from uprobe.http.utils.paths import get_data_dir

router = APIRouter(
    prefix="/custom_probes",
    tags=["custom_probes"],
    responses={404: {"description": "Not found"}},
)

def get_user_probes_file(username: str) -> Path:
    user_dir = get_data_dir() / "user_probes" / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "probes.json"

def load_user_probes(username: str) -> List[Dict[str, Any]]:
    file_path = get_user_probes_file(username)
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading probes for {username}: {e}")
        return []

def save_user_probes(username: str, probes: List[Dict[str, Any]]):
    file_path = get_user_probes_file(username)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(probes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving probes for {username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save custom probes")

@router.get("/", response_model=List[Dict[str, Any]])
async def get_custom_probes(current_user: User = Depends(get_current_active_user)):
    """获取当前用户的所有自定义探针"""
    return load_user_probes(current_user.username)

@router.post("/", response_model=Dict[str, Any])
async def save_custom_probe(
    probe_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """保存或更新自定义探针"""
    probes = load_user_probes(current_user.username)
    
    # 检查名称是否重复
    probe_name = probe_data.get("name")
    if not probe_name:
        raise HTTPException(status_code=400, detail="Probe name is required")
        
    # 如果是更新现有的（通过ID匹配）
    probe_id = probe_data.get("id")
    
    existing_idx = -1
    name_conflict = False
    
    for i, p in enumerate(probes):
        if p.get("id") == probe_id:
            existing_idx = i
        elif p.get("name") == probe_name:
            name_conflict = True
            
    if name_conflict and existing_idx == -1:
        raise HTTPException(status_code=400, detail=f"A probe with name '{probe_name}' already exists")
        
    if existing_idx >= 0:
        probes[existing_idx] = probe_data
    else:
        probes.append(probe_data)
        
    save_user_probes(current_user.username, probes)
    return probe_data

@router.delete("/{probe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_probe(
    probe_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """删除自定义探针"""
    probes = load_user_probes(current_user.username)
    
    initial_length = len(probes)
    probes = [p for p in probes if p.get("id") != probe_id]
    
    if len(probes) == initial_length:
        raise HTTPException(status_code=404, detail="Probe not found")
        
    save_user_probes(current_user.username, probes)
    return None
