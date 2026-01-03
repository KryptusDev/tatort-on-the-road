# Tatort on the Road - API Documentation

Complete REST API reference for video scene extraction and analysis.

## Base URL

```
http://localhost:8000
```

## Overview

The API provides asynchronous video processing with task-based tracking. Upload videos, monitor processing status, and download results through simple HTTP endpoints.

### Key Features

- **Async Processing**: Submit videos and continue without blocking
- **Task Tracking**: Monitor progress with unique task IDs
- **Multiple Tasks**: Process multiple videos simultaneously
- **Automatic Cleanup**: Optional cleanup of completed tasks
- **CORS Enabled**: Ready for web applications and integrations

## Authentication

Currently no authentication required. Add authentication middleware for production deployments.

---

## Endpoints

### Health Check

Check if the API server is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "Tatort on the Road API"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Root / API Info

Get API information and available endpoints.

**Endpoint:** `GET /`

**Response:**
```json
{
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
```

---

### Submit Video for Analysis

Upload a video file for scene extraction processing.

**Endpoint:** `POST /analyze`

**Content-Type:** `multipart/form-data`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | File | Yes | Video file to process (MP4, AVI, MOV, etc.) |

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Video submitted for analysis. Check status with /tasks/{task_id}"
}
```

**Status Codes:**
- `200 OK`: Video submitted successfully
- `400 Bad Request`: Invalid file or missing filename
- `500 Internal Server Error`: Upload or processing error

**Example:**
```bash
# Upload a video file
curl -X POST http://localhost:8000/analyze \
  -F "file=@/path/to/video.mp4"

# Response
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Video submitted for analysis. Check status with /tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/analyze"
files = {"file": open("video.mp4", "rb")}

response = requests.post(url, files=files)
data = response.json()
task_id = data["task_id"]
print(f"Task ID: {task_id}")
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Task ID:', data.task_id);
```

---

### Get Task Status

Check the processing status of a submitted video.

**Endpoint:** `GET /tasks/{task_id}`

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `task_id` | string | UUID of the task returned from `/analyze` |

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "created_at": "2026-01-03T20:30:00.123456",
  "started_at": "2026-01-03T20:30:01.234567",
  "completed_at": "2026-01-03T20:32:45.678901",
  "video_filename": "video.mp4",
  "output_file": "/workspaces/tatort-on-the-road/output/result_a1b2c3d4_20260103_203245.mp4",
  "error_message": null,
  "stats": {
    "num_scenes": 5,
    "total_scene_duration": 45.2,
    "video_duration": 180.0,
    "coverage_percentage": 25.11
  }
}
```

**Task Status Values:**
| Status | Description |
|--------|-------------|
| `pending` | Task queued, not yet started |
| `processing` | Video is being analyzed |
| `completed` | Processing finished successfully |
| `failed` | Processing encountered an error |

**Status Codes:**
- `200 OK`: Task found
- `404 Not Found`: Task ID doesn't exist

**Example:**
```bash
curl http://localhost:8000/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Polling Example (Python):**
```python
import requests
import time

task_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
url = f"http://localhost:8000/tasks/{task_id}"

while True:
    response = requests.get(url)
    data = response.json()
    status = data["status"]
    
    print(f"Status: {status}")
    
    if status in ["completed", "failed"]:
        break
    
    time.sleep(5)  # Check every 5 seconds

if status == "completed":
    print(f"Processing complete! {data['stats']['num_scenes']} scenes detected")
else:
    print(f"Processing failed: {data['error_message']}")
