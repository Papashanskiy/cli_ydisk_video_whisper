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


def parse_args():
    parser = ArgumentParser()
    # parser.add_argument('--url', required=True, help='URL для скачивания видео с Яндекс.Диска')
    parser.add_argument('--disk_token', required=True, help='Токен доступа к Яндекс.Диску')
    return parser.parse_args()


def ensure_tmp_dir():
    """Создает папку tmp если её нет"""
    os.makedirs(TMP_DIR, exist_ok=True)


def download_video(disk_token, url):
    disk_client = yadisk.Client(token=disk_token)

    with disk_client:
        print("Is valid token: ", disk_client.check_token())
        # Используем timestamp для уникальности имени файла
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"video_{timestamp}.mov"
        filepath = os.path.join(TMP_DIR, filename)
        print(f"temp file name: {filepath}")

        disk_client.download_by_link(url, filepath)

    return filepath


def video_to_audio(filepath):
    video = VideoFileClip(filepath)
    audio = video.audio
    
    # Используем timestamp для уникальности имени файла
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"audio_{timestamp}.mp3"
    audio_path = os.path.join(TMP_DIR, filename)
    
    audio.write_audiofile(audio_path)
    audio.close()
    video.close()
    
    return audio_path


def audio_to_text(audio_path):
    model = whisper.load_model("medium")
    result = model.transcribe(audio_path)
    return result["text"]


def remove_temp_files(video_path, audio_path):
    """Удаляет временные файлы с проверкой их существования"""
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"Удален временный файл: {video_path}")
    except OSError as e:
        print(f"Ошибка при удалении видео файла: {e}")
    
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Удален временный файл: {audio_path}")
    except OSError as e:
        print(f"Ошибка при удалении аудио файла: {e}")


def main():
    args = parse_args()

    url = input("Введите URL видео с Яндекс.Диска: ")

    start_time = time.time()
    
    # Убеждаемся, что папка tmp существует
    ensure_tmp_dir()

    try:
        video_path = download_video(args.disk_token, url)
        audio_path = video_to_audio(video_path)
        transcription = audio_to_text(audio_path)

        print("=" * 60)
        print("Финальный результат:")
        print(transcription)

        print("=" * 60)
        print("Затраченное время:")
        print(f"{time.time() - start_time:.2f} секунд")

        remove_temp_files(video_path, audio_path)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        print(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
