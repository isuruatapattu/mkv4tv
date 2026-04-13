import os
import re
import subprocess
import sys
from pathlib import Path
import json


def run_command_capture(command):
    """Execute a command (no shell), return stdout text, and print diagnostics before exiting on failures."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            shell=False
        )
        return result.stdout
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}")
        print("Make sure MKVToolNix is installed and mkvmerge/mkvextract are in PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("Command failed:")
        print(" ".join(command))
        if e.stdout:
            print("\nSTDOUT:")
            print(e.stdout)
        if e.stderr:
            print("\nSTDERR:")
            print(e.stderr)
        sys.exit(1)
          
def run_command_live(command):
    """Run command and show live output/progress in terminal."""
    try:
        process = subprocess.Popen(command)
        process.wait()
        if process.returncode != 0:
            print(f"\nCommand failed with exit code {process.returncode}:")
            print(" ".join(map(str, command)))
            sys.exit(process.returncode)
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}")
        print("Make sure MKVToolNix is installed and mkvmerge/mkvextract are in PATH.")
        sys.exit(1)
        
def normalize_user_path(path_str):
    """Remove wrapping quotes and normalize path."""
    path_str = path_str.strip().strip('"').strip("'")
    return os.path.normpath(path_str)

def get_paths(single_path: str = None, filelist_path: str = None):
    """
    Return a list of Path objects from either:
    - a single path
    - a file containing multiple paths
    """
    paths = []

    if single_path:
        paths.append(str(os.path.normpath(single_path)))

    elif filelist_path:
        filelist = Path(filelist_path).expanduser()

        if not filelist.exists():
            print(f"Error: file list does not exist: {filelist}")
            sys.exit(1)

        with filelist.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                paths.append(str(os.path.normpath(line)))

    else:
        print("Error: provide either --input or --filelist")
        sys.exit(1)
        
    print(paths)

    return paths

def codec_to_extension(codec: str, track_type: str) -> str | None:
    """
    Return the file extension for a given codec and track type.

    track_type: "audio" or "subtitles"
    """
    codec_map = {
        "audio": {
            "E-AC-3": "eac3",
            "TrueHD Atmos": "thd",
            "TrueHD": "thd",
            "AC-3": "ac3",
            "AAC": "aac",
            "DTS": "dts",
            "DTS-HD MA": "dts",
            "FLAC": "flac",
        },
        "subtitles": {
            "SubRip/SRT": "srt",
            "HDMV PGS": "sup",
            "PGS": "sup",
            "ASS": "ass",
            "SSA": "ssa",
        },
    }

    return codec_map.get(track_type.lower(), {}).get(codec)

def get_tracks(mkv_file):
    """Get track list from `mkvmerge -J`, print it, and return it for later use."""
    output = run_command_capture(["mkvmerge", "-J", mkv_file])
    data = json.loads(output)

    tracks = []
    for track in data.get("tracks", []):
        track_info = {
            "id": track.get("id"),
            "codec": track.get("codec", ""),
            "extension": codec_to_extension(track.get("codec", ""), track.get("type", "")),
            "type": track.get("type", "").strip().lower(),
            "language": track.get("properties", {}).get("language", "und")
        }
        tracks.append(track_info)

    print("\nAvailable tracks:\n")
    print(f"{'Track ID':<10} {'Type':<12} {'Codec':<30} {'Extension':<12} {'Language':<10}")
    print("-" * 80)
    for t in tracks:
        track_id = t.get("id", "")
        codec = t.get("codec", "")
        extension = t.get("extension") or "N/A"
        track_type = t.get("type", "")
        language = t.get("language", "")

        print(f"{track_id:<10} {track_type:<12} {codec:<30} {extension:<12} {language:<10}")
    print()

    return tracks

def get_track_ids_by_type(tracks, track_type):
    return [t["id"] for t in tracks if t["type"] == track_type]

def get_track_codec_by_id(tracks, track_id):
    for t in tracks:
        if t["id"] == track_id:
            return t["codec"]
    return None

def get_track_extension_by_id(tracks, track_id):
    for t in tracks:
        if t["id"] == track_id:
            return t["extension"]
    return None

def prompt_for_track(prompt_text, valid_ids):
    while True:
        value = input(prompt_text).strip()
        if value.isdigit() and int(value) in valid_ids:
            return int(value)
        print(f"Invalid selection. Choose from: {valid_ids}")
        
def ensure_destination_exists(destination_folder):
    """Create destination folder if it does not exist."""
    os.makedirs(destination_folder, exist_ok=True)
    
