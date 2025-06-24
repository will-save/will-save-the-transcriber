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


def transcribe_audio_advanced_v1(audio_path, output_path=None, language=None, device="cuda", 
                                model_size="large-v3", diarization_model="pyannote/speaker-diarization-3.1",
                                num_speakers=None, min_speakers=1, max_speakers=20, include_word_timestamps=True):
    """
    Version 1: Advanced transcription with multiple model options and better diarization.
    
    Args:
        audio_path (str): Path to the audio file
        output_path (str): Path for the output markdown file
        language (str): Language code (e.g., 'en', 'es', 'fr')
        device (str): Device to use ('cuda' or 'cpu')
        model_size (str): WhisperX model size
        diarization_model (str): Pyannote diarization model to use
        num_speakers (int): Exact number of speakers (if known)
        min_speakers (int): Minimum number of speakers to detect
        max_speakers (int): Maximum number of speakers to detect
        include_word_timestamps (bool): Whether to include word-level timestamps in output
    
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
    
    # Transcribe audio with language parameter if provided
    print("Transcribing audio with advanced settings...")
    if language:
        print(f"Using specified language: {language}")
        result = model.transcribe(
            audio, 
            language=language,
            batch_size=16
        )
    else:
        print("No language specified, language will be first be detected for each audio file (increases inference time).")
        result = model.transcribe(
            audio, 
            batch_size=16
        )
    
    # Align whisper output with better parameters
    print("Aligning timestamps with high precision...")
    # Use specified language or detected language for alignment
    align_language = language if language else result["language"]
    model_a, metadata = whisperx.load_align_model(language_code=align_language, device=device)
    result = whisperx.align(
        result["segments"], 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=include_word_timestamps
    )
    
    # Advanced diarization with multiple fallback options
    print("Performing advanced speaker diarization...")
    hf_token = load_hf_token()
    
    # Analyze audio for optimal diarization parameters
    audio_analysis = analyze_audio_for_diarization(converted_audio_path)
    
    # Use provided parameters or fall back to analysis suggestions
    # Fix the logic: use provided parameters if they're not the defaults
    final_min_speakers = min_speakers if min_speakers != 4 else audio_analysis['min_speakers']
    final_max_speakers = max_speakers if max_speakers != 20 else audio_analysis['max_speakers']
    final_num_speakers = num_speakers if num_speakers is not None else audio_analysis['num_speakers']
    
    print(f"Using diarization parameters: min={final_min_speakers}, max={final_max_speakers}, exact={final_num_speakers}")
    
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
            # Prioritize latest models that are most compatible with current versions
            diarization_models = [
                "pyannote/speaker-diarization-3.1",  # Latest, most compatible with current versions
                "pyannote/speaker-diarization-2.1",  # Fallback option
                "pyannote/speaker-diarization"       # Original version
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
                            min_speakers=final_min_speakers,
                            max_speakers=final_max_speakers,
                            num_speakers=final_num_speakers,
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
                    
                    # Post-process diarization results for better accuracy
                    result = post_process_diarization(result, min_segment_duration=2.0)
                    
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
        output_path = f"{audio_name}_advanced_v1_transcript.md"
    
    # Write markdown output
    print(f"Writing transcript to: {output_path}")
    write_advanced_markdown_transcript(result, output_path, title=Path(audio_path).stem, include_word_timestamps=include_word_timestamps)
    
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


def write_advanced_markdown_transcript(result, output_path, title=None, include_word_timestamps=True):
    """
    Write transcription results to a markdown file with advanced formatting.
    
    Args:
        result (dict): WhisperX transcription result
        output_path (str): Path to output markdown file
        title (str): Title for the transcript (optional)
        include_word_timestamps (bool): Whether to include word-level timestamps in output
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header with title or default
        if title:
            f.write(f"# {title}\n\n")
        else:
            f.write("# Audio Transcription\n\n")
        
        # Fix language output - ensure we get the detected language properly
        detected_language = result.get('language', 'Unknown')
        if detected_language and detected_language != 'Unknown':
            f.write(f"**Language:** {detected_language}\n\n")
        else:
            f.write("**Language:** Unknown\n\n")
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
            
            # Write individual words with timestamps if available
            if "words" in segment and segment["words"] and include_word_timestamps:
                f.write("**Words:**\n")
                for word_info in segment["words"]:
                    word = word_info.get("word", "").strip()
                    word_start = word_info.get("start", 0)
                    word_end = word_info.get("end", 0)
                    
                    if word and word_start is not None and word_end is not None:
                        word_start_time = format_time(word_start)
                        word_end_time = format_time(word_end)
                        f.write(f"  - **[{word_start_time} - {word_end_time}]** {word}\n")
                f.write("\n")
        
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


