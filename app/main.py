import io
import os
import time
import traceback
import yadisk
import datetime
import whisper
import mimetypes

from moviepy import VideoFileClip
from argparse import ArgumentParser


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(PROJECT_ROOT, "tmp")

VIDEO_PATH = None
AUDIO_PATH = None


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--disk_token', required=True)
    return parser.parse_args()


def ensure_tmp_dir():
    print(f"[INFO] Ensuring temporary directory exists: {TMP_DIR}")
    os.makedirs(TMP_DIR, exist_ok=True)
    print(f"[INFO] Temporary directory ready")


def validate_video_file(filepath):
    """Validates that the downloaded file is actually a video file"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Downloaded file does not exist: {filepath}")
    
    file_size = os.path.getsize(filepath)
    print(f"[INFO] Downloaded file size: {file_size} bytes")
    
    if file_size == 0:
        raise ValueError("Downloaded file is empty. The file may not have been downloaded correctly.")
    
    # Check if file is suspiciously small (likely HTML error page)
    if file_size < 1024:  # Less than 1KB is suspicious for a video
        print(f"[WARNING] File size is very small ({file_size} bytes). This might be an error page.")
        # Try to read first few bytes to check if it's HTML
        try:
            with open(filepath, 'rb') as f:
                first_bytes = f.read(100)
                if b'<html' in first_bytes.lower() or b'<!doctype' in first_bytes.lower():
                    raise ValueError("Downloaded file appears to be an HTML page, not a video file. Please check the file path and permissions.")
        except Exception:
            pass
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type and not mime_type.startswith('video/'):
        print(f"[WARNING] File MIME type is {mime_type}, expected video/*")
    
    print(f"[INFO] File validation passed")


def download_video(disk_token, _path):
    print(f"[STEP 1/3] Starting video download from Yandex Disk...")
    print(f"[INFO] Input: {_path}")

    disk_client = yadisk.Client(token=disk_token)

    with disk_client:
        is_valid = disk_client.check_token()
        print(f"[INFO] Token validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
        
        if not is_valid:
            raise Exception("Invalid Yandex Disk token")

        file_path = _path
        print("[INFO] Disk info:", disk_client.get_disk_info())
        
        # Check if file exists on disk
        print(f"[INFO] Checking if file exists on Yandex Disk: {file_path}")
        if not disk_client.exists(file_path):
            raise FileNotFoundError(f"File not found on Yandex Disk: {file_path}")
        # Get file info
        file_info = disk_client.get_meta(file_path)
        print(f"[INFO] File found: {file_info.name} ({file_info.size} bytes)")
        
        # Determine file extension from original file
        original_ext = os.path.splitext(file_info.name)[1] or '.mov'
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"video_{timestamp}{original_ext}"
        filepath = os.path.join(TMP_DIR, filename)
        global VIDEO_PATH
        VIDEO_PATH = filepath
        print(f"[INFO] Temporary video file: {filepath}")

        print(f"[INFO] Downloading video...")
        disk_client.download(file_path, filepath)
        print(f"[SUCCESS] Video downloaded successfully")
        
        # Validate the downloaded file
        validate_video_file(filepath)

    return filepath


def video_to_audio(filepath):
    print(f"[STEP 2/3] Extracting audio from video...")
    print(f"[INFO] Loading video file: {filepath}")
    
    video = VideoFileClip(filepath)
    audio = video.audio
    print(f"[INFO] Video loaded. Duration: {video.duration:.2f} seconds")
    
    # Используем timestamp для уникальности имени файла
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"audio_{timestamp}.mp3"
    audio_path = os.path.join(TMP_DIR, filename)
    
    global AUDIO_PATH
    AUDIO_PATH = audio_path

    print(f"[INFO] Extracting audio to: {audio_path}")
    audio.write_audiofile(audio_path)
    print(f"[SUCCESS] Audio extracted successfully")
    
    audio.close()
    video.close()
    
    return audio_path


def audio_to_text(audio_path):
    print(f"[STEP 3/3] Transcribing audio to text...")
    print(f"[INFO] Loading Whisper model (medium)...")
    print(f"[INFO] This may take a moment on first run...")
    
    model = whisper.load_model("medium")
    print(f"[INFO] Model loaded. Starting transcription...")
    
    result = model.transcribe(audio_path)
    print(f"[SUCCESS] Transcription completed")
    
    return result["text"]


def upload_transcription_to_yandex_disk(disk_token, disk_video_file_path, transcription):
    print(f"[STEP 4/4] Uploading transcription to Yandex Disk...")
    print(f"[INFO] Loading Yandex Disk client...")
    disk_client = yadisk.Client(token=disk_token)
    with disk_client:
        print(f"[INFO] Yandex Disk client loaded. Starting upload...")
        transcription_file = io.StringIO(transcription)
        transcription_file_path = os.path.join(
            disk_video_file_path.split('/')[:-1], 
            f"transcription_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.txt"
        )
        disk_client.upload(transcription_file, transcription_file_path)
        print(f"[SUCCESS] Transcription uploaded successfully")


def remove_temp_files(video_path, audio_path):
    """Удаляет временные файлы с проверкой их существования"""
    print(f"[CLEANUP] Removing temporary files...")
    
    if video_path:
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"[CLEANUP] Removed temporary video file: {video_path}")
            else:
                print(f"[CLEANUP] Video file not found (may have been already removed)")
        except (OSError, TypeError) as e:
            print(f"[WARNING] Error removing video file: {e}")
    
    if audio_path:
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"[CLEANUP] Removed temporary audio file: {audio_path}")
            else:
                print(f"[CLEANUP] Audio file not found (may have been already removed)")
        except (OSError, TypeError) as e:
            print(f"[WARNING] Error removing audio file: {e}")
    
    print(f"[CLEANUP] Cleanup completed")


def main():
    print("=" * 60)
    print("Yandex Disk Video Whisper Transcription Tool")
    print("=" * 60)
    
    args = parse_args()
    print(f"[INFO] Yandex Disk token provided")

    disk_video_file_path = input("Enter file path from Yandex Disk (e.g., /folder/video.mov): ")
    print()

    start_time = time.time()
    
    # Убеждаемся, что папка tmp существует
    ensure_tmp_dir()
    print()

    try:
        video_path = download_video(args.disk_token, disk_video_file_path)
        print()
        
        audio_path = video_to_audio(video_path)
        print()
        
        transcription = audio_to_text(audio_path)
        print()

        upload_transcription_to_yandex_disk(args.disk_token, disk_video_file_path, transcription)

        print("=" * 60)
        print("TRANSCRIPTION RESULT:")
        print("=" * 60)
        print(transcription)
        print("=" * 60)

        elapsed_time = time.time() - start_time
        print(f"[INFO] Total processing time: {elapsed_time:.2f} seconds")
        print()

        remove_temp_files(video_path, audio_path)
        print()
        print("[SUCCESS] Process completed successfully!")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[ERROR] An error occurred during processing")
        print("=" * 60)
        remove_temp_files(VIDEO_PATH, AUDIO_PATH)
        print(f"[ERROR] Error details: {e}")
        print()
        print("[ERROR] Full traceback:")
        print(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
