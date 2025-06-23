#!/usr/bin/env python3
"""
Simple transcription script using WhisperX with basic speaker diarization.
Two versions available: v1 (original) and v2 (pyannote-audio documentation approach).
"""

import argparse
import os
import sys
from pathlib import Path
import whisperx
import torch
import gc
from pyannote.audio import Pipeline
from dotenv import load_dotenv
import subprocess
import tempfile


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


def load_hf_token():
    """
    Load Hugging Face token from .env file or environment variable.
    
    Returns:
        str: Hugging Face token or None if not found
    """
    # Load from .env file
    load_dotenv()
    
    # Try to get token from environment
    hf_token = os.getenv("HF_TOKEN")
    
    if not hf_token:
        print("⚠️  Warning: HF_TOKEN not found in .env file or environment variables.")
        print("   Speaker diarization requires a Hugging Face token.")
        print("   Please create a .env file with: HF_TOKEN=your_token_here")
        print("   Or set the environment variable: export HF_TOKEN=your_token_here")
        return None
    
    return hf_token


def transcribe_audio_simple_v1(audio_path, output_path=None, language=None, device="cuda", model_size="large-v3"):
    """
    Version 1: Original transcription with WhisperX speaker diarization.
    
    Args:
        audio_path (str): Path to the audio file
        output_path (str): Path for the output markdown file
        language (str): Language code (e.g., 'en', 'es', 'fr')
        device (str): Device to use ('cuda' or 'cpu')
        model_size (str): WhisperX model size
    
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
    
    # Load WhisperX model
    print(f"Loading WhisperX model: {model_size}")
    compute_type = "float16" if device == "cuda" else "float32"
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    
    # Transcribe audio
    print("Transcribing audio...")
    result = model.transcribe(
        audio, 
        batch_size=16
    )
    
    # Align whisper output
    print("Aligning timestamps...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    
    # Diarize using pyannote.audio (Version 1)
    print("Performing speaker diarization (v1)...")
    hf_token = load_hf_token()
    
    if hf_token:
        try:
            diarize_model = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            diarize_model.to(torch.device(device))
            
            # Run diarization
            print("Running diarization pipeline...")
            diarize_segments = diarize_model(
                audio_path,
                min_speakers=1,
                max_speakers=10,
                num_speakers=None
            )
            
            # Assign speaker labels
            print("Assigning speaker labels...")
            result = whisperx.assign_word_speakers(diarize_segments, result)
            print("✅ Speaker diarization completed successfully!")
            
        except Exception as e:
            print(f"⚠️  Warning: Speaker diarization failed: {str(e)}")
            print("   Continuing with transcription without speaker labels...")
            for segment in result["segments"]:
                segment["speaker"] = "Speaker 0"
    else:
        print("⚠️  Skipping speaker diarization due to missing HF_TOKEN")
        for segment in result["segments"]:
            segment["speaker"] = "Speaker 0"
    
    # Generate output filename if not provided
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_v1_transcript.md"
    
    # Write markdown output
    print(f"Writing transcript to: {output_path}")
    write_markdown_transcript(result, output_path)
    
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


def transcribe_audio_simple_v2(audio_path, output_path=None, language=None, device="cuda", model_size="large-v3"):
    """
    Version 2: Transcription using pyannote-audio documentation approach with itertracks.
    
    Args:
        audio_path (str): Path to the audio file
        output_path (str): Path for the output markdown file
        language (str): Language code (e.g., 'en', 'es', 'fr')
        device (str): Device to use ('cuda' or 'cpu')
        model_size (str): WhisperX model size
    
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
    
    # Load WhisperX model
    print(f"Loading WhisperX model: {model_size}")
    compute_type = "float16" if device == "cuda" else "float32"
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    
    # Transcribe audio
    print("Transcribing audio...")
    result = model.transcribe(
        audio, 
        batch_size=16
    )
    
    # Align whisper output
    print("Aligning timestamps...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    
    # Diarize using pyannote.audio (Version 2 - documentation approach)
    print("Performing speaker diarization (v2)...")
    hf_token = load_hf_token()
    
    if hf_token:
        try:
            # Use the documentation approach
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            
            # Send pipeline to GPU (when available)
            pipeline.to(torch.device(device))
            
            # Apply pretrained pipeline
            print("Running diarization pipeline (v2)...")
            diarization = pipeline(converted_audio_path)
            
            # Process diarization results using itertracks
            print("Processing diarization results...")
            speaker_segments = []
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': f"Speaker_{speaker}"
                })
            
            print(f"✅ Found {len(speaker_segments)} speaker segments")
            
            # Assign speaker labels to WhisperX segments
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
            
        except Exception as e:
            print(f"⚠️  Warning: Speaker diarization failed: {str(e)}")
            print("   Continuing with transcription without speaker labels...")
            for segment in result["segments"]:
                segment["speaker"] = "Speaker 0"
    else:
        print("⚠️  Skipping speaker diarization due to missing HF_TOKEN")
        for segment in result["segments"]:
            segment["speaker"] = "Speaker 0"
    
    # Generate output filename if not provided
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_v2_transcript.md"
    
    # Write markdown output
    print(f"Writing transcript to: {output_path}")
    write_markdown_transcript(result, output_path)
    
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


