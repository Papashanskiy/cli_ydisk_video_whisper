import os
import time
import traceback
import yadisk
import datetime
import whisper

from moviepy import VideoFileClip
from argparse import ArgumentParser


# Получаем корневую директорию проекта (на уровень выше app/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(PROJECT_ROOT, "tmp")

VIDEO_PATH = None
AUDIO_PATH = None


def parse_args():
    parser = ArgumentParser()
    # parser.add_argument('--url', required=True, help='URL для скачивания видео с Яндекс.Диска')
    parser.add_argument('--disk_token', required=True, help='Токен доступа к Яндекс.Диску')
    return parser.parse_args()


def ensure_tmp_dir():
    """Создает папку tmp если её нет"""
    print(f"[INFO] Ensuring temporary directory exists: {TMP_DIR}")
    os.makedirs(TMP_DIR, exist_ok=True)
    print(f"[INFO] Temporary directory ready")


def download_video(disk_token, url):
    print(f"[STEP 1/3] Starting video download from Yandex Disk...")
    print(f"[INFO] Video URL: {url}")
    
    disk_client = yadisk.Client(token=disk_token)

    with disk_client:
        is_valid = disk_client.check_token()
        print(f"[INFO] Token validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
        
        if not is_valid:
            raise Exception("Invalid Yandex Disk token")
        
        # Используем timestamp для уникальности имени файла
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"video_{timestamp}.mov"
        filepath = os.path.join(TMP_DIR, filename)
        global VIDEO_PATH
        VIDEO_PATH = filepath
        print(f"[INFO] Temporary video file: {filepath}")

        print(f"[INFO] Downloading video...")
        disk_client.download_by_link(url, filepath)
        print(f"[SUCCESS] Video downloaded successfully")

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


def remove_temp_files(video_path, audio_path):
    """Удаляет временные файлы с проверкой их существования"""
    print(f"[CLEANUP] Removing temporary files...")
    
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"[CLEANUP] Removed temporary video file: {video_path}")
        else:
            print(f"[CLEANUP] Video file not found (may have been already removed)")
    except OSError as e:
        print(f"[WARNING] Error removing video file: {e}")
    
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"[CLEANUP] Removed temporary audio file: {audio_path}")
        else:
            print(f"[CLEANUP] Audio file not found (may have been already removed)")
    except OSError as e:
        print(f"[WARNING] Error removing audio file: {e}")
    
    print(f"[CLEANUP] Cleanup completed")


def main():
    print("=" * 60)
    print("Yandex Disk Video Whisper Transcription Tool")
    print("=" * 60)
    
    args = parse_args()
    print(f"[INFO] Yandex Disk token provided")

    url = input("Enter video URL from Yandex Disk: ")
    print()

    start_time = time.time()
    
    # Убеждаемся, что папка tmp существует
    ensure_tmp_dir()
    print()

    try:
        video_path = download_video(args.disk_token, url)
        print()
        
        audio_path = video_to_audio(video_path)
        print()
        
        transcription = audio_to_text(audio_path)
        print()

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