```

---

### List All Tasks

Retrieve all tasks, optionally filtered by status.

**Endpoint:** `GET /tasks`

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | string | No | Filter by status: `pending`, `processing`, `completed`, or `failed` |

**Response:**
```json
{
  "total": 3,
  "tasks": [
    {
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "completed",
      "created_at": "2026-01-03T20:30:00.123456",
      "video_filename": "video1.mp4",
      "stats": { "num_scenes": 5 }
    },
    {
      "task_id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
      "status": "processing",
      "created_at": "2026-01-03T20:35:00.123456",
      "video_filename": "video2.mp4",
      "stats": null
    },
    {
      "task_id": "c3d4e5f6-g7h8-9012-cdef-gh3456789012",
      "status": "pending",
      "created_at": "2026-01-03T20:38:00.123456",
      "video_filename": "video3.mp4",
      "stats": null
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Request successful

**Examples:**
```bash
# Get all tasks
curl http://localhost:8000/tasks

# Get only completed tasks
curl http://localhost:8000/tasks?status=completed

# Get only processing tasks
curl http://localhost:8000/tasks?status=processing
```

---

### Download Processed Video

Download the result video for a completed task.

**Endpoint:** `GET /tasks/{task_id}/download`

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `task_id` | string | UUID of a completed task |

**Response:**
- **Content-Type:** `video/mp4`
- **Body:** Binary video file

**Status Codes:**
- `200 OK`: Download successful
- `400 Bad Request`: Task not completed yet
- `404 Not Found`: Task or output file not found

**Example:**
```bash
# Download to file
curl http://localhost:8000/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890/download \
  -o result.mp4

# Stream with wget
wget http://localhost:8000/tasks/a1b2c3d4-e5f6-7890-abcd-ef1234567890/download \
  -O result.mp4
```

**Python Example:**
```python
import requests

task_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
url = f"http://localhost:8000/tasks/{task_id}/download"

response = requests.get(url, stream=True)
if response.status_code == 200:
    with open("result.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete!")
else:
    print(f"Error: {response.json()}")
```

---

### Cleanup Single Task

Remove uploaded and output files for a specific task.

**Endpoint:** `POST /cleanup/{task_id}`

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `task_id` | string | UUID of the task to clean up |

**Response:**
```json
{
  "message": "Task a1b2c3d4-e5f6-7890-abcd-ef1234567890 cleaned up successfully"
}
```

**Status Codes:**
- `200 OK`: Cleanup successful
- `404 Not Found`: Task doesn't exist
- `500 Internal Server Error`: Cleanup failed

**Example:**
```bash
curl -X POST http://localhost:8000/cleanup/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Note:** This removes:
- Uploaded video file from `uploads/`
- Processed video file from `output/`
- Task tracking data

---

### Cleanup All Completed Tasks

Remove all completed and failed tasks to free disk space.

**Endpoint:** `DELETE /cleanup`

**Response:**
```json
{
  "message": "Cleanup completed",
  "removed_tasks": [
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "b2c3d4e5-f6g7-8901-bcde-fg2345678901"
  ],
  "count": 2
}
```

**Status Codes:**
- `200 OK`: Cleanup successful
- `500 Internal Server Error`: Cleanup failed

**Example:**
```bash
curl -X DELETE http://localhost:8000/cleanup
```

**Note:** Only removes tasks with status `completed` or `failed`. Active tasks (`pending`, `processing`) are preserved.

---

## Complete Workflow Example

### Bash Script
```bash
#!/bin/bash

API_URL="http://localhost:8000"

# 1. Submit video
echo "Uploading video..."
RESPONSE=$(curl -s -X POST "$API_URL/analyze" -F "file=@video.mp4")
TASK_ID=$(echo $RESPONSE | jq -r '.task_id')
echo "Task ID: $TASK_ID"

# 2. Poll for completion
echo "Waiting for processing..."
while true; do
    STATUS=$(curl -s "$API_URL/tasks/$TASK_ID" | jq -r '.status')
    echo "Status: $STATUS"
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        break
    fi
    
    sleep 5
done

# 3. Download result
if [ "$STATUS" = "completed" ]; then
    echo "Downloading result..."
    curl "$API_URL/tasks/$TASK_ID/download" -o "result_$TASK_ID.mp4"
    echo "Done! Result saved to result_$TASK_ID.mp4"
    
    # 4. Cleanup
    curl -X POST "$API_URL/cleanup/$TASK_ID"
else
    echo "Processing failed"
    curl "$API_URL/tasks/$TASK_ID"
fi
```

### Python Script
```python
import requests
import time
from pathlib import Path

API_URL = "http://localhost:8000"

def process_video(video_path: str, output_path: str = "result.mp4"):
    """Upload, process, and download a video."""
    
    # 1. Upload video
    print("Uploading video...")
    with open(video_path, "rb") as f:
        response = requests.post(f"{API_URL}/analyze", files={"file": f})
    
    data = response.json()
    task_id = data["task_id"]
    print(f"Task ID: {task_id}")
    
    # 2. Poll for completion
    print("Processing video...")
    while True:
        response = requests.get(f"{API_URL}/tasks/{task_id}")
        data = response.json()
        status = data["status"]
        
        print(f"Status: {status}")
        
        if status in ["completed", "failed"]:
            break
        
        time.sleep(5)
    
    # 3. Handle result
    if status == "completed":
        print(f"Processing complete!")
        print(f"Scenes detected: {data['stats']['num_scenes']}")
        print(f"Total duration: {data['stats']['total_scene_duration']:.1f}s")
        
        # Download result
        print("Downloading result...")
        response = requests.get(f"{API_URL}/tasks/{task_id}/download", stream=True)
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Saved to {output_path}")
        
        # Cleanup
        requests.post(f"{API_URL}/cleanup/{task_id}")
        print("Cleanup complete")
        
        return True
    else:
        print(f"Processing failed: {data['error_message']}")
        return False

# Usage
if __name__ == "__main__":
    process_video("input.mp4", "output.mp4")
```

### Node.js Script
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_URL = 'http://localhost:8000';

async function processVideo(videoPath, outputPath = 'result.mp4') {
  // 1. Upload video
  console.log('Uploading video...');
  const form = new FormData();
  form.append('file', fs.createReadStream(videoPath));
  
  const uploadResponse = await axios.post(`${API_URL}/analyze`, form, {
    headers: form.getHeaders()
  });
  
  const taskId = uploadResponse.data.task_id;
  console.log(`Task ID: ${taskId}`);
  
  // 2. Poll for completion
  console.log('Processing video...');
  let status;
  let data;
  
  while (true) {
    const statusResponse = await axios.get(`${API_URL}/tasks/${taskId}`);
    data = statusResponse.data;
    status = data.status;
    
    console.log(`Status: ${status}`);
    
    if (status === 'completed' || status === 'failed') {
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
  
  // 3. Handle result
  if (status === 'completed') {
    console.log('Processing complete!');
    console.log(`Scenes detected: ${data.stats.num_scenes}`);
    console.log(`Total duration: ${data.stats.total_scene_duration.toFixed(1)}s`);
    
    // Download result
    console.log('Downloading result...');
    const downloadResponse = await axios.get(
      `${API_URL}/tasks/${taskId}/download`,
      { responseType: 'stream' }
    );
    
    const writer = fs.createWriteStream(outputPath);
    downloadResponse.data.pipe(writer);
    
    await new Promise((resolve, reject) => {
      writer.on('finish', resolve);
      writer.on('error', reject);
    });
    
    console.log(`Saved to ${outputPath}`);
    
    // Cleanup
    await axios.post(`${API_URL}/cleanup/${taskId}`);
    console.log('Cleanup complete');
    
    return true;
  } else {
    console.log(`Processing failed: ${data.error_message}`);
    return false;
  }
}

// Usage
processVideo('input.mp4', 'output.mp4')
  .then(success => process.exit(success ? 0 : 1))
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
```

---

## Response Schemas

### TaskInfo Object
```json
{
  "task_id": "string (UUID)",
  "status": "pending | processing | completed | failed",
  "created_at": "string (ISO 8601 timestamp)",
  "started_at": "string (ISO 8601 timestamp) | null",
  "completed_at": "string (ISO 8601 timestamp) | null",
  "video_filename": "string",
  "output_file": "string (absolute path) | null",
  "error_message": "string | null",
  "stats": {
    "num_scenes": "integer",
    "total_scene_duration": "float (seconds)",
    "video_duration": "float (seconds)",
    "coverage_percentage": "float"
  } | null
}
```

### Stats Object
```json
{
  "num_scenes": 5,
  "total_scene_duration": 45.2,
  "video_duration": 180.0,
  "coverage_percentage": 25.11
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 400 | No filename provided | Ensure file upload includes filename |
| 400 | Task not completed | Wait for task to complete before downloading |
| 404 | Task not found | Verify task_id is correct |
| 404 | Output file not found | Task may have been cleaned up |
| 500 | Processing error | Check logs, may be invalid video format |

### Handling Failed Tasks

When a task fails, the response includes an `error_message`:

```json
{
  "task_id": "...",
  "status": "failed",
  "error_message": "Processing returned no output. No scenes detected.",
  ...
}
```

Common failure reasons:
- No scenes detected (video doesn't contain target content)
- Unsupported video format
- Corrupted video file
- Out of memory
- GPU/CUDA errors

---

## Rate Limiting

Currently no rate limiting. For production:
- Implement request rate limiting
- Add queue size limits
- Set maximum concurrent tasks
- Add file size limits

---

## Best Practices

### 1. Always Poll for Completion
```python
# Good: Poll with timeout
import time

timeout = 300  # 5 minutes
start_time = time.time()

while time.time() - start_time < timeout:
    response = requests.get(f"{API_URL}/tasks/{task_id}")
    status = response.json()["status"]
    
    if status in ["completed", "failed"]:
        break
    
    time.sleep(5)
```

### 2. Handle Errors Gracefully
```python
try:
    response = requests.get(f"{API_URL}/tasks/{task_id}/download")
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print("Task not ready yet")
    elif e.response.status_code == 404:
        print("Task or file not found")
    else:
        print(f"Error: {e}")
```

### 3. Clean Up After Processing
```python
# Always cleanup to free disk space
if status == "completed":
    # Download first
    download_result(task_id)
    # Then cleanup
    requests.post(f"{API_URL}/cleanup/{task_id}")
```

### 4. Monitor Disk Space
```bash
# Periodic cleanup script
curl -X DELETE http://localhost:8000/cleanup
```

### 5. Validate File Before Upload
```python
import os

def is_valid_video(path):
    # Check file exists
    if not os.path.exists(path):
        return False
    
    # Check file size (e.g., max 1GB)
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > 1024:
        return False
    
    # Check extension
    valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    ext = os.path.splitext(path)[1].lower()
    return ext in valid_extensions
```

---

## Interactive API Documentation

The API provides interactive documentation via Swagger UI:

**URL:** `http://localhost:8000/docs`

Features:
- Try endpoints directly from browser
- View request/response schemas
- See example values
- Test authentication (if configured)

Alternative ReDoc format:

**URL:** `http://localhost:8000/redoc`

---

## Deployment Considerations

### Production Checklist

- [ ] Add authentication (API keys, OAuth, JWT)
- [ ] Implement rate limiting
- [ ] Add request validation and sanitization
- [ ] Set up persistent task storage (Redis, database)
- [ ] Configure reverse proxy (nginx, traefik)
- [ ] Enable HTTPS/TLS
- [ ] Set file size limits
- [ ] Configure logging and monitoring
- [ ] Set up automated cleanup jobs
- [ ] Add health check monitoring
- [ ] Configure CORS for specific origins
- [ ] Set resource limits (CPU, memory, disk)

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Processing
MAX_FILE_SIZE_MB=1024
UPLOAD_DIR=/data/uploads
OUTPUT_DIR=/data/output

# Cleanup
AUTO_CLEANUP_HOURS=24
MAX_DISK_USAGE_GB=100

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn
```

### Docker Production Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
    volumes:
      - uploads:/app/uploads
      - output:/app/output
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  uploads:
  output:
```

---

## Support

For issues or questions:
- Check logs: `docker logs <container_name>`
- API logs: Available in container stdout
- Review error responses for specific details
- See main README.md for troubleshooting guide

---

**Last Updated:** January 3, 2026  
**API Version:** 1.0.0