def write_markdown_transcript(result, output_path):
    """
    Write transcription results to a markdown file with speaker diarization.
    
    Args:
        result (dict): WhisperX transcription result
        output_path (str): Path to output markdown file
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# Audio Transcription\n\n")
        f.write(f"**Language:** {result.get('language', 'Unknown')}\n\n")
        f.write("---\n\n")
        
        # Write segments with speaker labels
        current_speaker = None
        
        for segment in result["segments"]:
            speaker = segment.get("speaker", "Unknown")
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            text = segment["text"].strip()
            
            # Add speaker header if speaker changes
            if speaker != current_speaker:
                f.write(f"\n## {speaker}\n\n")
                current_speaker = speaker
            
            # Write segment with timestamp
            f.write(f"**[{start_time} - {end_time}]** {text}\n\n")
        
        # Write summary
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
        
        # Add confidence scores if available
        if result["segments"] and "avg_logprob" in result["segments"][0]:
            avg_confidence = sum(seg.get("avg_logprob", 0) for seg in result["segments"]) / len(result["segments"])
            f.write(f"- **Average confidence:** {avg_confidence:.2f}\n")


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


def main():
    parser = argparse.ArgumentParser(description="Simple transcription using WhisperX with speaker diarization")
    parser.add_argument("audio_file", help="Path to the audio file (MP3, WAV, etc.)")
    parser.add_argument("-o", "--output", help="Output markdown file path")
    parser.add_argument("-l", "--language", help="Language code (e.g., 'en', 'es', 'fr')")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda", 
                       help="Device to use for processing (default: cuda)")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"], 
                       default="large-v3", help="WhisperX model size (default: large-v3)")
    parser.add_argument("-v", "--version", choices=["1", "2"], default="2",
                       help="Diarization version: 1 (original) or 2 (pyannote-audio docs approach) (default: 2)")
    
    args = parser.parse_args()
    
    # Check if audio file exists
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file '{args.audio_file}' not found.")
        sys.exit(1)
    
    try:
        if args.version == "1":
            print("🎤 Using diarization version 1 (original approach)")
            output_file = transcribe_audio_simple_v1(
                audio_path=args.audio_file,
                output_path=args.output,
                language=args.language,
                device=args.device,
                model_size=args.model
            )
        else:
            print("🎤 Using diarization version 2 (pyannote-audio docs approach)")
            output_file = transcribe_audio_simple_v2(
                audio_path=args.audio_file,
                output_path=args.output,
                language=args.language,
                device=args.device,
                model_size=args.model
            )
        
        print(f"✅ Transcription completed successfully!")
        print(f"📄 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during transcription: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 