"""
Shared video processing workflow module.
Extracts common scene detection and video generation logic.
"""
import logging
import os
import time

from app.analyzer import SceneAnalyzer
from app.video_editor import VideoEditor
from app.video_processor import VideoProcessor

# Constants
STEP_COARSE = 5.0
STEP_FINE = 1.0
BUFFER = 5.0
THRESHOLD = 0.22
BATCH_SIZE = 8
MIN_SCENE_DURATION = 2.0
MIN_GAP_THRESHOLD = 2.0


def process_video(video_path: str, output_dir: str = "output") -> tuple:
    """
    Process a video to extract driving scenes.
    
    Returns:
        tuple: (output_video_path, stats_dict) or (None, None) if processing failed
    """
    if not os.path.exists(video_path):
        logging.error(f"File not found: {video_path}")
        return None, None

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logging.info(f"Initializing Tatort on the Road for file: {video_path}")

    try:
        analyzer = SceneAnalyzer()
        processor = VideoProcessor(video_path)
    except Exception as e:
        logging.error(f"Initialization failed: {e}")
        return None, None

    # Pass 1: Coarse Scan
    coarse_candidates = _coarse_scan(analyzer, processor)

    if not coarse_candidates:
        logging.info("No scenes detected in coarse scan.")
        processor.close()
        return None, None

    # Pass 2: Fine Scan
    positive_frames = _fine_scan(analyzer, processor, coarse_candidates)

    # Post-Processing: Grouping
    final_scenes = _group_scenes(positive_frames)

    if not final_scenes:
        logging.info("No scenes confirmed after fine scan.")
        processor.close()
        return None, None

    # Calculate statistics
    stats = _calculate_stats(final_scenes, processor.duration)
    _log_statistics(stats, final_scenes)

    # Video Generation
    output_file = _generate_output_video(video_path, output_dir, final_scenes, processor)

    processor.close()

    return output_file, stats


def _coarse_scan(analyzer: SceneAnalyzer, processor: VideoProcessor) -> list:
    """Perform coarse scan at 5-second intervals."""
    start_time = time.time()
    logging.info("Starting Pass 1: Coarse Scan (every 5s)...")

    coarse_candidates = []
    current_time = 0.0

    while current_time < processor.duration:
        frame = processor.get_frame_at_time(current_time)
        if frame:
            pos_score, neg_score = analyzer.analyze_frame(frame)
            logging.info(
                f"Time: {current_time:6.1f}s | Pos: {pos_score:.4f} | Neg: {neg_score:.4f} | Delta: {pos_score - neg_score:.4f}"
            )

            if pos_score > THRESHOLD and pos_score > neg_score:
                logging.info(f"  >>> CANDIDATE FOUND at {current_time:.1f}s")
                coarse_candidates.append(current_time)

        current_time += STEP_COARSE

    duration = time.time() - start_time
    logging.info(f"Pass 1 Complete. Duration: {duration:.2f}s")

    return coarse_candidates


def _fine_scan(
    analyzer: SceneAnalyzer,
    processor: VideoProcessor,
    coarse_candidates: list,
) -> set:
    """Perform fine scan with 1-second intervals to refine boundaries."""
    start_time = time.time()
    logging.info("Starting Pass 2: Fine Scan (Refining boundaries)...")

    positive_frames = set()
    scanned_frames = set()
    coarse_candidates.sort()
    num_candidates = len(coarse_candidates)

    for i, current_time in enumerate(coarse_candidates):
        has_left_neighbor = (
            i > 0
            and abs(current_time - coarse_candidates[i - 1] - STEP_COARSE) < 0.1
        )
        has_right_neighbor = (
            i < num_candidates - 1
            and abs(coarse_candidates[i + 1] - current_time - STEP_COARSE) < 0.1
        )

        # If surrounded by candidates, auto-fill
        if has_left_neighbor and has_right_neighbor:
            for t in range(int(current_time - BUFFER), int(current_time + BUFFER)):
                positive_frames.add(t)
            continue

        # Left Side: [Curr - 5, Curr]
        _scan_side(
            analyzer,
            processor,
            max(0, current_time - BUFFER),
            current_time,
            has_left_neighbor,
            positive_frames,
            scanned_frames,
        )

        # Right Side: [Curr, Curr + 5]
        _scan_side(
            analyzer,
            processor,
            current_time,
            min(processor.duration, current_time + BUFFER),
            has_right_neighbor,
            positive_frames,
            scanned_frames,
        )

    duration = time.time() - start_time
    logging.info(f"Pass 2 Complete. Duration: {duration:.2f}s")

    return positive_frames


