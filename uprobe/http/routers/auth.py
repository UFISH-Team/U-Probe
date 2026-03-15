from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
import os
import re
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- Configuration ---
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")  # In a real app, use a secure, environment-variable-based key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- SMTP Configuration ---
# Read from environment variables or use defaults
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.163.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER = os.environ.get("SMTP_USER", "your_email@163.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your_auth_code")

# --- Router Setup ---
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# --- Password Hashing ---
def build_pwd_context():
    try:
        test_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        test_ctx.hash("probe-test")
        return test_ctx
    except Exception:
        return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

pwd_context = build_pwd_context()

# --- OAuth2 Scheme ---
oauth2_scheme = HTTPBearer()

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    email_or_username: str  # 支持邮箱或用户名登录
    password: str
    remember_me: Optional[bool] = False  # 记住我选项

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str
    
    @validator('email')
    def validate_email(cls, v):
        # 基础邮箱格式验证，不再限制特定域名
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.lower()):
            raise ValueError('Please enter a valid email address')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Username must be at least 2 characters long')
        # 可以添加更多关于用户名的规则，比如不能包含特殊字符等
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v.strip()

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    avatar_url: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user_info: User

class TokenData(BaseModel):
    username: Optional[str] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.lower()):
            raise ValueError('Please enter a valid email address')
        return v.lower()

class ResetPasswordRequest(BaseModel):
    email: str
    reset_code: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class SendVerificationCodeRequest(BaseModel):
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.lower()):
            raise ValueError('Please enter a valid email address')
        return v.lower()

class RegisterWithCodeRequest(BaseModel):
    email: str
    verification_code: str
    password: str
    username: str
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.lower()):
            raise ValueError('Please enter a valid email address')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Username must be at least 2 characters long')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v.strip()

class UserInDB(User):
    hashed_password: str

from uprobe.http.paths import get_data_dir

# --- User Database File ---
USERS_DB_FILE = get_data_dir() / "users_db.json"

def load_users_db():
    """Load users from JSON file, create default if not exists"""
    if os.path.exists(USERS_DB_FILE):
        try:
            with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Create default user database
    default_db = {
        "root": {
            "username": "root",
            "full_name": "Zhang Qian",
            "email": "qian.zhang@uprobe.com",
            "hashed_password": pwd_context.hash("123456"),
            "disabled": False,
            "avatar_url": None,
            "title": "Researcher",
            "department": "Research & Development",
            "location": "Not set",
            "phone": "Not set",
            "bio": "Researcher specializing in probe design and bioinformatics analysis."
        }
    }
    save_users_db(default_db)
    return default_db

