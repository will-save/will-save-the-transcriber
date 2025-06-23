#!/usr/bin/env python3
"""
Advanced transcription script using WhisperX with improved speaker diarization.
Multiple model options and better error handling for optimal results.
"""

import argparse
import os
import sys
from pathlib import Path
import whisperx
import torch
import gc
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from dotenv import load_dotenv
import subprocess
import tempfile


def test_env_loading():
    """
    Test function to verify .env file loading and token access.
    """
    print("Testing .env file loading...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env file found: {env_file.absolute()}")
    else:
        print(f"❌ .env file not found at: {env_file.absolute()}")
        return False
    
    # Load token
    token = load_hf_token()
    if token:
        print(f"✅ Token loaded successfully: {token[:10]}...")
        return True
    else:
        print("❌ Failed to load token")
        return False


def validate_hf_token(hf_token):
    """
    Validate that the Hugging Face token is working.
    
    Args:
        hf_token (str): Hugging Face token to validate
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=hf_token)
        # Try to access a simple model to test the token
        api.model_info("pyannote/speaker-diarization-3.1")
        return True
    except Exception as e:
        print(f"⚠️  Token validation failed: {str(e)}")
        return False


def load_hf_token():
    """
    Load Hugging Face token from .env file or environment variable.
    
    Returns:
        str: Hugging Face token or None if not found
    """
    # Load from .env file explicitly
    print("Loading environment variables from .env file...")
    load_dotenv(override=True)
    
    # Try to get token from environment
    hf_token = os.getenv("HF_TOKEN")
    
    if not hf_token:
        print("⚠️  Warning: HF_TOKEN not found in .env file or environment variables.")
        print("   Speaker diarization requires a Hugging Face token.")
        print("   Please create a .env file with: HF_TOKEN=your_token_here")
        print("   Or set the environment variable: export HF_TOKEN=your_token_here")
        return None
    
    print(f"✅ HF_TOKEN loaded successfully: {hf_token[:10]}...")
    return hf_token


def transcribe_audio_advanced(audio_path, output_path=None, language=None, device="cuda", 
                             model_size="large-v3", diarization_model="pyannote/speaker-diarization-3.1"):
    """
    Advanced transcription with multiple model options and better diarization.
    
    Args:
        audio_path (str): Path to the audio file
        output_path (str): Path for the output markdown file
        language (str): Language code (e.g., 'en', 'es', 'fr')
        device (str): Device to use ('cuda' or 'cpu')
        model_size (str): WhisperX model size
        diarization_model (str): Pyannote diarization model to use
    
    Returns:
        str: Path to the output markdown file
    """
    
    # Check if CUDA is available
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA not available, falling back to CPU")
        device = "cpu"
    
    # Convert audio to WAV format for better processing
    converted_audio_path = convert_audio_to_wav(audio_path)
    
    # Load audio file
    print(f"Loading audio file: {converted_audio_path}")
    audio = whisperx.load_audio(converted_audio_path)
    
    # Load WhisperX model with optimal settings
    print(f"Loading WhisperX model: {model_size}")
    compute_type = "float16" if device == "cuda" else "float32"
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    
    # Transcribe audio with supported parameters only
    print("Transcribing audio with advanced settings...")
    result = model.transcribe(
        audio, 
        batch_size=16
    )
    
    # Align whisper output with better parameters
    print("Aligning timestamps with high precision...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(
        result["segments"], 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=False
    )
    
    # Advanced diarization with multiple fallback options
    print("Performing advanced speaker diarization...")
    hf_token = load_hf_token()
    
    if hf_token:
        # Validate the token first
        print("Validating Hugging Face token...")
        if not validate_hf_token(hf_token):
            print("❌ HF token validation failed. Please check your token and model access.")
            print("   Make sure you've accepted the terms for pyannote/speaker-diarization-3.1")
            hf_token = None
        
        if hf_token:
            diarize_segments = None
            
            # Try multiple diarization models in order of preference
            diarization_models = [
                "pyannote/speaker-diarization-3.1",
                "pyannote/speaker-diarization-2.1",
                "pyannote/speaker-diarization"
            ]
            
            for model_name in diarization_models:
                try:
                    print(f"Trying diarization model: {model_name}")
                    print(f"Using HF token: {hf_token[:10]}...")
                    
                    # Try to load the model with explicit token passing
                    diarize_model = Pipeline.from_pretrained(
                        model_name,
                        use_auth_token=hf_token,
                        cache_dir=None  # Use default cache
                    )
                    
                    if diarize_model is None:
                        print(f"⚠️  Failed to load {model_name} - model is None")
                        continue
                        
                    diarize_model.to(torch.device(device))
                    
                    # Run diarization with progress tracking
                    with ProgressHook() as hook:
                        diarize_segments = diarize_model(
                            converted_audio_path,
                            min_speakers=1,
                            max_speakers=10,
                            num_speakers=None,  # Auto-detect
                            hook=hook
                        )
                    
                    print(f"✅ Successfully used {model_name}")
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"⚠️  Failed with {model_name}: {error_msg}")
                    
                    # Check if it's a model access issue
                    if "Could not download" in error_msg or "gated" in error_msg.lower():
                        print(f"   🔗 Please visit https://hf.co/{model_name} to accept the terms")
                        print(f"   🔗 You may also need to accept terms for related models:")
                        if "segmentation-3.0" in error_msg:
                            print(f"   🔗 https://hf.co/pyannote/segmentation-3.0")
                        if "segmentation" in error_msg:
                            print(f"   🔗 https://hf.co/pyannote/segmentation")
                    
                    continue
            
            if diarize_segments is not None:
                try:
                    # Assign speaker labels with better word-level alignment
                    print("Assigning speaker labels with high precision...")
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    print("✅ Speaker diarization completed successfully!")
                    
                except Exception as e:
                    print(f"⚠️  Warning: Speaker assignment failed: {str(e)}")
                    print("   Continuing with transcription without speaker labels...")
                    for segment in result["segments"]:
                        segment["speaker"] = "Speaker 0"
            else:
                print("⚠️  All diarization models failed, continuing without speaker labels...")
                for segment in result["segments"]:
                    segment["speaker"] = "Speaker 0"
    else:
        print("⚠️  Skipping speaker diarization due to missing HF_TOKEN")
        for segment in result["segments"]:
            segment["speaker"] = "Speaker 0"
    
    # Generate output filename if not provided
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_advanced_transcript.md"
    
    # Write markdown output
    print(f"Writing transcript to: {output_path}")
    write_advanced_markdown_transcript(result, output_path)
    
    # Clean up
    del model
    del model_a
    if 'diarize_model' in locals():
        del diarize_model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    
    # Clean up temporary WAV file if it was created
    if converted_audio_path != audio_path and os.path.exists(converted_audio_path):
        try:
            os.unlink(converted_audio_path)
            print(f"🧹 Cleaned up temporary file: {Path(converted_audio_path).name}")
        except Exception as e:
            print(f"⚠️  Could not clean up temporary file: {e}")
    
    return output_path


def write_advanced_markdown_transcript(result, output_path):
    """
    Write transcription results to a markdown file with advanced formatting.
    
    Args:
        result (dict): WhisperX transcription result
        output_path (str): Path to output markdown file
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# Advanced Audio Transcription\n\n")
        f.write(f"**Language:** {result.get('language', 'Unknown')}\n\n")
        f.write("---\n\n")
        
        # Write segments with speaker labels and confidence
        current_speaker = None
        
        for segment in result["segments"]:
            speaker = segment.get("speaker", "Unknown")
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            text = segment["text"].strip()
            confidence = segment.get("avg_logprob", 0)
            
            # Add speaker header if speaker changes
            if speaker != current_speaker:
                f.write(f"\n## {speaker}\n\n")
                current_speaker = speaker
            
            # Write segment with timestamp and confidence
            confidence_str = f" (confidence: {confidence:.2f})" if confidence != 0 else ""
            f.write(f"**[{start_time} - {end_time}]{confidence_str}** {text}\n\n")
            
            # Add word-level timestamps if available
            if "words" in segment and segment["words"]:
                f.write("```\n")
                for word in segment["words"]:
                    word_start = format_time(word["start"])
                    word_end = format_time(word["end"])
                    f.write(f"{word_start}-{word_end}: {word['word']}\n")
                f.write("```\n\n")
        
        # Write comprehensive summary
        f.write("---\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total segments:** {len(result['segments'])}\n")
        f.write(f"- **Duration:** {format_time(result['segments'][-1]['end'] if result['segments'] else 0)}\n")
        
        # Count speakers
        speakers = set()
        for segment in result["segments"]:
            if "speaker" in segment:
                speakers.add(segment["speaker"])
        f.write(f"- **Number of speakers:** {len(speakers)}\n")
        
        # Add confidence scores
        if result["segments"] and "avg_logprob" in result["segments"][0]:
            confidences = [seg.get("avg_logprob", 0) for seg in result["segments"]]
            avg_confidence = sum(confidences) / len(confidences)
            min_confidence = min(confidences)
            max_confidence = max(confidences)
            f.write(f"- **Average confidence:** {avg_confidence:.2f}\n")
            f.write(f"- **Confidence range:** {min_confidence:.2f} - {max_confidence:.2f}\n")
        
        # Add word count
        total_words = sum(len(seg["text"].split()) for seg in result["segments"])
        f.write(f"- **Total words:** {total_words}\n")


