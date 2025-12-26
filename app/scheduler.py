import schedule
import time
import logging
import os
from app.scraper import find_latest_episode
from app.downloader import download_video
from app.bot import request_confirmation
from app.poster import post_to_all
# We need to import the processing logic. 
# Since main.py has it in main(), we should refactor main.py or import the classes.
# The user asked to "extend this app", so we can reuse the classes.
from app.analyzer import SceneAnalyzer
from app.video_processor import VideoProcessor
from app.video_editor import VideoEditor
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_video_workflow(video_path):
    """
    Runs the video processing logic (Analyzer -> Processor -> Editor).
    Returns path to output video and stats text.
    """
    logging.info(f"Processing video: {video_path}")
    
    try:
        analyzer = SceneAnalyzer()
        processor = VideoProcessor(video_path)
    except Exception as e:
        logging.error(f"Initialization failed: {e}")
        return None, None

    # --- Pass 1: Coarse Scan ---
    logging.info("Starting Pass 1: Coarse Scan...")
    coarse_candidates = []
    step_coarse = 5.0
    threshold = 0.22
    
    current_time = 0.0
    while current_time < processor.duration:
        frame = processor.get_frame_at_time(current_time)
        if frame:
            pos_score, neg_score = analyzer.analyze_frame(frame)
            if pos_score > threshold and pos_score > neg_score:
                coarse_candidates.append(current_time)
        current_time += step_coarse
    
    if not coarse_candidates:
        logging.info("No scenes detected.")
        return None, None

    # --- Pass 2: Fine Scan ---
    logging.info("Starting Pass 2: Fine Scan...")
    positive_frames = set()
    scanned_frames = set()
    step_fine = 1.0
    buffer = 5.0 
    
    coarse_candidates.sort()
    num_candidates = len(coarse_candidates)

    for i, current_time in enumerate(coarse_candidates):
        has_left_neighbor = (i > 0 and abs(current_time - coarse_candidates[i-1] - step_coarse) < 0.1)
        has_right_neighbor = (i < num_candidates - 1 and abs(coarse_candidates[i+1] - current_time - step_coarse) < 0.1)

        if has_left_neighbor and has_right_neighbor:
            start_t = int(current_time - buffer)
            end_t = int(current_time + buffer)
            for t in range(start_t, end_t):
                positive_frames.add(t)
            continue

        # Left Side
        start_search = max(0, current_time - buffer)
        end_search = current_time
        if has_left_neighbor:
            t = start_search
            while t < end_search:
                positive_frames.add(int(t))
                t += step_fine
        else:
            t = start_search
            while t < end_search:
                t_int = int(t)
                if t_int not in scanned_frames:
                    frame = processor.get_frame_at_time(t)
                    if frame:
                        pos, neg = analyzer.analyze_frame(frame)
                        scanned_frames.add(t_int)
                        if pos > threshold and pos > neg:
                            positive_frames.add(t_int)
                t += step_fine

        # Right Side
        start_search = current_time
        end_search = min(processor.duration, current_time + buffer)
        if has_right_neighbor:
            t = start_search
            while t < end_search:
                positive_frames.add(int(t))
                t += step_fine
        else:
            t = start_search
            while t < end_search:
                t_int = int(t)
                if t_int not in scanned_frames:
                    frame = processor.get_frame_at_time(t)
                    if frame:
                        pos, neg = analyzer.analyze_frame(frame)
                        scanned_frames.add(t_int)
                        if pos > threshold and pos > neg:
                            positive_frames.add(t_int)
                t += step_fine

    # --- Grouping ---
    sorted_frames = sorted(list(positive_frames))
    if not sorted_frames:
        return None, None

    scenes = []
    current_start = sorted_frames[0]
    current_end = sorted_frames[0]
    
    for f in sorted_frames[1:]:
        if f <= current_end + 2:
            current_end = f
        else:
            scenes.append((current_start, current_end))
            current_start = f
            current_end = f
    scenes.append((current_start, current_end))

    final_scenes = [s for s in scenes if (s[1] - s[0]) >= 2]
    
    total_duration = sum([end - start for start, end in final_scenes])
    percentage = (total_duration / processor.duration) * 100 if processor.duration > 0 else 0
    
    stats_text = (
        f"Scenes Found: {len(final_scenes)}\n"
        f"Total Duration: {total_duration:.2f}s\n"
        f"Video Coverage: {percentage:.2f}%"
    )
    
    # --- Video Generation ---
    if not os.path.exists("output"):
        os.makedirs("output")
        
    output_file = f"output/tatort_summary_{int(time.time())}.mp4"
    editor = VideoEditor(video_path, output_file)
    try:
        editor.create_summary_video(final_scenes)
    except Exception as e:
        logging.error(f"Failed to create video: {e}")
        return None, None
        
    processor.close()
    return output_file, stats_text

def job():
    logging.info("Starting weekly Tatort job...")
    
    # 1. Scrape
    episode = find_latest_episode()
    if not episode:
        logging.error("No episode found.")
        return
        
    logging.info(f"Processing Episode: {episode['title']}")
    
    # 2. Download
    video_path = download_video(episode['url'], output_dir="downloads")
    if not video_path:
        logging.error("Download failed.")
        return
        
    # 3. Process
    output_video, stats = process_video_workflow(video_path)
    if not output_video:
        logging.error("Processing failed or no scenes found.")
        return
        
    # 4. Confirm
    confirmed = request_confirmation(output_video, stats)
    
    # 5. Post
    if confirmed:
        post_text = f"New Tatort Scene Extraction!\n\nEpisode: {episode['title']}\n{stats}\n\n#Tatort #AI"
        post_to_all(output_video, post_text)
    else:
        logging.info("Posting cancelled by user.")
        
    # Cleanup?
    # os.remove(video_path)
    # os.remove(output_video)

def start_scheduler():
    # Schedule: Sunday 9:45p CET (21:45)
    # Note: Server time might be UTC. User said CET.
    # If system time is correct (as per metadata), we can just use local time.
    schedule.every().sunday.at("21:45").do(job)
    
    logging.info("Scheduler started. Waiting for next job...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # For testing, we can run job() directly
    # job()
    start_scheduler()
