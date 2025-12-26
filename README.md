# Tatort on the Road

Automated scene extraction for Tatort episodes.

## Features

- **Automated Weekly Job**: Scrapes, downloads, processes, and extracts driving scenes from the latest Tatort episode every Sunday.
- **Manual Scene Extraction**: Manually process any video file to extract target scenes.

## Usage

### Automated Mode
The scheduler runs automatically when the container starts.

```bash
docker-compose up -d
```

### Manual Scene Extraction

You can verify or process specific files using `docker exec` on a running container.

**Prerequisites:**
- The input file must be available inside the container. You can mount a local directory to `/app/testfiles` or any other path.
- By default, `docker-compose.yml` mounts:
    - `./testfiles` -> `/app/testfiles`
    - `./output` -> `/app/output`

**Command:**

```bash
# General syntax
docker exec -it <container_name> python -m app.main <input_file_path> [--output-dir <output_path>]

# Example (assuming tatort-app is the service name/container prefix)
docker exec -it tatort-on-the-road-tatort-app-1 python -m app.main testfiles/myvideo.mp4 --output-dir output/custom_job
```

**Arguments:**
- `input_path`: Path to the video file INSIDE the container (e.g., `testfiles/video.mp4`).
- `--output-dir`: (Optional) Directory where the result and logs will be saved. Defaults to `output/`.
