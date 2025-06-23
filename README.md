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

# Specify language (optional, auto-detected if not provided)
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 -l en

# Use CPU instead of GPU
uv run transcribe_advanced.py audio/Episode\ 1\ Arrays\ Start\ at\ Zero.mp3 --device cpu
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
- Enhanced error handling and multiple model fallbacks
- Word-level timestamps and confidence scores

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

```
00:00:05-00:00:07: Hello,
00:00:07-00:00:09: welcome
00:00:09-00:00:12: to our
00:00:12-00:00:15: podcast
```

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
5. **Poor transcription quality**: Try the advanced script with `large-v3` model
6. **Diarization not working**: The advanced script will try multiple models automatically

## Performance Tips

- Use `large-v3` model for best quality (requires more memory)
- Use `medium` model for balanced speed/quality
- Use `small` or `base` for faster processing
- GPU processing is 5-10x faster than CPU
- The advanced script provides better diarization but takes longer

## License

This project is open source and available under the MIT License. 