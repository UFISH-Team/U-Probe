import sys
import os
from pathlib import Path
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback to simple parsing if python-dotenv is not installed
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

from uprobe.http.utils.logger import setup_logging
from uprobe.http.utils.paths import get_config
setup_logging()

# uprobe.http/server/app.py
from fastapi import FastAPI
import uvicorn

from uprobe.http.routers.genome import genome 
from uprobe.http.routers.workflow import workflow 
from uprobe.http.routers.task import router as task
from uprobe.http.routers.auth import router as auth_router
from uprobe.http.routers.user import router as user_router
from uprobe.http.routers.agent import agent_router
from uprobe.http.routers.custom_probes import router as custom_probes_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    from uprobe.http.routers.task import reset_stuck_tasks_on_startup
    reset_stuck_tasks_on_startup()

config = get_config()
frontend_url = config.get("Server", "frontend_url", fallback="http://localhost:5173")
if os.getenv("FRONTEND_URL"):
    frontend_url = os.getenv("FRONTEND_URL")

origins = [
    frontend_url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# routers
app.include_router(genome)
app.include_router(workflow)
app.include_router(task)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(agent_router)
app.include_router(custom_probes_router)

def start_server():
    config = get_config()
    
    # Read from config.ini, fallback to defaults
    env = config.get("Server", "app_env", fallback="development").lower()
    env = os.getenv("APP_ENV", env).lower()
    
    is_prod = env == "production"
    
    host = config.get("Server", "host", fallback="0.0.0.0" if is_prod else "127.0.0.1")
    host = os.getenv("HOST", host)
    
    port = config.getint("Server", "port", fallback=8000)
    port = int(os.getenv("PORT", port))
    
    default_workers = min(os.cpu_count() or 1, 6)
    
    workers_config = config.get("Server", "workers", fallback="")
    if workers_config and workers_config.isdigit():
        workers = int(workers_config)
    else:
        workers = default_workers if is_prod else 1
        
    workers = int(os.getenv("WORKERS", workers))
    
    reload = not is_prod

    print(f"Starting server in {env} mode on {host}:{port} with {workers} workers (reload={reload})")

    run_kwargs = {
        "host": host,
        "port": port,
        "workers": workers,
        "reload": reload,
        "log_level": "info",
        "access_log": True,
    }
    
    if reload:
        run_kwargs["reload_excludes"] = ["*.log", "*.log.*", "data/*", "logs/*", "results/*", "genomes/*", "temp/*"]

    uvicorn.run("uprobe.http.server:app", **run_kwargs)

if __name__ == "__main__":
    start_server()

# 开发模式启动: python -m uprobe.http.server (或 APP_ENV=development python -m uprobe.http.server)
# 生产模式启动: APP_ENV=production HOST=0.0.0.0 PORT=8000 WORKERS=4 python -m uprobe.http.server
