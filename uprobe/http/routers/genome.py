from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from datetime import datetime
import shutil
import os


genome = APIRouter(prefix="/genome", tags=["genome"])
genome_path = Path('/mnt/d/repos/testdata/genomes')

@genome.get("/", response_model=List[str])
def list_genomes():
    try:
        genomes = [x.name for x in genome_path.iterdir() if x.is_dir() and not x.name.startswith('.')]
        return genomes
    except Exception as e:
        return {"error": str(e)}

@genome.get("/{genome_name}/files")
async def list_genome_files(genome_name: str):
    try:
        genome_dir = genome_path / genome_name
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
async def get_file_metadata(genome_name: str, file_name: str):
    try:
        file_path = genome_path / genome_name / file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        file_stats = os.stat(file_path)
        
        # 检查是否为预设文件（基于创建时间或特定标记）
        # 这里假设预设文件是在特定时间之前创建的，或者在特定目录中
        preset_genomes = {'hg38', 'hg19', 'mm10', 'mm9'}
        is_preset = genome_name in preset_genomes
        
        # 或者可以基于文件的创建时间来判断
        # 假设2024年1月1日之前的文件都是预设文件
        preset_cutoff = datetime(2024, 1, 1).timestamp()
        is_preset_by_time = file_stats.st_ctime < preset_cutoff
        
        return {
            "size": file_stats.st_size,
            "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "is_preset": is_preset or is_preset_by_time,
            "can_delete": not (is_preset or is_preset_by_time)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")

@genome.post("/{genome_name}/upload")
async def upload_genome_file(genome_name: str, file: UploadFile = File(...)):
    try:
        genome_dir = genome_path / genome_name
        if not genome_dir.exists():
            genome_dir.mkdir(parents=True, exist_ok=True)
        
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
            
        return {"message": f"File '{filename}' uploaded successfully to {genome_name}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.post("/{genome_name}")
async def add_genome(genome_name: str):
    try:
        new_genome_dir = genome_path / genome_name
        if new_genome_dir.exists():
            raise HTTPException(status_code=400, detail="Genome directory already exists")
        new_genome_dir.mkdir()
        return {"message": f"Genome {genome_name} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.delete("/{genome_name}/{file_name:path}")
async def delete_file(genome_name: str, file_name: str):
    try:
        file_path = (genome_path / genome_name / file_name).resolve()
        
        # 安全检查：确保文件路径在genome目录内
        genome_dir = (genome_path / genome_name).resolve()
        if not str(file_path).startswith(str(genome_dir)):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
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
async def download_file(genome_name: str, file_name: str):
    try:
        file_path = (genome_path / genome_name / file_name).resolve()
        
        # 安全检查：确保文件路径在genome目录内
        genome_dir = (genome_path / genome_name).resolve()
        if not str(file_path).startswith(str(genome_dir)):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
            
        # 获取文件名（不包含路径）
        actual_filename = file_path.name
        return FileResponse(path=str(file_path), filename=actual_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@genome.delete("/{genome_name}")
async def delete_genome_directory(genome_name: str):
    try:
        genome_dir = genome_path / genome_name
        if not genome_dir.exists():
            raise HTTPException(status_code=404, detail="Genome directory not found")
        shutil.rmtree(genome_dir)
        return {"message": f"Genome directory '{genome_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
