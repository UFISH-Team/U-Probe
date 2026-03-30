from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from datetime import datetime
import shutil
import os
import yaml
from uprobe.http.utils.paths import get_public_genomes_dir, get_user_genomes_dir, get_genomes_yaml, get_user_genomes_yaml
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
    except HTTPException:
        raise
    except Exception as e:
        return [{"error": str(e)}]

@genome.get("/{genome_name}/files")
async def list_genome_files(genome_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        if not genome_dir.exists():
            raise HTTPException(status_code=404, detail="Genome directory not found")
        
        # Recursively get relative paths of all files and folders
        files = []
        
        def scan_directory(directory: Path, relative_path: str = ""):
            for item in directory.iterdir():
                if item.name.startswith('.') and item.name != '.gitkeep':  # Skip hidden files, but keep .gitkeep
                    continue
                    
                item_relative_path = f"{relative_path}/{item.name}" if relative_path else item.name
                
                if item.is_file():
                    files.append(item_relative_path)
                elif item.is_dir():
                    # Recursively scan subdirectories
                    scan_directory(item, item_relative_path)
        
        scan_directory(genome_dir)
        return {"genome": genome_name, "files": files}
    
    except HTTPException:
        raise
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
        
        # Check if it's a preset file (based on creation time or specific marker)
        # Assuming preset files were created before a specific time or in a specific directory
        preset_genomes = {'hg38', 'hg19', 'mm10', 'mm9'}
        is_preset = genome_name in preset_genomes
        
        # Can also determine by checking if it's in the public directory
        is_public = str(file_path).startswith(str(get_public_genomes_dir()))
        
        # Or determine based on file creation time
        # Assuming files before Jan 1, 2024 are preset files
        preset_cutoff = datetime(2024, 1, 1).timestamp()
        is_preset_by_time = file_stats.st_ctime < preset_cutoff
        
        return {
            "size": file_stats.st_size,
            "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
            "is_preset": is_preset or is_preset_by_time or is_public,
            "can_delete": not (is_preset or is_preset_by_time or is_public)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")

@genome.post("/{genome_name}/upload")
async def upload_genome_file(genome_name: str, file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    try:
        # Only allow uploading to user's private directory
        genome_dir = get_user_genomes_dir(current_user.username) / genome_name
        if not genome_dir.exists():
            genome_dir.mkdir(parents=True, exist_ok=True)
            # If it's a newly created directory, update yaml
            update_genomes_yaml(genome_name, current_user.username, "add")
        
        # Support more file types, including .gitkeep etc.
        allowed_extensions = {'fa', 'fna', 'fasta', 'gff', 'gtf', 'jf', 'sam', 'bam', 'txt', 'gitkeep', 'fai'}
        
        # Process file path, support folder structure
        filename = file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Check file extension (skip check for special files like .gitkeep)
        if '.' in filename:
            file_extension = filename.split(".")[-1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        # Create full file path, support subdirectories
        file_path = genome_dir / filename
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, "wb") as f:
            content = await file.read() 
            f.write(content)
            
        # If uploaded file is fasta or gtf, try to update specific paths in genomes.yaml
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.post("/{genome_name}")
async def add_genome(genome_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        # Check for conflict with public genomes
        public_dir = get_public_genomes_dir() / genome_name
        if public_dir.exists():
            raise HTTPException(status_code=400, detail="A public genome with this name already exists")
            
        new_genome_dir = get_user_genomes_dir(current_user.username) / genome_name
        if new_genome_dir.exists():
            raise HTTPException(status_code=400, detail="Genome directory already exists")
        new_genome_dir.mkdir(parents=True, exist_ok=True)
        
        # Automatically update genomes.yaml
        update_genomes_yaml(genome_name, current_user.username, "add")
        
        return {"message": f"Genome {genome_name} added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@genome.delete("/{genome_name}/{file_name:path}")
async def delete_file(genome_name: str, file_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        file_path = (genome_dir / file_name).resolve()
        
        # Security check: ensure file path is within genome directory
        if not str(file_path).startswith(str(genome_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Permission check: check if it's in public directory
        if str(file_path).startswith(str(get_public_genomes_dir())):
            raise HTTPException(status_code=403, detail="Cannot delete public files")
            
        # Permission check: check if it's a preset file
        file_stats = os.stat(file_path)
        preset_genomes = {'hg38', 'hg19', 'mm10', 'mm9'}
        is_preset = genome_name in preset_genomes
        
        # Determine if it's a preset file based on creation time
        preset_cutoff = datetime(2024, 1, 1).timestamp()
        is_preset_by_time = file_stats.st_ctime < preset_cutoff
        
        if is_preset or is_preset_by_time:
            raise HTTPException(status_code=403, detail="Cannot delete preset files")
            
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            # Check if all files in directory can be deleted
            for root, dirs, files in os.walk(file_path):
                for f in files:
                    f_path = Path(root) / f
                    f_stats = os.stat(f_path)
                    if f_stats.st_ctime < preset_cutoff:
                        raise HTTPException(status_code=403, detail=f"Cannot delete directory containing preset files: {f}")
            shutil.rmtree(file_path)
            
        return {"message": f"File '{file_name}' deleted successfully from {genome_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@genome.get("/{genome_name}/{file_name:path}")
async def download_file(genome_name: str, file_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        genome_dir = get_genome_dir(genome_name, current_user.username)
        file_path = (genome_dir / file_name).resolve()
        
        # Security check: ensure file path is within genome directory
        if not str(file_path).startswith(str(genome_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path")
            
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
            
        # Get filename (without path)
        actual_filename = file_path.name
        return FileResponse(path=str(file_path), filename=actual_filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@genome.delete("/{genome_name}")
async def delete_genome_directory(genome_name: str, current_user: User = Depends(get_current_active_user)):
    try:
        # Only allow deleting from user's own directory
        genome_dir = get_user_genomes_dir(current_user.username) / genome_name
        if not genome_dir.exists():
            # If it's under public, notify that it cannot be deleted
            public_dir = get_public_genomes_dir() / genome_name
            if public_dir.exists():
                raise HTTPException(status_code=403, detail="Cannot delete public genome directory")
            raise HTTPException(status_code=404, detail="Genome directory not found")
            
        shutil.rmtree(genome_dir)
        
        # Automatically update genomes.yaml
        update_genomes_yaml(genome_name, current_user.username, "delete")
        
        return {"message": f"Genome directory '{genome_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
