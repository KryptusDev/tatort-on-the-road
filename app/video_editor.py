import ffmpeg
import logging
import os

class VideoEditor:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        
    def create_summary_video(self, scenes):
        """
        scenes: List of (start, end) tuples in seconds.
        """
        if not scenes:
            logging.warning("No scenes to process.")
            return

        logging.info(f"Processing {len(scenes)} scenes into {self.output_path}...")
        
        input_stream = ffmpeg.input(self.input_path)
        streams = []
        
        for start, end in scenes:
            # Trim video
            v = input_stream.video.trim(start=start, end=end).setpts('PTS-STARTPTS')
            # Trim audio
            a = input_stream.audio.filter_('atrim', start=start, end=end).filter_('asetpts', 'PTS-STARTPTS')
            streams.append(v)
            streams.append(a)
            
        # Concat all streams
        # interleave=1 ensures audio and video are correctly multiplexed
        joined = ffmpeg.concat(*streams, v=1, a=1).node
        
        # Output
        output = ffmpeg.output(joined[0], joined[1], self.output_path)
        
        try:
            output.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            logging.info(f"Video saved to {self.output_path}")
        except ffmpeg.Error as e:
            logging.error(f"FFmpeg error: {e.stderr.decode('utf8')}")
            raise

