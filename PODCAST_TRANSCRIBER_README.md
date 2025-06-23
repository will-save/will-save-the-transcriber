# Podcast RSS Feed Transcriber

This script automatically downloads and transcribes podcast episodes from the Will Save the Podcast RSS feed, organizing them by series with readable titles and sanitized filenames.

## Features

- **RSS Feed Parsing**: Automatically fetches and parses the podcast RSS feed
- **Series Organization**: Organizes episodes by series using the same logic as the website
- **Smart File Naming**: Sanitizes filenames for better compatibility
- **Incremental Processing**: Skips already transcribed episodes
- **Audio Cleanup**: Automatically deletes downloaded audio files after transcription
- **CUDA Support**: Uses GPU acceleration when available

## Usage

### Basic Usage
```bash
python podcast_transcriber.py
```

This will:
1. Fetch the Will Save the Podcast RSS feed
2. Download all audio files
3. Transcribe each episode using WhisperX
4. Organize transcripts by series in the `episodes/` directory
5. Clean up downloaded audio files

### Advanced Usage

#### Keep Audio Files
```bash
python podcast_transcriber.py --keep-audio
```

#### Use Different RSS Feed
```bash
python podcast_transcriber.py --rss-url "https://your-podcast-feed.xml"
```

## Directory Structure

The script creates the following structure:

```
episodes/
├── threefold_conspiracy_book_1/
│   ├── episode_1_title.md
│   └── episode_2_title.md
├── threefold_conspiracy_book_2/
│   ├── episode_3_title.md
│   └── episode_4_title.md
├── unknown_treasures/
│   └── unknown_treasures_episode.md
└── ...
```

## Series Mapping

The script uses the same series mapping as the website:

- **Will Save the Trailer**: Trailer episodes
- **Threefold Conspiracy Book 1-6**: Main story arcs
- **Unknown Treasures**: Special episodes
- **Nano Adventure**: Short adventures
- **Will Save the Interviews**: Interview episodes
- **Will Save the Recap**: Recap episodes
- **Won't Save**: Spinoff series

## Requirements

- Python 3.8+
- All dependencies from `pyproject.toml`
- FFmpeg (for audio conversion)
- Hugging Face token (for speaker diarization - optional)

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables (optional):
```bash
cp env-example .env
# Edit .env and add your HF_TOKEN for speaker diarization
```

3. Run the script:
```bash
python podcast_transcriber.py
```

## Notes

- The script will skip episodes that have already been transcribed
- Audio files are temporarily downloaded to the `audio/` directory and cleaned up after transcription
- Use `--keep-audio` if you want to preserve the downloaded audio files
- The script uses the same series parsing logic as the JavaScript code on the website
- Filenames are sanitized to remove special characters and ensure compatibility 