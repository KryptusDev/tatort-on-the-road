# Tatort on the Road

AI-powered car scene extraction for video analysis. Automatically identifies and extracts driving scenes from videos using CLIP (Contrastive Language-Image Pre-training) for intelligent scene detection.

## Features

- 🎯 **Intelligent Scene Detection**: CLIP-based AI identifies driving scenes with high accuracy
- 🔄 **Two-Pass Analysis**: Coarse scan (5s) + fine scan (1s) for precise scene boundaries
- ⚡ **Batch Processing**: Optimized GPU inference for fast processing
- 🎬 **Video Summary Generation**: Creates highlight reels from detected scenes
- 🌐 **REST API**: FastAPI server with async task processing
- 📊 **Detailed Statistics**: Scene count, duration, and coverage metrics

## Quick Start

### With Dev Container (Recommended)

If you're in a dev container, the API is ready to start:

```bash
bash start-api.sh
```

The API will be available at `http://localhost:8000`

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python -m app.api_server

# Or use the CLI directly
python -m app.main testfiles/video.mp4 --output-dir output
```

### Docker

```bash
# Build and start the API server
docker-compose up --build

# Or process a video directly
docker-compose run --rm tatort-app python -m app.main testfiles/video.mp4
```

## Usage

### REST API

The API server provides asynchronous video processing. See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed endpoint documentation.

**Quick Example:**

```bash
# Check API health
curl http://localhost:8000/health

# Submit video for analysis
curl -X POST http://localhost:8000/analyze \
  -F "file=@video.mp4"

# Check task status
curl http://localhost:8000/tasks/{task_id}

# Download processed video
curl http://localhost:8000/tasks/{task_id}/download -o result.mp4
```

### Command Line Interface

Process videos directly from the command line:

```bash
python -m app.main <video_path> [--output-dir <directory>]
```

**Examples:**

```bash
# Basic usage
python -m app.main testfiles/sample.mp4

# Custom output directory
python -m app.main video.mp4 --output-dir /path/to/output

# Docker
docker-compose run --rm tatort-app python -m app.main testfiles/video.mp4
```

## How It Works

### 1. Coarse Scan (Pass 1)
- Samples frames every 5 seconds
- CLIP model scores each frame against driving scene prompts
- Identifies candidate time ranges

### 2. Fine Scan (Pass 2)
- Refines boundaries with 1-second intervals
- Batch processes frames for efficiency
- Groups adjacent positive frames into scenes

### 3. Post-Processing
- Filters scenes shorter than 2 seconds
- Merges scenes with small gaps (<2s)
- Generates comprehensive statistics

### 4. Output Generation
- Creates summary video with all detected scenes
- Preserves original quality and audio
- Outputs: scene count, total duration, coverage percentage

## Requirements

- **Python**: 3.10 or higher
- **GPU**: CUDA-capable GPU (optional, falls back to CPU)
- **Disk Space**: ~2-3x the source video size for processing
- **Docker**: Optional, for containerized deployment

## Configuration

Adjust detection parameters in [app/processor_workflow.py](app/processor_workflow.py):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `THRESHOLD` | 0.22 | CLIP score threshold for scene detection |
| `STEP_COARSE` | 5.0s | Coarse scan interval |
| `STEP_FINE` | 1.0s | Fine scan interval |
| `BATCH_SIZE` | 8 | Frames per batch for parallel processing |
| `MIN_SCENE_DURATION` | 2.0s | Minimum scene length |

## Project Structure

```
tatort-on-the-road/
├── app/
│   ├── __init__.py
│   ├── api_server.py         # FastAPI REST API
│   ├── analyzer.py           # CLIP-based scene analyzer
│   ├── main.py               # CLI entry point
│   ├── processor_workflow.py # Processing pipeline
│   ├── video_processor.py    # Frame extraction
│   └── video_editor.py       # Video composition
├── testfiles/                # Sample videos
├── output/                   # Processed videos
├── uploads/                  # API upload directory
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-container setup
├── start-api.sh             # API startup script
└── README.md                # This file
```

## Output

### CLI Mode
- `result_<filename>_<timestamp>.mp4` - Summary video with all scenes
- Console statistics: scene count, duration, coverage

### API Mode
- Async task tracking with status updates
- Downloadable result videos via `/tasks/{task_id}/download`
- JSON response with detailed statistics

## Performance

- **Model Loading**: ~5-10 seconds (first run only)
- **Processing Speed**: 
  - Coarse scan: ~10-15 FPS
  - Fine scan: ~5-10 FPS
- **Total Time**: Depends on video length and scene complexity
  - 5-min video: ~2-5 minutes
  - 30-min video: ~15-30 minutes

**GPU vs CPU**: GPU processing is 3-5x faster than CPU

## API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for:
- Complete endpoint reference
- Request/response schemas
- Integration examples
- Error handling
- Task lifecycle management

## Troubleshooting

**API won't start**: Check if port 8000 is available: `lsof -i :8000`

**Out of memory**: Reduce `BATCH_SIZE` in [app/processor_workflow.py](app/processor_workflow.py)

**No scenes detected**: Lower `THRESHOLD` value (try 0.18-0.20)

**Slow processing**: Ensure GPU is available and CUDA is properly installed

**Docker issues**: Check logs with `docker-compose logs -f`

## Development

```bash
# Install in development mode
pip install -e .

# Run tests (if available)
pytest

# Format code
black app/

# Type checking
mypy app/
```

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