def _scan_side(
    analyzer: SceneAnalyzer,
    processor: VideoProcessor,
    start_search: float,
    end_search: float,
    has_neighbor: bool,
    positive_frames: set,
    scanned_frames: set,
) -> None:
    """Scan a time range and update positive frames."""
    if has_neighbor:
        # Auto-fill if neighbor exists
        t = start_search
        while t < end_search:
            positive_frames.add(int(t))
            t += STEP_FINE
    else:
        # Scan with batch processing
        timestamps_to_scan = []
        t = start_search
        while t < end_search:
            t_int = int(t)
            if t_int not in scanned_frames:
                timestamps_to_scan.append(t)
            t += STEP_FINE

        if timestamps_to_scan:
            for i in range(0, len(timestamps_to_scan), BATCH_SIZE):
                batch_times = timestamps_to_scan[i : i + BATCH_SIZE]
                frames = []
                valid_times = []

                for bt in batch_times:
                    frame = processor.get_frame_at_time(bt)
                    if frame:
                        frames.append(frame)
                        valid_times.append(bt)

                if frames:
                    results = analyzer.analyze_batch(frames)
                    for j, (pos_score, neg_score) in enumerate(results):
                        t_int = int(valid_times[j])
                        scanned_frames.add(t_int)
                        if pos_score > THRESHOLD and pos_score > neg_score:
                            positive_frames.add(t_int)


def _group_scenes(positive_frames: set) -> list:
    """Group consecutive positive frames into scenes."""
    sorted_frames = sorted(list(positive_frames))

    if not sorted_frames:
        return []

    scenes = []
    current_start = sorted_frames[0]
    current_end = sorted_frames[0]

    for f in sorted_frames[1:]:
        if f <= current_end + MIN_GAP_THRESHOLD:
            current_end = f
        else:
            scenes.append((current_start, current_end))
            current_start = f
            current_end = f

    scenes.append((current_start, current_end))

    # Filter short scenes
    final_scenes = [s for s in scenes if (s[1] - s[0]) >= MIN_SCENE_DURATION]

    return final_scenes


def _calculate_stats(scenes: list, total_duration: float) -> dict:
    """Calculate statistics about the detected scenes."""
    total_scene_duration = sum(end - start for start, end in scenes)
    percentage = (total_scene_duration / total_duration) * 100 if total_duration > 0 else 0

    return {
        "num_scenes": len(scenes),
        "total_duration": total_scene_duration,
        "percentage": percentage,
    }


def _log_statistics(stats: dict, scenes: list) -> None:
    """Log scene detection statistics."""
    logging.info("=" * 40)
    logging.info("STATISTICS:")
    logging.info(f"  - Total Scenes Found: {stats['num_scenes']}")
    logging.info(f"  - Total Duration: {stats['total_duration']:.2f}s")
    logging.info(f"  - Video Coverage: {stats['percentage']:.2f}%")
    logging.info("=" * 40)

    logging.info(f"Found {stats['num_scenes']} target scenes:")
    for start, end in scenes:
        logging.info(f"  - {start}s to {end}s (Duration: {end - start}s)")


def _generate_output_video(
    video_path: str, output_dir: str, scenes: list, processor: VideoProcessor
) -> str:
    """Generate the output summary video."""
    start_time = time.time()

    output_filename = f"result_{os.path.basename(video_path).rsplit('.', 1)[0]}_{int(time.time())}.mp4"
    output_file = os.path.join(output_dir, output_filename)

    editor = VideoEditor(video_path, output_file)
    try:
        editor.create_summary_video(scenes)
    except Exception as e:
        logging.error(f"Failed to create video: {e}")
        return None

    duration = time.time() - start_time
    logging.info(f"Video Generation Complete. Duration: {duration:.2f}s")

    return output_file


def get_stats_text(stats: dict) -> str:
    """Format statistics as text for posting."""
    return (
        f"Scenes Found: {stats['num_scenes']}\n"
        f"Total Duration: {stats['total_duration']:.2f}s\n"
        f"Video Coverage: {stats['percentage']:.2f}%"
    )
