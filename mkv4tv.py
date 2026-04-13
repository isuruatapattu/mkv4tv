import os
import re
import subprocess
import sys
from pathlib import Path
import json
import argparse

from utils import *

# =========================
# SET YOUR FIXED DESTINATION HERE
# Use a Windows raw string: r"..."
# =========================

TARGET_AUDIO_CODEC = "E-AC-3"
TARGET_SUBTITLE_CODEC = "SubRip/SRT"

def main():
    print("MKV convertor for TV\n")
    parser = argparse.ArgumentParser(description="Provide MKV file path or filelist to convert.")
    parser.add_argument("--file",
        type=str,
        help="Single input file path"
    )
    parser.add_argument("--filelist",
        type=str,
        help="Path to a text file containing mkv file paths, one per line"
    )
    parser.add_argument("--dest",
        type=str,
        help="Destination folder for output files (overrides default in code)"
    )
    args = parser.parse_args()
    
    print(args.file)
    print(args.filelist)
    
    # Prevent user from giving both at the same time
    if args.file and args.filelist:
        print("[ERROR]: use either --input or --filelist, not both")
        sys.exit(1)
    
    # Require at least one of them
    if not (args.file or args.filelist):
        print("[ERROR]: provide either --input or --filelist")
        sys.exit(1)
    
    # Allow user to override destination folder via command line
    if args.dest:
        global DESTINATION_FOLDER
        DESTINATION_FOLDER = normalize_user_path(args.dest)
        os.makedirs(DESTINATION_FOLDER, exist_ok=True)
        print(f"Using destination folder: {DESTINATION_FOLDER}")
    else:
        print("[ERROR]: No destination folder provided. Use --dest to specify the output folder.")
        sys.exit(1)

    paths = get_paths(single_path=args.file, filelist_path=args.filelist)
    
    print (paths)
    
    tracks_extract_config = []
    
    for path in paths:
        print("=" * 80)
        print(f"Source : {path}")
        if not os.path.isfile(path):
            print(f"[ERROR]: file does not exist: {path}")
            continue
        elif not str(path).lower().endswith(".mkv"):
            print(f"[ERROR]: {path} is not an .mkv file.")
            continue
        
        tracks = get_tracks(path)
        
        print(tracks)
        
        if not tracks:
            print("[ERROR]: No tracks found or unable to parse mkvmerge output.")
            continue
        
        title           = Path(path).stem
        print(f"Title: {title}")
        video_ids       = get_track_ids_by_type(tracks, "video")
        audio_ids       = get_track_ids_by_type(tracks, "audio")
        subtitle_ids    = get_track_ids_by_type(tracks, "subtitles")
        
        if not video_ids:
            print("Error: No video tracks found.")
            sys.exit(1)

        if not audio_ids:
            print("Error: No audio tracks found.")
            sys.exit(1)

        if not subtitle_ids:
            print("Error: No subtitle tracks found.")
            sys.exit(1)
        
        video_track = prompt_for_track(f"Enter video track ID {video_ids}: ", video_ids)
        
        # Audio Track Safety Check and Optional Conversion Prompt
        while True:
            audio_track = prompt_for_track(f"Enter audio track ID {audio_ids}: ", audio_ids)
            if get_track_codec_by_id(tracks, audio_track) != "E-AC-3":
                print("[WARNING]: Selected audio codec may not be compatible with TV")
                audio_convert_choice = input("Choose: [c]onvert to E-AC-3, [r]eselect track, [k]eep as-is (default: k): ").strip().lower() or "k"
                if audio_convert_choice in ("c", "convert"):
                    convert_audio_to_eac3 = True
                    print("[INFO]: Audio will be converted to E-AC-3.")
                    break
                elif audio_convert_choice in ("r", "reselect"):
                    continue
                else:
                    print("[INFO]: Audio will not be converted to E-AC-3.")
                    break
            else:
                print("[INFO]: Selected audio track is already E-AC-3. No Conversion needed.")
                convert_audio_to_eac3 = False
                break
        
        # Subtitle Track Safety Check
        while True:
            subtitle_track  = prompt_for_track(f"Enter subtitle track ID {subtitle_ids}: ", subtitle_ids)
            if get_track_codec_by_id(tracks, subtitle_track) != "SubRip/SRT":
                print("[WARNING]: Selected subtitle codec may not be compatible with TV")
                subtitle_convert_choice = input("Choose: [r]eselect track, [k]eep as-is (default: k): ").strip().lower() or "k"
                if subtitle_convert_choice in ("r", "reselect"):
                    continue
                else:
                    print("[INFO]: Convert subtitles to SRT manually if needed. Keeping selected track as-is.")
                    break
            else:  
                print("[INFO]: Selected subtitle track is SRT. No Conversion needed.")
                break
                
        print("=" * 80)
        
        tracks_extract_config.append({
            "source_file": path,
            "title": title,
            "video_track": video_track,
            "audio_track": audio_track,
            "audio_convert": convert_audio_to_eac3 if 'convert_audio_to_eac3' in locals() else False,
            "subtitle_track": subtitle_track
        })
        
    print("\nConversion configuration:")
    for config in tracks_extract_config:
        print(f"\nTitle: {config['title']}")
        print(f"Source: {config['source_file']}")
        print(f"  Video Track ID: {config['video_track']}")
        print(f"  Audio Track ID: {config['audio_track']}")
        print(f"  Convert Audio to E-AC-3: {'Yes' if config['audio_convert'] else 'No'}")
        print(f"  Subtitle Track ID: {config['subtitle_track']}")
        
        # Audio track selection and conversion
        if (config['audio_convert']):
            # Create a temporary file for the converted audio
            temp_audio_path = Path(DESTINATION_FOLDER) / f"{config['title']}_temp_audio_{config['audio_track']}.{codec_to_extension(TARGET_AUDIO_CODEC, 'audio')}"
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", config['source_file'],
                "-vn", "-sn", "-dn",
                "-map", f"0:{config['audio_track']}",
                "-c:a", "eac3",
                "-b:a", "640k",
                str(temp_audio_path)
            ]
            run_command_live(ffmpeg_cmd)
            print(f"Audio converted and saved to: {temp_audio_path}")
            
            # Update the audio track in the mkvmerge command to use the converted file
            mkvmerge_cmd = [
                "mkvmerge",
                "-o", str(Path(DESTINATION_FOLDER) / f"{config['title']}.mkv"),
                
                "--no-audio",
                "--no-subtitles",
                "--video-tracks", str(config['video_track']),
                config['source_file'],
                
                "--audio-tracks", "0",
                "--language", "0:eng",
                "--track-name", "0:English EAC3",
                "--forced-track", "0:no",
                "--default-track", "0:yes",
                temp_audio_path,
            ]
        else:
            mkvmerge_cmd = [
                "mkvmerge",
                "-o", str(Path(DESTINATION_FOLDER) / f"{config['title']}.mkv"),
                "--video-tracks", str(config['video_track']),
                "--audio-tracks", str(config['audio_track']),
                "--default-track", f"{config['audio_track']}:yes",
                "--no-subtitles",
                config["source_file"],
            ]
            
        run_command_live(mkvmerge_cmd)
        
        # Subtitle extraction
        mkvextract_cmd = [
            "mkvextract",
            config["source_file"],
            "tracks",
            f"{config['subtitle_track']}:{Path(DESTINATION_FOLDER) / f'{config['title']}.{get_track_extension_by_id(tracks, config['subtitle_track'])}'}"
        ]
        run_command_live(mkvextract_cmd)
        print()
        
    
        

if __name__ == "__main__":
    main()