def save_users_db(users_db):
    """Save users to JSON file"""
    try:
        with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
            # Save all user data including hashed passwords
            json.dump(users_db, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving users database: {e}")

# Load users database
fake_users_db = load_users_db()

def get_db():
    """Helper to always get the latest DB state from memory"""
    global fake_users_db
    return fake_users_db

# 存储密码重置代码（在生产环境中应该使用Redis或数据库）
reset_codes = {}

# 存储注册验证码
verification_codes = {}

# --- Utility Functions ---
def send_email_sync(to_email: str, subject: str, body: str) -> bool:
    """同步发送邮件函数"""
    if SMTP_USER == "your_email@163.com":
        print(f"Warning: SMTP not configured. Would send to {to_email}: {body}")
        return True
        
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def get_user_by_email(db, email: str):
    """通过邮箱查找用户"""
    for username, user_data in db.items():
        if user_data.get('email') == email:
            return UserInDB(**user_data)
    return None

def generate_username_from_email(email: str) -> str:
    """从邮箱生成用户名"""
    # 取邮箱@前的部分作为用户名
    username = email.split('@')[0]
    return username

def is_email_exists(db, email: str) -> bool:
    """检查邮箱是否已存在"""
    for user_data in db.values():
        if user_data.get('email') == email:
            return True
    return False

def is_username_exists(db, username: str) -> bool:
    """检查用户名是否已存在"""
    return username in db

def generate_reset_code() -> str:
    """生成隔6位数字重置代码"""
    return ''.join(random.choices(string.digits, k=6))

def store_reset_code(email: str, code: str):
    """存储重置代码，有10分钟过期"""
    expiry_time = datetime.now() + timedelta(minutes=10)
    reset_codes[email] = {
        'code': code,
        'expiry': expiry_time
    }

def verify_reset_code(email: str, code: str) -> bool:
    """验证重置代码"""
    if email not in reset_codes:
        return False
    
    stored_data = reset_codes[email]
    if datetime.now() > stored_data['expiry']:
        # 代码已过期
        del reset_codes[email]
        return False
    
    return stored_data['code'] == code

def clear_reset_code(email: str):
    """清除使用过的重置代码"""
    if email in reset_codes:
        del reset_codes[email]

def store_verification_code(email: str, code: str):
    """存储注册验证码，10分钟过期"""
    expiry_time = datetime.now() + timedelta(minutes=10)
    verification_codes[email] = {
        'code': code,
        'expiry': expiry_time
    }

def verify_verification_code(email: str, code: str) -> bool:
    """验证注册验证码"""
    if email not in verification_codes:
        return False
    
    stored_data = verification_codes[email]
    if datetime.now() > stored_data['expiry']:
        del verification_codes[email]
        return False
    
    return stored_data['code'] == code

def clear_verification_code(email: str):
    """清除使用过的注册验证码"""
    if email in verification_codes:
        del verification_codes[email]

def get_user_by_email_or_username(db, email_or_username: str):
    """通过邮箱或用户名查找用户"""
    # 先尝试作为用户名查找（管理员账户）
    if email_or_username in db:
        user_dict = db[email_or_username]
        return UserInDB(**user_dict)
    
    # 再尝试作为邮箱查找（普通用户）
    for username, user_data in db.items():
        if user_data.get('email') == email_or_username:
            return UserInDB(**user_data)
    
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Always reload from file to ensure we have latest state across workers
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- API Endpoints ---
@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(login_request: LoginRequest):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    user = get_user_by_email_or_username(db, login_request.email_or_username)
    if not user or not pwd_context.verify(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 根据记住我选项设置不同的过期时间
    if login_request.remember_me:
        access_token_expires = timedelta(days=30)  # 30天
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 30分钟
    
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    user_info = User.model_validate(user)

    return {
        "token": access_token,
        "token_type": "bearer",
        "user_info": user_info,
    }

@router.post("/register", response_model=LoginResponse)
async def register_user(register_request: RegisterRequest):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # 检查邮箱是否已存在
    if is_email_exists(db, register_request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )
    
    # 检查用户名是否已存在
    if is_username_exists(db, register_request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    
    # 创建新用户
    hashed_password = pwd_context.hash(register_request.password)
    new_user_data = {
        "username": register_request.username,
        "full_name": register_request.username, # 默认将全名设为用户名
        "email": register_request.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "avatar_url": None,
        "title": "Researcher",
        "department": "Research & Development",
        "location": "Not set",
        "phone": "Not set",
        "bio": "Researcher specializing in probe design and bioinformatics analysis."
    }
    
    # 保存到数据库
    db[register_request.username] = new_user_data
    save_users_db(db)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": register_request.username}, expires_delta=access_token_expires
    )
    
    # 返回用户信息
    user_info = User(**new_user_data)
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user_info": user_info,
    }

@router.post("/send-verification-code")
async def send_verification_code(request: SendVerificationCodeRequest):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # 检查邮箱是否已存在
    if is_email_exists(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )
    
    # 生成验证码
    code = generate_reset_code()  # 复用生成6位数字的函数
    store_verification_code(request.email, code)
    
    # 发送邮件
    subject = "🔬U-Probe - Registration Verification Code"
    body = f"🔬Welcome to U-Probe! \n\nA universal probe design platform.\n\nYour registration verification code is: {code}\n\nThis code will expire in 10 minutes.\nIf you did not request this, please ignore this email."
    
    success = send_email_sync(request.email, subject, body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )
        
    return {"message": "Verification code sent successfully"}

@router.post("/register-with-code", response_model=LoginResponse)
async def register_with_code(request: RegisterWithCodeRequest):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # 检查邮箱是否已存在
    if is_email_exists(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )
        
    # 检查用户名是否已存在
    if is_username_exists(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
        
    # 验证验证码
    if not verify_verification_code(request.email, request.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
        
    # 创建新用户
    hashed_password = pwd_context.hash(request.password)
    new_user_data = {
        "username": request.username,
        "full_name": request.username, # 默认将全名设为用户名
        "email": request.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "avatar_url": None,
        "title": "Researcher",
        "department": "Research & Development",
        "location": "Not set",
        "phone": "Not set",
        "bio": "Researcher specializing in probe design and bioinformatics analysis."
    }
    
    # 保存到数据库
    db[request.username] = new_user_data
    save_users_db(db)
    
    # 清除验证码
    clear_verification_code(request.email)
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    
    # 返回用户信息
    user_info = User(**new_user_data)
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user_info": user_info,
    }

@router.post("/logout")
async def logout():
    # On the client-side, the token should be deleted.
    # This endpoint is mostly for formality.
    return {"message": "Successfully logged out"}

@router.get("/check", response_model=User)
async def check_token(current_user: User = Depends(get_current_active_user)):
    # Get the full user data from database to ensure all fields are included
    user_data = fake_users_db.get(current_user.username)
    if user_data:
        return User(**user_data)
    return current_user

@router.put("/profile", response_model=User)
async def update_profile(
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # Update user in database
    if current_user.username in db:
        if user_update.full_name is not None:
            db[current_user.username]["full_name"] = user_update.full_name
        if user_update.email is not None:
            db[current_user.username]["email"] = user_update.email
        if user_update.title is not None:
            db[current_user.username]["title"] = user_update.title
        if user_update.department is not None:
            db[current_user.username]["department"] = user_update.department
        if user_update.location is not None:
            db[current_user.username]["location"] = user_update.location
        if user_update.phone is not None:
            db[current_user.username]["phone"] = user_update.phone
        if user_update.bio is not None:
            db[current_user.username]["bio"] = user_update.bio
        
        # Save to file
        save_users_db(db)
        
        # Return updated user info
        updated_user = get_user(db, current_user.username)
        return User.model_validate(updated_user)
    
    raise HTTPException(status_code=404, detail="User not found")

@router.put("/password")
async def update_password(
    password_update: PasswordUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # Get user from DB
    user_in_db = get_user(db, current_user.username)
    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not pwd_context.verify(password_update.current_password, user_in_db.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Hash new password
    new_hashed_password = pwd_context.hash(password_update.new_password)
    
    # Update password in database
    db[current_user.username]["hashed_password"] = new_hashed_password
    save_users_db(db)
    
    return {"message": "Password updated successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # 检查邮箱是否存在
    user = get_user_by_email(db, request.email)
    if not user:
        # 为了安全起见，不要透露邮箱是否存在
        return {"message": "If the email exists, a reset code has been sent."}
    
    # 生成重置代码
    reset_code = generate_reset_code()
    store_reset_code(request.email, reset_code)
    
    # 发送密码重置邮件
    subject = "UProbe - Password Reset Code"
    body = f"Hello,\n\nYour password reset code is: {reset_code}\n\nThis code will expire in 10 minutes.\nIf you did not request a password reset, please ignore this email."
    
    success = send_email_sync(request.email, subject, body)
    if not success:
        print(f"Failed to send reset code {reset_code} to {request.email}")
        # We still return success to the user to not leak email existence, 
        # but in a real app we might want to log this or handle it differently.
    
    return {"message": "If the email exists, a reset code has been sent."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    # Always reload from file to ensure we have latest state
    db = load_users_db()
    global fake_users_db
    fake_users_db = db
    
    # 验证重置代码
    if not verify_reset_code(request.email, request.reset_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # 查找用户
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新密码
    new_hashed_password = pwd_context.hash(request.new_password)
    db[user.username]["hashed_password"] = new_hashed_password
    save_users_db(db)
    
    # 清除重置代码
    clear_reset_code(request.email)
    
    return {"message": "Password has been reset successfully"}