def analyze_audio_for_diarization(audio_path):
    """
    Analyze audio file to suggest optimal diarization parameters.
    
    Args:
        audio_path (str): Path to the audio file
    
    Returns:
        dict: Suggested parameters for diarization
    """
    try:
        import librosa
        
        print("Analyzing audio for optimal diarization parameters...")
        
        # Load audio for analysis
        y, sr = librosa.load(audio_path, sr=None)
        duration = len(y) / sr
        
        # Calculate audio characteristics
        rms = librosa.feature.rms(y=y)[0]
        avg_volume = float(rms.mean())
        volume_variance = float(rms.var())
        
        # Detect silence regions
        silence_threshold = avg_volume * 0.1
        silence_regions = librosa.effects.split(y, top_db=20)
        silence_duration = sum([(end - start) / sr for start, end in silence_regions])
        speech_ratio = (duration - silence_duration) / duration
        
        print(f"Audio duration: {duration:.1f} seconds")
        print(f"Average volume: {avg_volume:.3f}")
        print(f"Volume variance: {volume_variance:.3f}")
        print(f"Speech ratio: {speech_ratio:.2f}")
        
        # Suggest parameters based on analysis
        suggestions = {
            'min_speakers': 4,
            'max_speakers': 20,
            'num_speakers': None
        }
        
        # Adjust based on duration
        if duration < 60:  # Short audio
            suggestions['max_speakers'] = 3
            print("Short audio detected - limiting to 3 speakers max")
        elif duration < 300:  # Medium audio
            suggestions['max_speakers'] = 5
            print("Medium audio detected - limiting to 5 speakers max")
        
        # Adjust based on speech ratio
        if speech_ratio < 0.3:
            print("Low speech ratio - may have background noise")
            suggestions['min_speakers'] = 1
        elif speech_ratio > 0.8:
            print("High speech ratio - dense conversation")
            suggestions['max_speakers'] = min(suggestions['max_speakers'], 8)
        
        # Adjust based on volume variance (indicates multiple speakers)
        if volume_variance > avg_volume * 0.5:
            print("High volume variance - likely multiple speakers")
            suggestions['min_speakers'] = 2
        else:
            print("Low volume variance - may be single speaker or similar voices")
        
        return suggestions
        
    except ImportError:
        print("⚠️  librosa not available for audio analysis")
        return {'min_speakers': 4, 'max_speakers': 20, 'num_speakers': None}
    except Exception as e:
        print(f"⚠️  Audio analysis failed: {e}")
        return {'min_speakers': 4, 'max_speakers': 20, 'num_speakers': None}


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


def post_process_diarization(result, min_segment_duration=1.0):
    """
    Post-process diarization results to improve speaker assignment.
    
    Args:
        result (dict): WhisperX transcription result with speaker labels
        min_segment_duration (float): Minimum duration for a speaker segment
    
    Returns:
        dict: Improved transcription result
    """
    print("Post-processing diarization results...")
    
    # Group segments by speaker
    speaker_segments = {}
    for segment in result["segments"]:
        speaker = segment.get("speaker", "Unknown")
        if speaker not in speaker_segments:
            speaker_segments[speaker] = []
        speaker_segments[speaker].append(segment)
    
    # Calculate total speaking time per speaker
    speaker_durations = {}
    for speaker, segments in speaker_segments.items():
        total_duration = sum(seg["end"] - seg["start"] for seg in segments)
        speaker_durations[speaker] = total_duration
    
    print(f"Detected speakers: {list(speaker_durations.keys())}")
    for speaker, duration in speaker_durations.items():
        print(f"  {speaker}: {duration:.1f}s")
    
    # Remove speakers with very short total duration
    filtered_speakers = {}
    for speaker, duration in speaker_durations.items():
        if duration >= min_segment_duration:
            filtered_speakers[speaker] = duration
        else:
            print(f"Removing {speaker} (too short: {duration:.1f}s)")
    
    # Reassign speaker labels if needed
    if len(filtered_speakers) != len(speaker_durations):
        # Create new speaker mapping
        new_speakers = list(filtered_speakers.keys())
        old_to_new = {}
        
        for old_speaker in speaker_durations.keys():
            if old_speaker in filtered_speakers:
                old_to_new[old_speaker] = old_speaker
            else:
                # Assign to the most similar speaker (by duration)
                best_match = min(new_speakers, key=lambda x: abs(speaker_durations[x] - speaker_durations[old_speaker]))
                old_to_new[old_speaker] = best_match
                print(f"Reassigning {old_speaker} -> {best_match}")
        
        # Update segments
        for segment in result["segments"]:
            old_speaker = segment.get("speaker", "Unknown")
            segment["speaker"] = old_to_new.get(old_speaker, old_speaker)
    
    # Rename speakers to be more user-friendly
    final_speakers = sorted(filtered_speakers.keys())
    speaker_rename = {}
    for i, speaker in enumerate(final_speakers):
        new_name = f"Speaker {i+1}"
        speaker_rename[speaker] = new_name
        print(f"Renaming {speaker} -> {new_name}")
    
    # Apply renaming
    for segment in result["segments"]:
        old_speaker = segment.get("speaker", "Unknown")
        segment["speaker"] = speaker_rename.get(old_speaker, old_speaker)
    
    print(f"Final speaker count: {len(final_speakers)}")
    return result


