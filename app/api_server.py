"""
FastAPI REST API wrapper for Tatort on the Road video processor.
Provides endpoints for video analysis with async task processing.
"""
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import threading
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.processor_workflow import process_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Tatort on the Road API",
    description="AI-powered car scene extraction for video analysis",
    version="1.0.0"
)

# Add CORS middleware for n8n compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task status tracking
class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    video_filename: str
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    stats: Optional[dict] = None

# In-memory task store (use Redis in production)
tasks: dict[str, TaskInfo] = {}
tasks_lock = threading.Lock()

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def _process_video_task(task_id: str, video_path: str, output_dir: str) -> None:
    """Background task to process video."""
    try:
        with tasks_lock:
            tasks[task_id].status = TaskStatus.PROCESSING
            tasks[task_id].started_at = datetime.now().isoformat()
        
        logger.info(f"Starting video processing for task {task_id}: {video_path}")
        
        output_file, stats = process_video(video_path, output_dir)
        
        with tasks_lock:
            if output_file:
                tasks[task_id].status = TaskStatus.COMPLETED
                tasks[task_id].output_file = output_file
                tasks[task_id].stats = stats
                logger.info(f"Task {task_id} completed successfully: {output_file}")
            else:
                tasks[task_id].status = TaskStatus.FAILED
                tasks[task_id].error_message = "Processing returned no output. No scenes detected."
                logger.warning(f"Task {task_id}: No scenes detected")
            
            tasks[task_id].completed_at = datetime.now().isoformat()
    
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {str(e)}", exc_info=True)
        with tasks_lock:
            tasks[task_id].status = TaskStatus.FAILED
            tasks[task_id].error_message = str(e)
            tasks[task_id].completed_at = datetime.now().isoformat()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Tatort on the Road API"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Tatort on the Road API",
        "version": "1.0.0",
        "description": "AI-powered car scene extraction for video analysis",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze - Submit video for analysis",
            "status": "GET /tasks/{task_id} - Check task status",
            "download": "GET /tasks/{task_id}/download - Download result video",
            "list_tasks": "GET /tasks - List all tasks"
        }
    }


@app.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Submit a video file for scene analysis.
    
    Returns:
        task_id: Unique identifier for tracking the analysis job
        status: Current status of the task
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Generate unique task ID and save file
        task_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        saved_filename = f"{task_id}{file_extension}"
        video_path = UPLOAD_DIR / saved_filename
        
        # Save uploaded file
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Task {task_id}: Saved uploaded file {file.filename} -> {video_path}")
        
        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            video_filename=file.filename
        )
        
        with tasks_lock:
            tasks[task_id] = task_info
        
        # Start background processing
        background_tasks.add_task(
            _process_video_task,
            task_id,
            str(video_path),
            str(OUTPUT_DIR)
        )
        
        logger.info(f"Task {task_id} queued for processing")
        
        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "message": "Video submitted for analysis. Check status with /tasks/{task_id}"
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def list_tasks(status: Optional[TaskStatus] = None):
    """List all tasks, optionally filtered by status."""
    with tasks_lock:
        all_tasks = list(tasks.values())
    
    if status:
        all_tasks = [t for t in all_tasks if t.status == status]
    
    return {
        "total": len(all_tasks),
        "tasks": all_tasks
    }


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task."""
    with tasks_lock:
        task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task


@app.get("/tasks/{task_id}/download")
async def download_result(task_id: str):
    """Download the processed video file."""
    with tasks_lock:
        task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is in {task.status} status. Cannot download incomplete task."
        )
    
    if not task.output_file or not os.path.exists(task.output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        task.output_file,
        filename=Path(task.output_file).name,
        media_type="video/mp4"
    )


@app.post("/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """Clean up uploaded and output files for a task."""
    with tasks_lock:
        task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    try:
        # Find and remove uploaded file
        for file in UPLOAD_DIR.glob(f"{task_id}*"):
            file.unlink()
            logger.info(f"Deleted uploaded file: {file}")
        
        # Remove output file if it exists
        if task.output_file and os.path.exists(task.output_file):
            os.unlink(task.output_file)
            logger.info(f"Deleted output file: {task.output_file}")
        
        # Remove task from tracking
        with tasks_lock:
            del tasks[task_id]
        
        return {"message": f"Task {task_id} cleaned up successfully"}
    
    except Exception as e:
        logger.error(f"Error cleaning up task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cleanup")
async def cleanup_all():
    """Clean up all completed and failed tasks."""
    removed_tasks = []
    
    try:
        with tasks_lock:
            task_list = list(tasks.items())
        
        for task_id, task in task_list:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                # Clean up files
                for file in UPLOAD_DIR.glob(f"{task_id}*"):
                    file.unlink()
                
                if task.output_file and os.path.exists(task.output_file):
                    os.unlink(task.output_file)
                
                with tasks_lock:
                    del tasks[task_id]
                
                removed_tasks.append(task_id)
                logger.info(f"Cleaned up task: {task_id}")
        
        return {
            "message": "Cleanup completed",
            "removed_tasks": removed_tasks,
            "count": len(removed_tasks)
        }
    
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
