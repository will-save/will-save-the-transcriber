#!/usr/bin/env python3
"""
Simple transcription script using WhisperX with high-quality transcription.
Focuses on transcription quality without complex diarization requirements.
"""

import argparse
import os
import sys
from pathlib import Path
import whisperx
import torch
import gc
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


def transcribe_audio_simple(audio_path, output_path=None, language=None, device="cuda", model_size="large-v3"):
    """
    Simple transcription with high quality, no complex diarization.
    
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
    
    # Load WhisperX model with optimal settings
    print(f"Loading WhisperX model: {model_size}")
    compute_type = "float16" if device == "cuda" else "float32"
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    
    # Transcribe audio with high quality settings
    print("Transcribing audio with high quality settings...")
    result = model.transcribe(
        audio, 
        batch_size=16
    )
    
    # Align whisper output for better timestamps
    print("Aligning timestamps for precision...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(
        result["segments"], 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=False
    )
    
    # Add simple speaker labels (all as one speaker for now)
    print("Adding basic speaker labels...")
    for segment in result["segments"]:
        segment["speaker"] = "Speaker"
    
    # Generate output filename if not provided
    if output_path is None:
        audio_name = Path(audio_path).stem
        output_path = f"{audio_name}_simple_transcript.md"
    
    # Write markdown output
    print(f"Writing transcript to: {output_path}")
    write_simple_markdown_transcript(result, output_path)
    
    # Clean up
    del model
    del model_a
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


def write_simple_markdown_transcript(result, output_path):
    """
    Write transcription results to a markdown file with simple formatting.
    
    Args:
        result (dict): WhisperX transcription result
        output_path (str): Path to output markdown file
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# High-Quality Audio Transcription\n\n")
        f.write(f"**Language:** {result.get('language', 'Unknown')}\n\n")
        f.write("---\n\n")
        
        # Write segments with timestamps
        for i, segment in enumerate(result["segments"]):
            start_time = format_time(segment["start"])
            end_time = format_time(segment["end"])
            text = segment["text"].strip()
            confidence = segment.get("avg_logprob", 0)
            
            # Write segment with timestamp and confidence
            confidence_str = f" (confidence: {confidence:.2f})" if confidence != 0 else ""
            f.write(f"**[{start_time} - {end_time}]{confidence_str}** {text}\n\n")
        
        # Write comprehensive summary
        f.write("---\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total segments:** {len(result['segments'])}\n")
        f.write(f"- **Duration:** {format_time(result['segments'][-1]['end'] if result['segments'] else 0)}\n")
        
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


def main():
    parser = argparse.ArgumentParser(description="Simple high-quality transcription using WhisperX")
    parser.add_argument("audio_file", help="Path to the audio file (MP3, WAV, etc.)")
    parser.add_argument("-o", "--output", help="Output markdown file path")
    parser.add_argument("-l", "--language", help="Language code (e.g., 'en', 'es', 'fr')")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda", 
                       help="Device to use for processing (default: cuda)")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"], 
                       default="large-v3", help="WhisperX model size (default: large-v3)")
    
    args = parser.parse_args()
    
    # Check if audio file exists
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file '{args.audio_file}' not found.")
        sys.exit(1)
    
    try:
        output_file = transcribe_audio_simple(
            audio_path=args.audio_file,
            output_path=args.output,
            language=args.language,
            device=args.device,
            model_size=args.model
        )
        print(f"✅ Simple transcription completed successfully!")
        print(f"📄 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during transcription: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 