def check_version_compatibility():
    """
    Check version compatibility and provide specific recommendations for fixing issues.
    """
    print("🔍 Checking version compatibility for optimal diarization quality...")
    
    try:
        import torch
        import pyannote.audio
        import pytorch_lightning
        
        torch_version = torch.__version__
        pyannote_version = pyannote.audio.__version__
        lightning_version = pytorch_lightning.__version__
        
        print(f"   PyTorch: {torch_version}")
        print(f"   Pyannote Audio: {pyannote_version}")
        print(f"   PyTorch Lightning: {lightning_version}")
        
        # Define compatible version ranges for current environment
        compatible_versions = {
            'torch': ('2.0.0', '3.0.0'),  # Current stable range
            'pyannote_audio': ('3.0.0', '4.0.0'),  # Current stable range
            'pytorch_lightning': ('2.0.0', '3.0.0')  # Current stable range
        }
        
        issues = []
        recommendations = []
        
        # Check PyTorch compatibility
        torch_major, torch_minor = map(int, torch_version.split('.')[:2])
        if torch_major < 2:
            issues.append(f"PyTorch {torch_version} is older than recommended range {compatible_versions['torch'][0]}-{compatible_versions['torch'][1]}")
            recommendations.append("Consider upgrading: uv pip install 'torch>=2.0.0,<3.0.0' 'torchaudio>=2.0.0,<3.0.0'")
        
        # Check Pyannote Audio compatibility
        pyannote_major = int(pyannote_version.split('.')[0])
        if pyannote_major < 3:
            issues.append(f"Pyannote Audio {pyannote_version} is older than recommended range {compatible_versions['pyannote_audio'][0]}-{compatible_versions['pyannote_audio'][1]}")
            recommendations.append("Consider upgrading: uv pip install 'pyannote-audio>=3.0.0,<4.0.0'")
        
        # Check PyTorch Lightning compatibility
        lightning_major = int(lightning_version.split('.')[0])
        if lightning_major < 2:
            issues.append(f"PyTorch Lightning {lightning_version} is older than recommended range {compatible_versions['pytorch_lightning'][0]}-{compatible_versions['pytorch_lightning'][1]}")
            recommendations.append("Consider upgrading: uv pip install 'pytorch-lightning>=2.0.0,<3.0.0'")
        
        if issues:
            print("\n⚠️  Compatibility issues detected that may affect diarization quality:")
            for issue in issues:
                print(f"   • {issue}")
            
            print("\n🔧 Recommended fixes for optimal diarization quality:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
            
            print("\n💡 Alternative: Use compatible model versions")
            print("   • Try: pyannote/speaker-diarization-3.1 (latest, most compatible)")
            print("   • Or: pyannote/speaker-diarization-2.1 (fallback option)")
            
            print("\n❓ Continue anyway? (y/N): ", end="")
            response = input().strip().lower()
            if response != 'y':
                print("Exiting. Please fix compatibility issues first.")
                sys.exit(1)
            else:
                print("⚠️  Continuing with potential quality issues...")
        else:
            print("\n✅ All versions are compatible for optimal diarization quality!")
            print("   Using modern versions that work well together.")
        
        print()
        
    except ImportError as e:
        print(f"⚠️  Could not check all versions: {e}")
        print()


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
    parser.add_argument("--num-speakers", type=int, 
                       help="Exact number of speakers (if known)")
    parser.add_argument("--min-speakers", type=int, default=1,
                       help="Minimum number of speakers to detect (default: 1)")
    parser.add_argument("--max-speakers", type=int, default=20,
                       help="Maximum number of speakers to detect (default: 20)")
    parser.add_argument("--no-audio-analysis", action="store_true",
                       help="Skip audio analysis for diarization parameters")
    parser.add_argument("--test-env", action="store_true", 
                       help="Test .env file loading and token validation")
    parser.add_argument("-v", "--version", choices=["1", "2"], default="2",
                       help="Diarization version: 1 (original) or 2 (pyannote-audio docs approach) (default: 2)")
    parser.add_argument("--no-word-timestamps", action="store_true",
                       help="Disable word-level timestamps in output (faster processing)")
    
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
        # Check version compatibility first
        check_version_compatibility()
        
        # Print the parameters being used for transparency
        print(f"🔧 Using parameters:")
        print(f"   Model: {args.model}")
        print(f"   Language: {args.language or 'auto-detect'}")
        print(f"   Device: {args.device}")
        print(f"   Diarization version: {args.version}")
        print(f"   Min speakers: {args.min_speakers}")
        print(f"   Max speakers: {args.max_speakers}")
        print(f"   Exact speakers: {args.num_speakers or 'auto-detect'}")
        print(f"   Word timestamps: {'disabled' if args.no_word_timestamps else 'enabled'}")
        print()
        
        if args.version == "1":
            print("🎤 Using diarization version 1 (original approach)")
            output_file = transcribe_audio_advanced_v1(
                audio_path=args.audio_file,
                output_path=args.output,
                language=args.language,
                device=args.device,
                model_size=args.model,
                diarization_model=args.diarization_model,
                num_speakers=args.num_speakers,
                min_speakers=args.min_speakers,
                max_speakers=args.max_speakers,
                include_word_timestamps=not args.no_word_timestamps
            )
        else:
            print("🎤 Using diarization version 2 (pyannote-audio docs approach)")
            output_file = transcribe_audio_advanced_v2(
                audio_path=args.audio_file,
                output_path=args.output,
                language=args.language,
                device=args.device,
                model_size=args.model,
                diarization_model=args.diarization_model,
                num_speakers=args.num_speakers,
                min_speakers=args.min_speakers,
                max_speakers=args.max_speakers,
                title=Path(args.audio_file).stem,
                include_word_timestamps=not args.no_word_timestamps
            )
        
        print(f"✅ Advanced transcription completed successfully!")
        print(f"📄 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during transcription: {str(e)}")
        sys.exit(1)


def transcribe_audio_advanced_v2(audio_path, output_path=None, language=None, device="cuda", 
                                model_size="large-v3", diarization_model="pyannote/speaker-diarization-3.1",
                                num_speakers=None, min_speakers=4, max_speakers=20, title=None, include_word_timestamps=True):
    """
    Version 2: Advanced transcription using pyannote-audio documentation approach with itertracks.
    
    Args:
        audio_path (str): Path to the audio file
        output_path (str): Path for the output markdown file
        language (str): Language code (e.g., 'en', 'es', 'fr')
        device (str): Device to use ('cuda' or 'cpu')
        model_size (str): WhisperX model size
        diarization_model (str): Pyannote diarization model to use
        num_speakers (int): Exact number of speakers (if known)
        min_speakers (int): Minimum number of speakers to detect
        max_speakers (int): Maximum number of speakers to detect
        title (str): Title for the transcript (optional)
        include_word_timestamps (bool): Whether to include word-level timestamps in output
    
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
    
    # Transcribe audio with language parameter if provided
    print("Transcribing audio with advanced settings...")
    if language:
        print(f"Using specified language: {language}")
        result = model.transcribe(
            audio, 
            language=language,
            batch_size=16
        )
    else:
        print("No language specified, language will be first be detected for each audio file (increases inference time).")
        result = model.transcribe(
            audio, 
            batch_size=16
        )
    
    # Align whisper output with better parameters
    print("Aligning timestamps with high precision...")
    # Use specified language or detected language for alignment
    align_language = language if language else result["language"]
    model_a, metadata = whisperx.load_align_model(language_code=align_language, device=device)
    result = whisperx.align(
        result["segments"], 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=include_word_timestamps
    )
    
    # Advanced diarization with documentation approach (Version 2)
    print("Performing advanced speaker diarization (v2)...")
    hf_token = load_hf_token()
    
    # Analyze audio for optimal diarization parameters
    audio_analysis = analyze_audio_for_diarization(converted_audio_path)
    
    # Use provided parameters or fall back to analysis suggestions
    final_min_speakers = min_speakers if min_speakers != 4 else audio_analysis['min_speakers']
    final_max_speakers = max_speakers if max_speakers != 20 else audio_analysis['max_speakers']
    final_num_speakers = num_speakers if num_speakers is not None else audio_analysis['num_speakers']
    
    print(f"Using diarization parameters: min={final_min_speakers}, max={final_max_speakers}, exact={final_num_speakers}")
    
    if hf_token:
        # Validate the token first
        print("Validating Hugging Face token...")
        if not validate_hf_token(hf_token):
            print("❌ HF token validation failed. Please check your token and model access.")
            print("   Make sure you've accepted the terms for pyannote/speaker-diarization-3.1")
            hf_token = None
        
        if hf_token:
            diarization = None
            
            # Try multiple diarization models in order of preference
            diarization_models = [
                "pyannote/speaker-diarization-3.1",  # Latest, most compatible with current versions
                "pyannote/speaker-diarization-2.1",  # Fallback option
                "pyannote/speaker-diarization"       # Original version
            ]
            
            for model_name in diarization_models:
                try:
                    print(f"Trying diarization model: {model_name}")
                    print(f"Using HF token: {hf_token[:10]}...")
                    
                    # Use the documentation approach
                    pipeline = Pipeline.from_pretrained(
                        model_name,
                        use_auth_token=hf_token,
                        cache_dir=None  # Use default cache
                    )
                    
                    if pipeline is None:
                        print(f"⚠️  Failed to load {model_name} - pipeline is None")
                        continue
                        
                    # Send pipeline to GPU (when available)
                    pipeline.to(torch.device(device))
                    
                    # Apply pretrained pipeline with progress tracking
                    with ProgressHook() as hook:
                        diarization = pipeline(
                            converted_audio_path,
                            min_speakers=final_min_speakers,
                            max_speakers=final_max_speakers,
                            num_speakers=final_num_speakers,
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
            
            if diarization is not None:
                try:
                    # Process diarization results using itertracks (documentation approach)
                    print("Processing diarization results using itertracks...")
                    speaker_segments = []
                    
                    for turn, _, speaker in diarization.itertracks(yield_label=True):
                        speaker_segments.append({
                            'start': turn.start,
                            'end': turn.end,
                            'speaker': f"Speaker_{speaker}"
                        })
                    
                    print(f"✅ Found {len(speaker_segments)} speaker segments")
                    
                    # Assign speaker labels to WhisperX segments with advanced overlap detection
                    print("Assigning speaker labels to transcription segments...")
                    for segment in result["segments"]:
                        segment_start = segment["start"]
                        segment_end = segment["end"]
                        
                        # Find the speaker segment that overlaps most with this transcription segment
                        best_speaker = "Speaker_0"
                        max_overlap = 0
                        
                        for speaker_seg in speaker_segments:
                            # Calculate overlap
                            overlap_start = max(segment_start, speaker_seg['start'])
                            overlap_end = min(segment_end, speaker_seg['end'])
                            overlap = max(0, overlap_end - overlap_start)
                            
                            if overlap > max_overlap:
                                max_overlap = overlap
                                best_speaker = speaker_seg['speaker']
                        
                        segment["speaker"] = best_speaker
                    
                    print("✅ Speaker diarization (v2) completed successfully!")
                    
                    # Post-process diarization results for better accuracy
                    result = post_process_diarization(result, min_segment_duration=2.0)
                    
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
        output_path = f"{audio_name}_advanced_v2_transcript.md"
    
    # Write markdown output
    print(f"Writing transcript to: {output_path}")
    write_advanced_markdown_transcript(result, output_path, title=title, include_word_timestamps=include_word_timestamps)
    
    # Clean up
    del model
    del model_a
    if 'pipeline' in locals():
        del pipeline
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


if __name__ == "__main__":
    main() 