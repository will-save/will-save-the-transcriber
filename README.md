# Will Save The Transcriber

A Python script that uses WhisperX to transcribe audio files with speaker diarization and outputs the results as a markdown file.

## Features

- 🎤 **Speaker Diarization**: Automatically identifies and labels different speakers
- 📝 **Markdown Output**: Clean, readable transcript format with timestamps
- 🚀 **WhisperX**: Advanced transcription with improved accuracy and alignment
- ⚡ **GPU Acceleration**: Supports CUDA for faster processing
- 🌍 **Multi-language**: Supports multiple languages
- 🎯 **Multiple Model Options**: Choose from different WhisperX model sizes
- 🔄 **Robust Diarization**: Multiple fallback models for better speaker detection
- 📊 **Confidence Scores**: Track transcription quality
- 🕐 **Word-Level Timestamps**: Precise timing for individual words (advanced mode)
- 🎙️ **Podcast RSS Integration**: Automatically transcribe podcast episodes from RSS feeds
- ⚙️ **Flexible Methods**: Choose between simple and advanced transcription methods

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

1. Install UV if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up Hugging Face token for speaker diarization:
   - Get a token from [Hugging Face](https://huggingface.co/settings/tokens)
   - Accept the terms for the [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) model
   - Accept the terms for [pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)
   - Create a `.env` file in the project root:
     ```
     HF_TOKEN=your_huggingface_token_here
     ```
   - Or set the environment variable: `export HF_TOKEN=your_token_here`

## Usage

### Basic Usage

```bash
uv run transcribe.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3
```

### Advanced Usage (Recommended)

```bash
# Use the advanced script with better models and diarization
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3

# Specify output file
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 -o transcript.md

# Use a specific model size
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --model large-v3

# Specify exact number of speakers (if known)
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --num-speakers 3

# Set speaker count range
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --min-speakers 2 --max-speakers 5

# Skip audio analysis for diarization
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --no-audio-analysis

# Specify language (optional, auto-detected if not provided)
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 -l en

# Use CPU instead of GPU
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --device cpu

# Disable word-level timestamps for faster processing
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --no-word-timestamps

# Test environment setup
uv run transcribe_advanced.py --test-env
```

### Command Line Options

#### Basic Script (`transcribe.py`)
- `audio_file`: Path to the audio file (MP3, WAV, etc.)
- `-o, --output`: Output markdown file path (optional)
- `-l, --language`: Language code (e.g., 'en', 'es', 'fr') - optional
- `--device`: Device to use ('cuda' or 'cpu') - defaults to 'cuda'
- `--model`: WhisperX model size - defaults to 'large-v3'

#### Advanced Script (`transcribe_advanced.py`)
- All options from basic script, plus:
- `--diarization-model`: Pyannote diarization model to use
- `--num-speakers`: Exact number of speakers (if known)
- `--min-speakers`: Minimum number of speakers to detect (default: 1)
- `--max-speakers`: Maximum number of speakers to detect (default: 20)
- `--no-audio-analysis`: Skip audio analysis for diarization parameters
- `--no-word-timestamps`: Disable word-level timestamps in output (faster processing)
- `--test-env`: Test .env file loading and token validation
- `-v, --version`: Diarization version: 1 (original) or 2 (pyannote-audio docs approach) (default: 2)
- Enhanced error handling and multiple model fallbacks
- Word-level timestamps and confidence scores
- Audio analysis for optimal diarization parameters
- Post-processing for better speaker assignment

### Model Options

Available WhisperX models (in order of quality and speed):
- `tiny`: Fastest, lowest quality
- `base`: Fast, low quality
- `small`: Balanced speed/quality
- `medium`: Good quality, moderate speed
- `large`: High quality, slower
- `large-v2`: Very high quality (default in basic script)
- `large-v3`: Best quality (default in advanced script)

## Output Format

### Basic Output
```markdown
# Audio Transcription

**Language:** en

---

## SPEAKER_00

**[00:00:05 - 00:00:15]** Hello, welcome to our podcast about programming.

**[00:00:18 - 00:00:25]** Today we're going to talk about arrays.

## SPEAKER_01

**[00:00:28 - 00:00:35]** That sounds interesting! I've always wondered about arrays.

---

## Summary

- **Total segments:** 3
- **Duration:** 00:00:35
- **Number of speakers:** 2
```

### Advanced Output
```markdown
# Advanced Audio Transcription

**Language:** en

---

## SPEAKER_00

**[00:00:05 - 00:00:15] (confidence: 0.85)** Hello, welcome to our podcast about programming.

**Words:**
  - **[00:00:05 - 00:00:07]** Hello
  - **[00:00:07 - 00:00:09]** welcome
  - **[00:00:09 - 00:00:12]** to our
  - **[00:00:12 - 00:00:15]** podcast

---

## Summary

- **Total segments:** 3
- **Duration:** 00:00:35
- **Number of speakers:** 2
- **Average confidence:** 0.82
- **Confidence range:** 0.75 - 0.89
- **Total words:** 15
```

## Requirements

- Python 3.8 or higher
- CUDA-compatible GPU (optional, for faster processing)
- Audio file in a supported format (MP3, WAV, M4A, etc.)
- Hugging Face token for speaker diarization

## Notes

- The first run will download the WhisperX models, which may take some time
- GPU processing is significantly faster than CPU processing
- The script automatically falls back to CPU if CUDA is not available
- Speaker diarization works best with clear audio and distinct voices
- If no HF_TOKEN is provided, the script will transcribe without speaker diarization
- The advanced script includes multiple fallback diarization models for better reliability

## Troubleshooting

If you encounter issues:

1. **CUDA errors**: Try using `--device cpu`
2. **Memory issues**: Try a smaller model (e.g., `--model medium`)
3. **Audio format issues**: Ensure your audio file is in a supported format
4. **Speaker diarization errors**: Make sure you have a valid HF_TOKEN and have accepted the terms for the pyannote/speaker-diarization-3.1 model 
5. **Segmentation diarization errors**: A dependency for diarization of episodes 
6. **Poor transcription quality**: Try the advanced script with `large-v3` model
7. **Diarization not working**: The advanced script will try multiple models automatically
8. **Slow processing**: Use `--no-word-timestamps` to disable word-level timestamps for faster processing
9. **Environment issues**: Use `--test-env` to verify your setup
10. **Podcast transcription too slow**: Use `-m simple` for faster podcast transcription

## Performance Tips

- **Use GPU acceleration** if available (CUDA) for faster transcription
- **Large model** provides best accuracy but slower processing
- **Word timestamps** add processing time - use `--no-word-timestamps` for speed
- **Simple method** is faster than advanced for podcast transcription
- **Episode skipping** automatically checks for existing transcripts before downloading audio
- **Audio cleanup** happens immediately after each episode to save disk space
- **Batch processing** handles multiple episodes efficiently

## Quick Start Examples

### Single File Transcription

**Basic transcription of any audio file:**
```bash
# Simple transcription (faster)
python transcribe_simple.py your_audio_file.mp3

# Advanced transcription (recommended, more features)
python transcribe_advanced.py your_audio_file.mp3

# Advanced transcription with word-level timestamps
python transcribe_advanced.py your_audio_file.mp3

# Advanced transcription without word timestamps (faster)
python transcribe_advanced.py your_audio_file.mp3 --no-word-timestamps

# Specify language and output file
python transcribe_advanced.py your_audio_file.mp3 -l en -o transcript.md
```

**Common use cases:**
```bash
# Podcast episode with word timestamps
python transcribe_advanced.py podcast_episode.mp3

# Interview with multiple speakers
python transcribe_advanced.py interview.mp3 --num-speakers 3

# Non-English content
python transcribe_advanced.py spanish_audio.mp3 -l es

# CPU-only processing
python transcribe_advanced.py audio.mp3 --device cpu

# Test environment setup
python transcribe_advanced.py --test-env
```

### Will Save the Podcast Feed Parsing

**Automatically transcribe all episodes from the Will Save the Podcast RSS feed:**

```bash
# Transcribe all episodes using simple method (default, faster)
python podcast_transcriber.py

# Use advanced transcription method (more features, slower)
python podcast_transcriber.py -m advanced

# Use simple transcription explicitly
python podcast_transcriber.py -m simple

# Keep downloaded audio files for reuse
python podcast_transcriber.py --keep-audio

# Use a different RSS feed with advanced method
python podcast_transcriber.py --rss-url "https://your-podcast-feed.xml" -m advanced
```

**Transcription Methods:**

- **Simple Method** (`-m simple`): Faster processing with basic speaker diarization, suitable for most podcast transcription needs
- **Advanced Method** (`-m advanced`): More detailed analysis with advanced speaker diarization, word-level timestamps, and comprehensive confidence analysis

**What this does:**
1. **Fetches RSS feed** from Will Save the Podcast
2. **Checks for existing transcripts** before downloading audio files
3. **Downloads audio files** only for episodes that need transcription
4. **Organizes by series** (Threefold Conspiracy Book 1, Unknown Treasures, etc.)
5. **Transcribes each episode** using advanced diarization
6. **Saves markdown files** in organized directory structure
7. **Cleans up audio files** immediately after each episode transcription

**Output structure:**
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

**Features:**
- **Method selection** - Choose between simple (faster) and advanced (more features) transcription
- **Automatic series detection** using the same logic as the website
- **Sanitized filenames** for better compatibility
- **Incremental processing** - only transcribes new episodes
- **Advanced diarization** with version 2 (pyannote-audio docs approach)
- **Word-level timestamps** (advanced method only)
- **English language optimization** for podcast content
- **GPU acceleration** when available
- **Comprehensive confidence analysis** (advanced method only)

**For other podcasts:**
```bash
# Transcribe any podcast RSS feed with simple method
python podcast_transcriber.py --rss-url "https://feed.podbean.com/your-podcast/feed.xml"

# Use advanced method for better quality
python podcast_transcriber.py --rss-url "https://feed.podbean.com/your-podcast/feed.xml" -m advanced

# Customize speaker detection with advanced method
python podcast_transcriber.py --rss-url "your-feed.xml" -m advanced
```

> **⚠️ Disclaimer**: The `--rss-url` feature for other podcasts has not been thoroughly vetted. Different podcast feeds may have varying RSS structures, audio formats, or metadata that could affect transcription quality. Use at your own discretion and test with a small sample first.
> 
> **Note**: For non-Will Save the Podcast feeds, episodes are saved directly to the `episodes/` directory without series organization, as the series detection logic is specific to Will Save the Podcast's naming conventions.

## License

This project is open source and available under the MIT License. 