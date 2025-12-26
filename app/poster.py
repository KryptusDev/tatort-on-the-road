import logging
import os
import tweepy
from mastodon import Mastodon

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def post_to_twitter(video_path, text):
    """
    Uploads video and posts a tweet.
    Requires: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
    """
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    
    if not all([api_key, api_secret, access_token, access_secret]):
        logging.warning("Twitter credentials missing. Skipping Twitter post.")
        return False
        
    logging.info("Posting to Twitter...")
    try:
        # Authenticate v1.1 for media upload
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api = tweepy.API(auth)
        
        # Upload media
        media = api.media_upload(video_path)
        
        # Authenticate v2 for tweeting
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Create Tweet
        client.create_tweet(text=text, media_ids=[media.media_id])
        logging.info("Successfully posted to Twitter.")
        return True
        
    except Exception as e:
        logging.error(f"Twitter post failed: {e}")
        return False

def post_to_mastodon(video_path, text):
    """
    Uploads video and posts a toot.
    Requires: MASTODON_ACCESS_TOKEN, MASTODON_API_BASE_URL
    """
    access_token = os.getenv("MASTODON_ACCESS_TOKEN")
    api_base_url = os.getenv("MASTODON_API_BASE_URL")
    
    if not all([access_token, api_base_url]):
        logging.warning("Mastodon credentials missing. Skipping Mastodon post.")
        return False
        
    logging.info("Posting to Mastodon...")
    try:
        mastodon = Mastodon(
            access_token=access_token,
            api_base_url=api_base_url
        )
        
        # Upload media
        media = mastodon.media_post(video_path, description="Tatort Summary")
        
        # Post status
        mastodon.status_post(text, media_ids=[media])
        logging.info("Successfully posted to Mastodon.")
        return True
        
    except Exception as e:
        logging.error(f"Mastodon post failed: {e}")
        return False

def post_to_all(video_path, text):
    """
    Posts to all configured social media platforms.
    """
    twitter_success = post_to_twitter(video_path, text)
    mastodon_success = post_to_mastodon(video_path, text)
    return twitter_success, mastodon_success
