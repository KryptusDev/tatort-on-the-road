import argparse
import logging
import time

from app.processor_workflow import process_video

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="Tatort on the Road - Scene Extractor")
    parser.add_argument("input_path", help="Path to the input video file")
    parser.add_argument("--output-dir", default="output", help="Directory for output files")
    
    args = parser.parse_args()
    
    start_total = time.time()
    
    output_file, stats = process_video(args.input_path, args.output_dir)
    
    if output_file:
        logging.info(f"Output saved to: {output_file}")
    else:
        logging.error("Processing failed or no scenes found.")
    
    duration_total = time.time() - start_total
    logging.info(f"Finished. Total Execution Time: {duration_total:.2f}s")

if __name__ == "__main__":
    main()
