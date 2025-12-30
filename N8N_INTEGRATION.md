# n8n Integration Guide for Tatort on the Road API

## Quick Start

### 1. Running the API Locally (for testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python -m uvicorn app.api_server:app --host 0.0.0.0 --port 8000

# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 2. Running with Docker Compose (for production)

```bash
# Make sure the n8n_net network exists
docker network create n8n_net

# Build and start the service
docker-compose up -d

# The API will be available at http://tatort-api:8000 (within docker network)
# Or http://localhost:8000 from the host
```

## API Endpoints

### Health Check
- **GET** `/health` - Check if the API is running
- **Response:** `{"status": "healthy", "service": "Tatort on the Road API"}`

### Submit Video for Analysis
- **POST** `/analyze` - Upload a video file for scene extraction
- **Parameters:** 
  - `file` (multipart/form-data): The video file to analyze
- **Response:**
  ```json
  {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "message": "Video submitted for analysis. Check status with /tasks/{task_id}"
  }
  ```

### Get Task Status
- **GET** `/tasks/{task_id}` - Get the current status of a task
- **Response:**
  ```json
  {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "created_at": "2025-12-29T10:00:00.000000",
    "started_at": "2025-12-29T10:00:05.000000",
    "completed_at": "2025-12-29T10:05:30.000000",
    "video_filename": "input.mp4",
    "output_file": "/workspace/output/output_550e8400.mp4",
    "error_message": null,
    "stats": {
      "total_scenes": 5,
      "total_duration": 125.5,
      ...
    }
  }
  ```

### List All Tasks
- **GET** `/tasks?status=completed` - List tasks (optionally filter by status)
- **Query Parameters:**
  - `status` (optional): Filter by status (pending, processing, completed, failed)

### Download Result Video
- **GET** `/tasks/{task_id}/download` - Download the processed video
- **Response:** Binary video file

### Cleanup Task Files
- **POST** `/cleanup/{task_id}` - Delete uploaded and output files for a specific task
- **DELETE** `/cleanup` - Delete all completed and failed tasks

## n8n Workflow Examples

### Example 1: Simple Video Analysis Workflow

```
Trigger (Webhook or Manual) 
  ↓
Upload File to Tatort API (HTTP Request)
  ↓
Wait/Poll for Status (Loop with HTTP Request)
  ↓
Download Result (HTTP Request)
  ↓
Send Result via Email (Send Email)
```

### Example 2: n8n HTTP Request Node Configuration

#### Submit Video for Analysis
```
Node Type: HTTP Request
Method: POST
URL: http://tatort-api:8000/analyze
Authentication: None
Headers: (leave default)
Body type: Form Data
- Key: "file"
- Value type: File
- Value: [Select from previous node or upload]
```

#### Check Task Status
```
Node Type: HTTP Request
Method: GET
URL: http://tatort-api:8000/tasks/{{ $json.body.task_id }}
Authentication: None
Send Query Parameters: false
```

#### Download Result
```
Node Type: HTTP Request
Method: GET
URL: http://tatort-api:8000/tasks/{{ $json.body.task_id }}/download
Authentication: None
Response Format: File
```

### Example 3: Polling for Task Completion

```json
{
  "nodes": [
    {
      "parameters": {
        "method": "POST",
        "url": "http://tatort-api:8000/analyze",
        "body": {
          "file": "{{ $node.FileInput.data }}"
        }
      },
      "name": "Submit Video"
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://tatort-api:8000/tasks/{{ $node.SubmitVideo.json.task_id }}"
      },
      "name": "Check Status"
    },
    {
      "parameters": {
        "loopExpression": "{{ $node.CheckStatus.json.status === 'completed' }}"
      },
      "name": "Wait for Completion"
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://tatort-api:8000/tasks/{{ $node.SubmitVideo.json.task_id }}/download",
        "responseFormat": "file"
      },
      "name": "Download Result"
    }
  ]
}
```

## Docker Network Setup

### Create the n8n network (if it doesn't exist)
```bash
docker network create n8n_net
```

### Connect to existing n8n setup
The `docker-compose.yml` is configured to use an external network `n8n_net`. When running both n8n and Tatort API as services, they can communicate using service names:

- **From n8n to Tatort API:** `http://tatort-api:8000`
- **From host machine:** `http://localhost:8000`

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/

# Submit a video
curl -X POST -F "file=@/path/to/video.mp4" http://localhost:8000/analyze

# Check task status
curl http://localhost:8000/tasks/{task_id}

# List all tasks
curl http://localhost:8000/tasks

# Download result
curl http://localhost:8000/tasks/{task_id}/download -o result.mp4
```

### Using n8n Test Node
1. Create an HTTP Request node in n8n
2. Set Method: POST
3. Set URL: `http://tatort-api:8000/analyze` (or `http://localhost:8000/analyze` if testing locally)
4. Set Body to Form Data with file parameter
5. Click Test

## Troubleshooting

### API not accessible from n8n
- Make sure both services are on the same Docker network (`n8n_net`)
- Verify the network exists: `docker network ls`
- Use service name (tatort-api) instead of localhost when calling from n8n container

### Task stays in "processing" status
- Check API logs: `docker logs tatort-on-the-road-api`
- Long videos may take several minutes to process
- Check available GPU memory if using CUDA

### Out of memory errors
- The app uses significant GPU/CPU memory
- Reduce batch size in `app/processor_workflow.py` if needed
- Ensure sufficient disk space for uploads and output

## Environment Variables (for advanced configuration)

In docker-compose.yml, you can add environment variables:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - UPLOAD_DIR=/workspace/uploads
  - OUTPUT_DIR=/workspace/output
  - LOG_LEVEL=INFO
```

## Production Deployment Tips

1. **Use environment variables** for paths and configuration
2. **Enable authentication** in the API (add API key validation)
3. **Use Redis** for persistent task tracking instead of in-memory storage
4. **Add request size limits** to prevent abuse
5. **Monitor disk space** for uploads and output files
6. **Implement cleanup policies** for old files
7. **Use load balancing** if running multiple instances
8. **Enable logging** to centralized system (ELK, Loki, etc.)

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Test API locally: `python -m uvicorn app.api_server:app --reload`
3. Create first n8n workflow with HTTP Request node
4. Deploy with Docker when ready for production
