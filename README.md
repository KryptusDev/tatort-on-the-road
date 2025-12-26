# Tatort on the Road

Automated scene extraction for Tatort episodes using AI-powered video analysis.

## Features

- **Intelligent Scene Detection**: Uses CLIP (Contrastive Language-Image Pre-training) to identify driving scenes
- **Two-Pass Analysis**: Coarse scan (5s intervals) followed by fine scan (1s intervals) for precise boundaries
- **Batch Processing**: Optimized frame processing with batch inference for faster analysis
- **Video Summary Generation**: Creates a concise summary video containing only the detected scenes

## Requirements

- Python 3.10+
- CUDA-capable GPU (optional, will fall back to CPU)
- Docker & Docker Compose (for containerized deployment)

## Installation

### Local Setup

```bash
pip install -r requirements.txt
```

### Docker Setup

```bash
docker-compose build
```

## Usage

### Command Line

Process a single video file and extract driving scenes:

```bash
python -m app.main <input_video_path> [--output-dir <output_directory>]
```

**Arguments:**
- `input_video_path`: Path to the video file to process (e.g., `testfiles/video.mp4`)
- `--output-dir`: (Optional) Directory for output files. Defaults to `output/`

**Example:**

```bash
python -m app.main testfiles/sample.mp4 --output-dir output
```

### Docker

```bash
docker-compose run --rm tatort-app python -m app.main testfiles/video.mp4 --output-dir output
```

## How It Works

### Pass 1: Coarse Scan
- Samples frames at 5-second intervals
- Uses CLIP to score each frame against positive prompts (driving scenes) and negative prompts (non-driving scenes)
- Identifies candidate time ranges containing target scenes

### Pass 2: Fine Scan
- Refines boundaries with 1-second interval sampling
- Uses batch processing for efficiency
- Groups adjacent positive frames into complete scenes

### Post-Processing
- Filters out short scenes (< 2 seconds)
- Handles small gaps between scenes (< 2 seconds)
- Generates statistics about detected content

### Output Generation
- Creates a summary video concatenating all detected scenes
- Preserves original audio and video quality
- Outputs statistics: number of scenes, total duration, video coverage percentage

## Directory Structure

```
├── app/
│   ├── __init__.py
│   ├── analyzer.py           # CLIP-based scene analyzer
│   ├── main.py               # CLI entry point
│   ├── processor_workflow.py  # Shared processing logic
│   ├── video_processor.py     # Video frame extraction
│   └── video_editor.py        # Video composition & export
├── testfiles/                # Sample video files for testing
├── output/                   # Output directory for processed videos
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── docker-compose.yml       # Docker Compose configuration
```

## Output

For each processed video, you'll get:
- **Summary Video**: `result_<filename>_<timestamp>.mp4` - Concatenated driving scenes
- **Console Logs**: Statistics about detected scenes (number, total duration, coverage percentage)

## Performance Notes

- GPU processing significantly speeds up CLIP inference
- Initial model loading takes ~5-10 seconds (one-time per run)
- Processing speed: ~10-15 FPS for coarse scan, ~5-10 FPS for fine scan
- Total processing time depends on video length and number of detected scenes

## Configuration

Tuning parameters can be adjusted in `app/processor_workflow.py`:
- `THRESHOLD`: CLIP score threshold for scene detection (default: 0.22)
- `STEP_COARSE`: Coarse scan interval in seconds (default: 5.0)
- `STEP_FINE`: Fine scan interval in seconds (default: 1.0)
- `BATCH_SIZE`: Number of frames to process in parallel (default: 8)
- `MIN_SCENE_DURATION`: Minimum scene length in seconds (default: 2.0)

## Limitations

- Works best with content that matches the trained positive/negative prompts
- Requires sufficient disk space for processing (plan for 2-3x source video size during processing)
- Best results with 720p or higher resolution videos