def format_time(seconds):
    """
    Format time in seconds to HH:MM:SS format.
    
    Args:
        seconds (float): Time in seconds
    
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def convert_audio_to_wav(input_path, output_path=None):
    """
    Convert audio file to WAV format with optimal parameters for WhisperX.
    
    Args:
        input_path (str): Path to input audio file
        output_path (str): Path for output WAV file (optional)
    
    Returns:
        str: Path to the converted WAV file
    """
    input_path = Path(input_path)
    
    if output_path is None:
        # Create temporary WAV file
        output_path = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    else:
        output_path = Path(output_path)
    
    print(f"Converting {input_path.name} to WAV format...")
    
    # FFmpeg command with optimal parameters for WhisperX
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-ar', '16000',  # Sample rate 16kHz
        '-ac', '1',      # Mono audio
        '-c:a', 'pcm_s16le',  # 16-bit PCM
        '-y',  # Overwrite output file
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Audio converted successfully: {Path(output_path).name}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Audio conversion failed: {e}")
        print(f"FFmpeg error: {e.stderr}")
        # Fall back to original file
        return str(input_path)
    except FileNotFoundError:
        print("⚠️  FFmpeg not found, using original audio file")
        return str(input_path)


def main():
    parser = argparse.ArgumentParser(description="Advanced transcription using WhisperX with improved speaker diarization")
    parser.add_argument("audio_file", nargs='?', help="Path to the audio file (MP3, WAV, etc.)")
    parser.add_argument("-o", "--output", help="Output markdown file path")
    parser.add_argument("-l", "--language", help="Language code (e.g., 'en', 'es', 'fr')")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda", 
                       help="Device to use for processing (default: cuda)")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"], 
                       default="large-v3", help="WhisperX model size (default: large-v3)")
    parser.add_argument("--diarization-model", 
                       default="pyannote/speaker-diarization-3.1",
                       help="Pyannote diarization model to use")
    parser.add_argument("--test-env", action="store_true", 
                       help="Test .env file loading and token validation")
    
    args = parser.parse_args()
    
    # Test environment loading if requested
    if args.test_env:
        if test_env_loading():
            print("✅ Environment test passed!")
            sys.exit(0)
        else:
            print("❌ Environment test failed!")
            sys.exit(1)
    
    # Check if audio file is provided
    if not args.audio_file:
        print("Error: Audio file path is required.")
        print("Use --test-env to test environment loading.")
        sys.exit(1)
    
    # Check if audio file exists
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file '{args.audio_file}' not found.")
        sys.exit(1)
    
    try:
        output_file = transcribe_audio_advanced(
            audio_path=args.audio_file,
            output_path=args.output,
            language=args.language,
            device=args.device,
            model_size=args.model,
            diarization_model=args.diarization_model
        )
        print(f"✅ Advanced transcription completed successfully!")
        print(f"📄 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during transcription: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 