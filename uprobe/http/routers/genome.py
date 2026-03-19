from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from datetime import datetime
import shutil
import os
import yaml
from uprobe.http.paths import get_public_genomes_dir, get_user_genomes_dir, get_genomes_yaml, get_user_genomes_yaml
from uprobe.http.routers.auth import get_current_active_user, User

genome = APIRouter(prefix="/genome", tags=["genome"])

def get_genome_dir(genome_name: str, username: str) -> Path:
    """Helper to find if a genome is public or private, and return its path."""
    public_dir = get_public_genomes_dir() / genome_name
    if public_dir.exists():
        return public_dir
        
    user_dir = get_user_genomes_dir(username) / genome_name
    return user_dir

def update_genomes_yaml(genome_name: str, username: str, action: str = "add"):
    """Update user's genomes.yaml when a genome is added or removed."""
    yaml_path = get_user_genomes_yaml(username)
    genomes_dir = get_user_genomes_dir(username)
    
    # Load existing data
    data = {}
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading {username}'s genomes.yaml: {e}")
            
    if action == "add":
        if genome_name not in data:
            genome_base = str(genomes_dir / genome_name)
            data[genome_name] = {
                "description": f"Custom genome {genome_name}",
                "species": genome_name,
                "fasta": f"{genome_base}/{genome_name}.fa",
                "gtf": f"{genome_base}/{genome_name}.gtf",
                "out": genome_base,
                "align_index": ["bowtie2", "blast"],
                "jellyfish": False
            }
    elif action == "delete":
        if genome_name in data:
            del data[genome_name]
            
    # Save back
    try:
        # Ensure parent directory exists
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception as e:
        print(f"Error saving {username}'s genomes.yaml: {e}")

@genome.get("/", response_model=List[dict])
def list_genomes(current_user: User = Depends(get_current_active_user)):
    try:
        genomes_dict = {}
        
        # Add public genomes
        public_dir = get_public_genomes_dir()
        if public_dir.exists():
            for x in public_dir.iterdir():
                if x.is_dir() and not x.name.startswith('.'):
                    genomes_dict[x.name] = {"name": x.name, "is_public": True}
                    
        # Add user genomes
        user_dir = get_user_genomes_dir(current_user.username)
        if user_dir.exists():
            for x in user_dir.iterdir():
                if x.is_dir() and not x.name.startswith('.'):
                    genomes_dict[x.name] = {"name": x.name, "is_public": False}
                    
        return list(genomes_dict.values())
    except Exception as e:
        return [{"error": str(e)}]

