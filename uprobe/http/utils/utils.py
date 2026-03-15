import subprocess
from fastapi import HTTPException

def run_cmd(cmd: list) -> None:
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"Command executed successfully:\n{result.stdout}")
    else:
        print(f"Error executing command:\n{result.stderr}")
        raise HTTPException(status_code=500, detail=f"Error executing command: {' '.join(cmd)}\n{result.stderr}")
