from unittest.mock import patch, MagicMock
import app.scheduler
from app.scheduler import job
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

@patch('app.scheduler.find_latest_episode')
@patch('app.scheduler.download_video')
@patch('app.scheduler.process_video_workflow')
@patch('app.scheduler.request_confirmation')
@patch('app.scheduler.post_to_all')
def test_scheduler_job(mock_post, mock_confirm, mock_process, mock_download, mock_scrape):
    print("Testing Scheduler Job (Mocked)...")
    
    # Setup mocks
    mock_scrape.return_value = {
        'title': 'Test Episode',
        'url': 'http://test.url',
        'duration': 90
    }
    mock_download.return_value = 'downloads/test_video.mp4'
    mock_process.return_value = ('output/test_summary.mp4', 'Stats: 5 scenes found.')
    mock_confirm.return_value = True # Simulate user clicking "Post"
    
    # Run job
    job()
    
    # Verify calls
    mock_scrape.assert_called_once()
    mock_download.assert_called_once_with('http://test.url', output_dir='downloads')
    mock_process.assert_called_once_with('downloads/test_video.mp4')
    mock_confirm.assert_called_once_with('output/test_summary.mp4', 'Stats: 5 scenes found.')
    mock_post.assert_called_once()
    
    print("Job finished successfully. All steps verified.")

if __name__ == "__main__":
    test_scheduler_job()
