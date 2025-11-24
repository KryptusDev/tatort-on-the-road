import os
import logging
import time
import random
from app.analyzer import SceneAnalyzer
from app.video_processor import VideoProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    start_total = time.time()
    video_path = "testfiles/tatort3.mp4"
    if not os.path.exists(video_path):
        logging.error(f"File not found: {video_path}")
        return

    logging.info("Initializing Tatort on the Road...")
    
    try:
        analyzer = SceneAnalyzer()
        processor = VideoProcessor(video_path)
    except Exception as e:
        logging.error(f"Initialization failed: {e}")
        return

    # --- Pass 1: Coarse Scan ---
    start_coarse = time.time()
    logging.info("Starting Pass 1: Coarse Scan (every 5s)...")
    coarse_candidates = []
    step_coarse = 5.0
    threshold = 0.22 # Lowered for raw cosine similarity (CLIP raw scores are usually 0.2-0.3 for matches)
    
    current_time = 0.0
    while current_time < processor.duration:
        frame = processor.get_frame_at_time(current_time)
        if frame:
            pos_score, neg_score = analyzer.analyze_frame(frame)
            
            # Log every frame for debugging
            logging.info(f"Time: {current_time:6.1f}s | Pos: {pos_score:.4f} | Neg: {neg_score:.4f} | Delta: {pos_score - neg_score:.4f}")

            # Criteria: Positive score high enough AND Positive > Negative
            if pos_score > threshold and pos_score > neg_score:
                logging.info(f"  >>> CANDIDATE FOUND at {current_time:.1f}s")
                coarse_candidates.append(current_time)
        
        current_time += step_coarse
    
    duration_coarse = time.time() - start_coarse
    logging.info(f"Pass 1 Complete. Duration: {duration_coarse:.2f}s")

    if not coarse_candidates:
        logging.info("No scenes detected in coarse scan.")
        return

    # --- Pass 2: Fine Scan ---
    start_fine = time.time()
    logging.info("Starting Pass 2: Fine Scan (Refining boundaries)...")
    positive_frames = set()
    scanned_frames = set() # To prevent double scanning
    step_fine = 1.0
    buffer = 5.0 
    
    coarse_candidates.sort()
    num_candidates = len(coarse_candidates)

    for i, current_time in enumerate(coarse_candidates):
        # Check neighbors (assuming step_coarse is 5.0)
        # We use a small epsilon for float comparison
        has_left_neighbor = (i > 0 and abs(current_time - coarse_candidates[i-1] - step_coarse) < 0.1)
        has_right_neighbor = (i < num_candidates - 1 and abs(coarse_candidates[i+1] - current_time - step_coarse) < 0.1)

        # Optimization: If surrounded by candidates, everything is positive, no need to scan
        # (The neighbors will handle the filling of the gaps)
        if has_left_neighbor and has_right_neighbor:
            # Just ensure the intervals are marked (redundant but safe)
            # Actually, we can just skip, because the Left Neighbor handled [Left -> Curr]
            # and the Right Neighbor will handle [Curr -> Right] (when we iterate to it? No, Right Neighbor looks Left)
            # Let's be explicit to be safe:
            # Mark Left Interval [Curr-5, Curr] as positive
            start_t = int(current_time - buffer)
            end_t = int(current_time)
            for t in range(start_t, end_t):
                positive_frames.add(t)
            
            # Mark Right Interval [Curr, Curr+5] as positive
            start_t = int(current_time)
            end_t = int(current_time + buffer)
            for t in range(start_t, end_t):
                positive_frames.add(t)
            continue

        # --- Left Side Processing [Curr - 5, Curr] ---
        start_search = max(0, current_time - buffer)
        end_search = current_time
        
        if has_left_neighbor:
            # Auto-fill positive (Gap between Prev and Curr)
            t = start_search
            while t < end_search:
                positive_frames.add(int(t))
                t += step_fine
        else:
            # Scan (Edge case) - Batch Processing
            timestamps_to_scan = []
            t = start_search
            while t < end_search:
                t_int = int(t)
                if t_int not in scanned_frames:
                    timestamps_to_scan.append(t)
                t += step_fine
            
            if timestamps_to_scan:
                batch_size = 8
                for i in range(0, len(timestamps_to_scan), batch_size):
                    batch_times = timestamps_to_scan[i : i + batch_size]
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
                            if pos_score > threshold and pos_score > neg_score:
                                positive_frames.add(t_int)

        # --- Right Side Processing [Curr, Curr + 5] ---
        start_search = current_time
        end_search = min(processor.duration, current_time + buffer)
        
        if has_right_neighbor:
            # Auto-fill positive (Gap between Curr and Next)
            t = start_search
            while t < end_search:
                positive_frames.add(int(t))
                t += step_fine
        else:
            # Scan (Edge case) - Batch Processing
            timestamps_to_scan = []
            t = start_search
            while t < end_search:
                t_int = int(t)
                if t_int not in scanned_frames:
                    timestamps_to_scan.append(t)
                t += step_fine
            
            if timestamps_to_scan:
                batch_size = 8
                for i in range(0, len(timestamps_to_scan), batch_size):
                    batch_times = timestamps_to_scan[i : i + batch_size]
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
                            if pos_score > threshold and pos_score > neg_score:
                                positive_frames.add(t_int)

    duration_fine = time.time() - start_fine
    logging.info(f"Pass 2 Complete. Duration: {duration_fine:.2f}s")

    # --- Post-Processing: Grouping ---
    logging.info("Grouping scenes...")
    sorted_frames = sorted(list(positive_frames))
    if not sorted_frames:
        logging.info("No scenes confirmed after fine scan.")
        return

    scenes = []
    if sorted_frames:
        current_start = sorted_frames[0]
        current_end = sorted_frames[0]
        
        for f in sorted_frames[1:]:
            if f <= current_end + 2: # Allow 1-2 second gaps
                current_end = f
            else:
                scenes.append((current_start, current_end))
                current_start = f
                current_end = f
        scenes.append((current_start, current_end))

    # Filter short scenes
    final_scenes = [s for s in scenes if (s[1] - s[0]) >= 2]

    total_scene_duration = sum([end - start for start, end in final_scenes])
    total_video_duration = processor.duration
    percentage = (total_scene_duration / total_video_duration) * 100 if total_video_duration > 0 else 0

    logging.info("="*40)
    logging.info(f"STATISTICS:")
    logging.info(f"  - Total Scenes Found: {len(final_scenes)}")
    logging.info(f"  - Total Duration: {total_scene_duration:.2f}s")
    logging.info(f"  - Video Coverage: {percentage:.2f}%")
    logging.info("="*40)

    logging.info(f"Found {len(final_scenes)} target scenes:")
    for start, end in final_scenes:
        logging.info(f"  - {start}s to {end}s (Duration: {end-start}s)")

    # --- Video Generation ---
    start_video = time.time()
    from app.video_editor import VideoEditor
    output_file = f"output/result{random.randint(1, 100)}.mp4"
    editor = VideoEditor(video_path, output_file)
    try:
        editor.create_summary_video(final_scenes)
    except Exception as e:
        logging.error(f"Failed to create video: {e}")
    
    duration_video = time.time() - start_video
    logging.info(f"Video Generation Complete. Duration: {duration_video:.2f}s")

    processor.close()
    
    duration_total = time.time() - start_total
    logging.info(f"Finished. Total Execution Time: {duration_total:.2f}s")

if __name__ == "__main__":
    main()
