from app.bot import request_confirmation
import os
import logging
from dotenv import load_dotenv

# Load env vars
load_dotenv()

logging.basicConfig(level=logging.INFO)

def test_bot():
    # Create a dummy video file
    dummy_video = "test_bot_video.mp4"
    # Make it a valid mp4 container if possible, or just text. 
    # Telegram might reject invalid video.
    # Let's try to use the downloaded one if available, or a small valid mp4.
    # Or just a text file renamed to mp4 (might fail upload).
    
    # Create a dummy video file for testing (to avoid 50MB Telegram limit)
    dummy_video = "test_bot_video.mp4"
    
    # Create a small valid mp4 or just text (Telegram might reject text as video, but let's try)
    # Actually, let's just use a tiny text file but name it mp4. 
    # If Telegram validates headers, this might fail. 
    # But usually for a bot test, we just want to see if the message sends.
    # To be safe, let's try to find a small mp4 or just send a text message if video fails?
    # No, let's just write a few bytes.
    
    with open(dummy_video, "wb") as f:
        f.write(b"dummy video content")
        
    video_path = dummy_video
    print(f"Testing with dummy video: {video_path}")
    
    result = request_confirmation(video_path, "Test Stats: 10 scenes, 5 minutes.")
    print(f"User Decision: {result}")

    if video_path == dummy_video:
        os.remove(dummy_video)

if __name__ == "__main__":
    test_bot()