@genome.get("/{genome_name}/files")
async def list_genome_files(genome_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        if not genome_dir.exists():
            raise HTTPException(status_code=404, detail="Genome directory not found")
        
        # 递归获取所有文件和文件夹的相对路径
        files = []
        
        def scan_directory(directory: Path, relative_path: str = ""):
            for item in directory.iterdir():
                if item.name.startswith('.'):  # 跳过隐藏文件
                    continue
                    
                item_relative_path = f"{relative_path}/{item.name}" if relative_path else item.name
                
                if item.is_file():
                    files.append(item_relative_path)
                elif item.is_dir():
                    # 递归扫描子目录
                    scan_directory(item, item_relative_path)
        
        scan_directory(genome_dir)
        return {"genome": genome_name, "files": files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.get("/{genome_name}/{file_name:path}/metadata")
async def get_file_metadata(genome_name: str, file_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        file_path = genome_dir / file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        file_stats = os.stat(file_path)
        
        # 检查是否为预设文件（基于创建时间或特定标记）
        # 这里假设预设文件是在特定时间之前创建的，或者在特定目录中
        preset_genomes = {'hg38', 'hg19', 'mm10', 'mm9'}
        is_preset = genome_name in preset_genomes
        
        # 也可以通过判断是否在 public 目录下
        is_public = str(file_path).startswith(str(get_public_genomes_dir()))
        
        # 或者可以基于文件的创建时间来判断
        # 假设2024年1月1日之前的文件都是预设文件
        preset_cutoff = datetime(2024, 1, 1).timestamp()
        is_preset_by_time = file_stats.st_ctime < preset_cutoff
        
        return {
            "size": file_stats.st_size,
            "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "is_preset": is_preset or is_preset_by_time or is_public,
            "can_delete": not (is_preset or is_preset_by_time or is_public)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")

@genome.post("/{genome_name}/upload")
async def upload_genome_file(genome_name: str, file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    try:
        # 只允许上传到用户的私有目录
        genome_dir = get_user_genomes_dir(current_user.username) / genome_name
        if not genome_dir.exists():
            genome_dir.mkdir(parents=True, exist_ok=True)
            # 如果是新创建的目录，更新 yaml
            update_genomes_yaml(genome_name, current_user.username, "add")
        
        # 支持更多文件类型，包括.gitkeep等
        allowed_extensions = {'fa', 'fna', 'fasta', 'gff', 'gtf', 'jf', 'sam', 'bam', 'txt', 'gitkeep', 'fai'}
        
        # 处理文件路径，支持文件夹结构
        filename = file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # 检查文件扩展名（跳过.gitkeep等特殊文件的检查）
        if '.' in filename:
            file_extension = filename.split(".")[-1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # 创建完整的文件路径，支持子目录
        file_path = genome_dir / filename
        
        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, "wb") as f:
            content = await file.read() 
            f.write(content)
            
        # 如果上传的是 fasta 或 gtf 文件，尝试更新 genomes.yaml 中的具体路径
        if filename.endswith(('.fa', '.fasta', '.fna', '.gtf', '.gff')):
            yaml_path = get_user_genomes_yaml(current_user.username)
            if yaml_path.exists():
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f) or {}
                    if genome_name in data:
                        if filename.endswith(('.fa', '.fasta', '.fna')):
                            data[genome_name]['fasta'] = str(file_path)
                        elif filename.endswith(('.gtf', '.gff')):
                            data[genome_name]['gtf'] = str(file_path)
                        with open(yaml_path, 'w', encoding='utf-8') as f:
                            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                except Exception as e:
                    print(f"Error updating specific file paths in {current_user.username}'s genomes.yaml: {e}")
            
        return {"message": f"File '{filename}' uploaded successfully to {genome_name}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.post("/{genome_name}")
async def add_genome(genome_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        # 检查是否与 public 冲突
        public_dir = get_public_genomes_dir() / genome_name
        if public_dir.exists():
            raise HTTPException(status_code=400, detail="A public genome with this name already exists")
            
        new_genome_dir = get_user_genomes_dir(current_user.username) / genome_name
        if new_genome_dir.exists():
            raise HTTPException(status_code=400, detail="Genome directory already exists")
        new_genome_dir.mkdir(parents=True, exist_ok=True)
        
        # 自动更新 genomes.yaml
        update_genomes_yaml(genome_name, current_user.username, "add")
        
        return {"message": f"Genome {genome_name} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.delete("/{genome_name}/{file_name:path}")
async def delete_file(genome_name: str, file_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        file_path = (genome_dir / file_name).resolve()
        
        # 安全检查：确保文件路径在genome目录内
        if not str(file_path).startswith(str(genome_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 权限检查：检查是否在 public 目录下
        if str(file_path).startswith(str(get_public_genomes_dir())):
            raise HTTPException(status_code=403, detail="Cannot delete public files")
            
        # 权限检查：检查是否为预设文件
        file_stats = os.stat(file_path)
        preset_genomes = {'hg38', 'hg19', 'mm10', 'mm9'}
        is_preset = genome_name in preset_genomes
        
        # 基于创建时间判断是否为预设文件
        preset_cutoff = datetime(2024, 1, 1).timestamp()
        is_preset_by_time = file_stats.st_ctime < preset_cutoff
        
        if is_preset or is_preset_by_time:
            raise HTTPException(status_code=403, detail="Cannot delete preset files")
            
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            # 检查目录中的所有文件是否都可以删除
            for root, dirs, files in os.walk(file_path):
                for f in files:
                    f_path = Path(root) / f
                    f_stats = os.stat(f_path)
                    if f_stats.st_ctime < preset_cutoff:
                        raise HTTPException(status_code=403, detail=f"Cannot delete directory containing preset files: {f}")
            shutil.rmtree(file_path)
            
        return {"message": f"File '{file_name}' deleted successfully from {genome_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@genome.get("/{genome_name}/{file_name:path}")
async def download_file(genome_name: str, file_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        file_path = (genome_dir / file_name).resolve()
        
        # 安全检查：确保文件路径在genome目录内
        if not str(file_path).startswith(str(genome_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
            
        # 获取文件名（不包含路径）
        actual_filename = file_path.name
        return FileResponse(path=str(file_path), filename=actual_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@genome.delete("/{genome_name}")
async def delete_genome_directory(genome_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        # 只能删除用户自己目录下的
        genome_dir = get_user_genomes_dir(current_user.username) / genome_name
        if not genome_dir.exists():
            # 如果是 public 下的，提示不能删除
            public_dir = get_public_genomes_dir() / genome_name
            if public_dir.exists():
                raise HTTPException(status_code=403, detail="Cannot delete public genome directory")
            raise HTTPException(status_code=404, detail="Genome directory not found")
            
        shutil.rmtree(genome_dir)
        
        # 自动更新 genomes.yaml
        update_genomes_yaml(genome_name, current_user.username, "delete")
        
        return {"message": f"Genome directory '{genome_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
