# CLI Yandex Disk Video Whisper

A simple command-line tool that downloads videos from Yandex Disk and transcribes them using OpenAI Whisper.

## Features

- 📥 Download videos directly from Yandex Disk
- 🎵 Extract audio from video files
- 🗣️ Transcribe audio to text using Whisper AI
- 🧹 Automatic cleanup of temporary files

## Requirements

- Python 3.7+
- Yandex Disk access token

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd cli_ydisk_video_whisper
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Getting a Yandex Disk Token

Use the helper script in `misc/get_disk_token.py` to obtain your access token:

1. Update the script with your Yandex application credentials
2. Run the script and follow the instructions
3. Save the token for use with the main application

## Usage

Run the application with your Yandex Disk token:

```bash
python app/main.py --disk_token YOUR_TOKEN_HERE
```

The application will prompt you to enter the Yandex Disk video PATH. After processing, it will display the transcription and automatically clean up temporary files.

## How It Works

1. Downloads the video from Yandex Disk to a temporary directory
2. Extracts audio from the video file
3. Transcribes the audio using Whisper (medium model)
4. Displays the transcription result
5. Removes temporary files

## Dependencies

- `openai-whisper` - Speech recognition model
- `yadisk` - Yandex Disk API client
- `moviepy` - Video processing library

## License

MIT

