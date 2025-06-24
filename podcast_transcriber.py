#!/usr/bin/env python3
"""
Podcast RSS Feed Transcriber

This script parses the Will Save the Podcast RSS feed, downloads audio files,
and transcribes them using WhisperX. Episodes are organized by series with
readable titles and sanitized filenames.
"""

import os
import sys
import re
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
import hashlib
from typing import Dict, List, Optional
import argparse
import subprocess
import tempfile
from transcribe_advanced import transcribe_audio_advanced_v2


class PodcastTranscriber:
    def __init__(self, rss_url: str = "https://feed.podbean.com/willsavethepodcast/feed.xml"):
        self.rss_url = rss_url
        self.episodes_dir = Path("episodes")
        self.audio_dir = Path("audio")
        self.is_will_save_podcast = "willsavethepodcast" in rss_url.lower()
        self.series_title_map = {
            "willSaveTheTrailer": {"title": "Will Save the Trailer", "series": "Will Save the Podcast"},
            "book1": {"title": "Threefold Conspiracy Book 1", "series": "Will Save the Podcast"},
            "book2": {"title": "Threefold Conspiracy Book 2", "series": "Will Save the Podcast"},
            "book3": {"title": "Threefold Conspiracy Book 3", "series": "Will Save the Podcast"},
            "book4": {"title": "Threefold Conspiracy Book 4", "series": "Will Save the Podcast"},
            "book5": {"title": "Threefold Conspiracy Book 5", "series": "Will Save the Podcast"},
            "book6": {"title": "Threefold Conspiracy Book 6", "series": "Will Save the Podcast"},
            "unknownTreasures": {"title": "Unknown Treasures", "series": "Will Save and the Interstellar Tales from the Extra Galactic Adventure Anthology"},
            "nanoAdventure": {"title": "Nano Adventure", "series": "Will Save the Podcast"},
            "willSaveTheInterviews": {"title": "Will Save the Interviews", "series": "Will Save the Podcast"},
            "willSaveTheRecap": {"title": "Will Save the Recap", "series": "Will Save the Podcast"},
            "won'tSave": {"title": "Won't Save", "series": "Won't Save The Old Gods"},
        }
        
        # Create directories if they don't exist
        self.episodes_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing special characters and replacing spaces."""
        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces and other separators with underscores
        sanitized = re.sub(r'[\s\-_]+', '_', sanitized)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized.lower()
    
    def to_camel_case(self, text: str) -> str:
        """Convert text to camelCase (matching JavaScript logic)."""
        words = text.split()
        if not words:
            return ""
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def parse_series_key(self, title: str) -> str:
        """Parse series key from episode title (matching JavaScript logic)."""
        if title.startswith("Episode"):
            # This would be handled by the book counter logic
            return "book1"  # Default to book1 for now
        elif "Plot Armor" in title and "Unknown Treasures" not in title:
            if "Nano Adventure" not in title:
                return "book1"  # This would increment in the actual logic
            else:
                return "nanoAdventure"
        else:
            # Extract series title from beginning
            series_match = re.match(r'^([^—-]+)', title)
            if series_match:
                series_title = series_match.group(1).strip()
                return self.to_camel_case(series_title)
            else:
                return "unknown"
    
    def fetch_rss_feed(self) -> str:
        """Fetch RSS feed content."""
        print(f"📡 Fetching RSS feed from: {self.rss_url}")
        try:
            response = requests.get(self.rss_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error fetching RSS feed: {e}")
            sys.exit(1)
    
    def parse_rss(self, xml_content: str) -> List[Dict]:
        """Parse RSS XML and extract episode information."""
        print("🔍 Parsing RSS feed...")
        
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            print(f"❌ Error parsing XML: {e}")
            sys.exit(1)
        
        episodes = []
        
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else ""
            
            # Find enclosure (audio file)
            enclosure = item.find('enclosure')
            enclosure_url = enclosure.get('url') if enclosure is not None else ""
            
            if not enclosure_url:
                print(f"⚠️  Skipping episode '{title}' - no audio URL found")
                continue
            
            episodes.append({
                'title': title,
                'enclosure_url': enclosure_url,
                'series_key': self.parse_series_key(title)
            })
        
        print(f"✅ Found {len(episodes)} episodes")
        return episodes
    
    def organize_episodes_by_series(self, episodes: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize episodes by series (matching JavaScript logic for Will Save the Podcast)."""
        # For non-Will Save the Podcast feeds, put all episodes in a single series
        if not self.is_will_save_podcast:
            series = {"general": episodes}
            for i, episode in enumerate(episodes):
                episode['playlist_pos'] = i
            return series
        
        # Original logic for Will Save the Podcast
        series = {}
        book_counter = 1
        
        for i, episode in enumerate(episodes):
            title = episode['title']
            series_key = episode['series_key']
            
            # Apply the same logic as the JavaScript
            if title.startswith("Episode"):
                episode_match = re.match(r'^Episode (\d+)', title)
                series_key = f"book{book_counter}"
            elif "Plot Armor" in title and "Unknown Treasures" not in title:
                if "Nano Adventure" not in title:
                    book_counter += 1
                series_key = f"book{book_counter}"
            
            if series_key not in series:
                series[series_key] = []
            
            episode['playlist_pos'] = i
            series[series_key].append(episode)
        
        return series
    
    def download_audio(self, url: str, filename: str) -> Optional[Path]:
        """Download audio file."""
        audio_path = self.audio_dir / filename
        
        # Always download - don't skip if exists since we clean up after each episode
        print(f"⬇️  Downloading: {filename}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded: {filename}")
            return audio_path
            
        except requests.RequestException as e:
            print(f"❌ Error downloading {filename}: {e}")
            return None
    
    def get_series_directory(self, series_key: str) -> Path:
        """Get the directory path for a series."""
        # For non-Will Save the Podcast feeds, use a generic directory
        if not self.is_will_save_podcast:
            if series_key == "general":
                return self.episodes_dir
            else:
                # Fallback for any other series keys
                sanitized_key = self.sanitize_filename(series_key)
                return self.episodes_dir / sanitized_key
        
        # Original logic for Will Save the Podcast
        if series_key in self.series_title_map:
            series_title = self.series_title_map[series_key]["title"]
            sanitized_title = self.sanitize_filename(series_title)
            return self.episodes_dir / sanitized_title
        else:
            # Fallback for unknown series
            sanitized_key = self.sanitize_filename(series_key)
            return self.episodes_dir / sanitized_key
    
    def cleanup_episode_audio(self, audio_path: Path, wav_path: Path):
        """Clean up audio files for a specific episode."""
        try:
            # Clean up original audio file
            if audio_path.exists():
                audio_path.unlink()
                print(f"🗑️  Deleted: {audio_path.name}")
            
            # Clean up WAV file if it's different from the original
            if wav_path != audio_path and wav_path.exists():
                wav_path.unlink()
                print(f"🗑️  Deleted: {wav_path.name}")
                
        except Exception as e:
            print(f"⚠️  Error cleaning up episode audio files: {e}")
    
    def transcribe_episode(self, episode: Dict, audio_path: Path, wav_path: Path, series_dir: Path) -> bool:
        """Transcribe a single episode."""
        # Create sanitized filename
        sanitized_title = self.sanitize_filename(episode['title'])
        output_path = series_dir / f"{sanitized_title}.md"
        
        print(f"🎤 Transcribing: {episode['title']}")
        
        try:
            # Create series directory if it doesn't exist
            series_dir.mkdir(parents=True, exist_ok=True)
            
            # Transcribe using the advanced transcriber with version 2 diarization
            transcribe_audio_advanced_v2(
                audio_path=str(wav_path),
                output_path=str(output_path),
                language='en',  # Default to English for podcast episodes
                device='cuda' if self.check_cuda_available() else 'cpu',
                model_size='large-v3',
                min_speakers=1,
                max_speakers=10,
                num_speakers=None,
                title=episode['title']
            )
            
            print(f"✅ Transcribed: {output_path.name}")
            
            # Clean up audio files immediately after successful transcription
            self.cleanup_episode_audio(audio_path, wav_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Error transcribing {episode['title']}: {e}")
            # Clean up audio files even if transcription failed
            self.cleanup_episode_audio(audio_path, wav_path)
            return False
    
    def check_cuda_available(self) -> bool:
        """Check if CUDA is available for transcription."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def convert_audio_to_wav(self, input_path: Path) -> Path:
        """Convert audio file to WAV format with optimal parameters for WhisperX."""
        input_path = Path(input_path)
        
        # Create WAV file in the same directory as the original
        output_path = input_path.with_suffix('.wav')
        
        print(f"🔄 Converting {input_path.name} to WAV format...")
        
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
            print(f"✅ Audio converted successfully: {output_path.name}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Audio conversion failed: {e}")
            print(f"FFmpeg error: {e.stderr}")
            # Fall back to original file
            return input_path
        except FileNotFoundError:
            print("⚠️  FFmpeg not found, using original audio file")
            return input_path
    
    def cleanup_audio_files(self):
        """Clean up any remaining audio files (fallback method)."""
        print("🧹 Cleaning up any remaining audio files...")
        try:
            for audio_file in self.audio_dir.glob("*"):
                if audio_file.is_file():
                    audio_file.unlink()
                    print(f"🗑️  Deleted: {audio_file.name}")
        except Exception as e:
            print(f"⚠️  Error cleaning up audio files: {e}")
    
    def run(self, cleanup_audio: bool = True):
        """Main execution method."""
        if self.is_will_save_podcast:
            print("🎙️  Starting Will Save the Podcast Transcription Process")
        else:
            print("🎙️  Starting Podcast Transcription Process")
            print("⚠️  Note: This RSS feed is not Will Save the Podcast. Series organization may not work as expected.")
        print("=" * 50)
        
        # Fetch and parse RSS feed
        xml_content = self.fetch_rss_feed()
        episodes = self.parse_rss(xml_content)
        
        if not episodes:
            print("❌ No episodes found in RSS feed")
            return
        
        # Organize episodes by series
        series = self.organize_episodes_by_series(episodes)
        
        if self.is_will_save_podcast:
            print(f"\n📚 Found {len(series)} series:")
            for series_key, series_episodes in series.items():
                series_title = self.series_title_map.get(series_key, {}).get('title', series_key)
                print(f"  - {series_title}: {len(series_episodes)} episodes")
        else:
            print(f"\n📚 Found {len(episodes)} episodes (no series organization)")
        
        # Process each series
        total_episodes = 0
        processed_episodes = 0
        skipped_episodes = 0
        
        for series_key, series_episodes in series.items():
            series_dir = self.get_series_directory(series_key)
            
            if self.is_will_save_podcast:
                series_title = self.series_title_map.get(series_key, {}).get('title', series_key)
                print(f"\n📖 Processing series: {series_title}")
            else:
                print(f"\n📖 Processing episodes")
            print("-" * 40)
            
            for episode in series_episodes:
                total_episodes += 1
                
                # Check if transcript already exists before downloading
                sanitized_title = self.sanitize_filename(episode['title'])
                output_path = series_dir / f"{sanitized_title}.md"
                
                if output_path.exists():
                    print(f"⏭️  Skipping {episode['title']} - transcript already exists")
                    skipped_episodes += 1
                    continue
                
                # Generate filename for audio download
                file_extension = Path(urlparse(episode['enclosure_url']).path).suffix
                if not file_extension:
                    file_extension = '.mp3'  # Default extension
                
                audio_filename = f"{sanitized_title}{file_extension}"
                
                # Download audio
                audio_path = self.download_audio(episode['enclosure_url'], audio_filename)
                if not audio_path:
                    continue
                
                # Convert audio to WAV
                wav_path = self.convert_audio_to_wav(audio_path)
                
                # Transcribe episode (audio files are cleaned up within this method)
                if self.transcribe_episode(episode, audio_path, wav_path, series_dir):
                    processed_episodes += 1
        
        # Final cleanup as fallback (in case any files were missed)
        if cleanup_audio:
            self.cleanup_audio_files()
        
        print("\n" + "=" * 50)
        print(f"✅ Transcription complete!")
        print(f"📊 Processed {processed_episodes}/{total_episodes} episodes")
        print(f"⏭️  Skipped {skipped_episodes} episodes (already transcribed)")
        print(f"📁 Transcripts saved to: {self.episodes_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download and transcribe podcast episodes from RSS feed")
    parser.add_argument("--rss-url", default="https://feed.podbean.com/willsavethepodcast/feed.xml",
                       help="RSS feed URL (default: Will Save the Podcast feed)")
    parser.add_argument("--keep-audio", action="store_true",
                       help="Keep downloaded audio files (default: delete after transcription)")
    
    args = parser.parse_args()
    
    transcriber = PodcastTranscriber(args.rss_url)
    transcriber.run(cleanup_audio=not args.keep_audio)


if __name__ == "__main__":
    main() 