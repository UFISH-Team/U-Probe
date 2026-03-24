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

origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
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
    uvicorn.run(app, host="127.0.0.1", log_config=None)

if __name__ == "__main__":
    start_server()

# uvicorn uprobe.http.server:app --reload
