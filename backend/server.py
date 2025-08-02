from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, date
import jwt
import bcrypt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT and Password hashing
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Authentication Models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Task Models
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    completed: bool = False
    order_index: int = 0
    task_date: str  # YYYY-MM-DD format
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class TaskCreate(BaseModel):
    title: str
    task_date: Optional[str] = None  # If not provided, use today

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None
    order_index: Optional[int] = None

class TaskReorder(BaseModel):
    task_orders: List[dict]  # [{"id": "task_id", "order_index": 0}, ...]

class DailyProgress(BaseModel):
    date: str
    total_tasks: int
    completed_tasks: int
    completion_percentage: float
    tasks: List[Task]

class WeeklyProgress(BaseModel):
    week_start: str
    week_end: str
    daily_progress: List[DailyProgress]
    week_total_tasks: int
    week_completed_tasks: int
    week_completion_percentage: float

# Authentication helpers
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    user = User(username=user_data.username, hashed_password=hashed_password)
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user["id"],
        username=user["username"]
    )

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.id, "username": current_user.username}

# Task Routes
@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    # Use today's date if not provided
    task_date = task_data.task_date or date.today().strftime("%Y-%m-%d")
    
    # Get the current max order_index for this user and date
    existing_tasks = await db.tasks.find({"user_id": current_user.id, "task_date": task_date}).to_list(1000)
    max_order = max([t.get("order_index", 0) for t in existing_tasks], default=-1)
    
    task = Task(
        user_id=current_user.id,
        title=task_data.title,
        task_date=task_date,
        order_index=max_order + 1
    )
    
    await db.tasks.insert_one(task.dict())
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(task_date: Optional[str] = None, current_user: User = Depends(get_current_user)):
    # Use today's date if not provided
    if not task_date:
        task_date = date.today().strftime("%Y-%m-%d")
    
    tasks = await db.tasks.find({"user_id": current_user.id, "task_date": task_date}).to_list(1000)
    # Sort by order_index
    tasks_sorted = sorted(tasks, key=lambda x: x.get("order_index", 0))
    return [Task(**task) for task in tasks_sorted]

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate, current_user: User = Depends(get_current_user)):
    # Find the task
    task = await db.tasks.find_one({"id": task_id, "user_id": current_user.id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    update_data = {}
    if task_update.title is not None:
        update_data["title"] = task_update.title
    if task_update.completed is not None:
        update_data["completed"] = task_update.completed
        if task_update.completed:
            update_data["completed_at"] = datetime.utcnow()
        else:
            update_data["completed_at"] = None
    if task_update.order_index is not None:
        update_data["order_index"] = task_update.order_index
    
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    
    # Get updated task
    updated_task = await db.tasks.find_one({"id": task_id})
    return Task(**updated_task)

@api_router.post("/tasks/reorder")
async def reorder_tasks(reorder_data: TaskReorder, current_user: User = Depends(get_current_user)):
    # Update order_index for each task
    for task_order in reorder_data.task_orders:
        await db.tasks.update_one(
            {"id": task_order["id"], "user_id": current_user.id},
            {"$set": {"order_index": task_order["order_index"]}}
        )
    
    return {"message": "Tasks reordered successfully"}

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    result = await db.tasks.delete_one({"id": task_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted successfully"}

@api_router.get("/tasks/stats")
async def get_task_stats(task_date: Optional[str] = None, current_user: User = Depends(get_current_user)):
    # Use today's date if not provided
    if not task_date:
        task_date = date.today().strftime("%Y-%m-%d")
    
    tasks = await db.tasks.find({"user_id": current_user.id, "task_date": task_date}).to_list(1000)
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get("completed", False)])
    
    return {
        "date": task_date,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "remaining_tasks": total_tasks - completed_tasks,
        "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

# New History and Progress Routes
@api_router.get("/tasks/history", response_model=List[DailyProgress])
async def get_task_history(days: int = 7, current_user: User = Depends(get_current_user)):
    """Get task history for the last N days"""
    history = []
    
    for i in range(days):
        target_date = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        tasks = await db.tasks.find({"user_id": current_user.id, "task_date": target_date}).to_list(1000)
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("completed", False)])
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        daily_progress = DailyProgress(
            date=target_date,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_percentage=completion_percentage,
            tasks=[Task(**task) for task in sorted(tasks, key=lambda x: x.get("order_index", 0))]
        )
        
        history.append(daily_progress)
    
    return history

@api_router.get("/tasks/weekly-progress", response_model=WeeklyProgress)
async def get_weekly_progress(current_user: User = Depends(get_current_user)):
    """Get weekly progress starting from Monday"""
    today = date.today()
    
    # Calculate Monday of current week
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    
    daily_progress = []
    week_total_tasks = 0
    week_completed_tasks = 0
    
    for i in range(7):
        current_date = monday + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        tasks = await db.tasks.find({"user_id": current_user.id, "task_date": date_str}).to_list(1000)
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("completed", False)])
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        week_total_tasks += total_tasks
        week_completed_tasks += completed_tasks
        
        daily_progress.append(DailyProgress(
            date=date_str,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_percentage=completion_percentage,
            tasks=[Task(**task) for task in sorted(tasks, key=lambda x: x.get("order_index", 0))]
        ))
    
    week_completion_percentage = (week_completed_tasks / week_total_tasks * 100) if week_total_tasks > 0 else 0
    
    return WeeklyProgress(
        week_start=monday.strftime("%Y-%m-%d"),
        week_end=sunday.strftime("%Y-%m-%d"),
        daily_progress=daily_progress,
        week_total_tasks=week_total_tasks,
        week_completed_tasks=week_completed_tasks,
        week_completion_percentage=week_completion_percentage
    )

@api_router.get("/tasks/date/{task_date}", response_model=List[Task])
async def get_tasks_by_date(task_date: str, current_user: User = Depends(get_current_user)):
    """Get tasks for a specific date"""
    tasks = await db.tasks.find({"user_id": current_user.id, "task_date": task_date}).to_list(1000)
    tasks_sorted = sorted(tasks, key=lambda x: x.get("order_index", 0))
    return [Task(**task) for task in tasks_sorted]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()