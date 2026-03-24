from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from ..routers.auth import get_current_active_user, User, save_users_db, fake_users_db
from uprobe.http.utils.paths import get_data_dir
import shutil
import os

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

# Create a directory for storing avatars if it doesn't exist
AVATAR_DIR = get_data_dir() / "avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

@router.get("/avatars/{filename}")
async def get_avatar(filename: str):
    file_path = AVATAR_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(str(file_path))

@router.post("/upload-avatar", response_model=User)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    # Generate a safe filename
    file_extension = os.path.splitext(file.filename)[1]
    avatar_filename = f"{current_user.username}{file_extension}"
    avatar_path = os.path.join(AVATAR_DIR, avatar_filename)
    
    # Save the file
    try:
        with open(avatar_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save avatar: {e}")

    # Update user's avatar URL in the database
    # We serve avatars via a new endpoint or mount
    avatar_url = f"/user/avatars/{avatar_filename}"
    if current_user.username in fake_users_db:
        fake_users_db[current_user.username]["avatar_url"] = avatar_url
        save_users_db(fake_users_db)
    else:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Manually create a user model to return, as get_user doesn't have avatar_url
    updated_user_data = fake_users_db[current_user.username]
    
    return User(**updated_user_data)
