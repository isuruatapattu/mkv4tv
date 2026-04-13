# MyMkvExtractor

A powerful tool for converting and extracting MKV files optimized for TV playback. Select specific video, audio, and subtitle tracks from your MKV files and convert them to TV-compatible formats with ease.

## Features

- **Track Selection**: Choose specific video, audio, and subtitle tracks from MKV files
- **Audio Conversion**: Automatically convert audio tracks to E-AC-3 format for TV compatibility
- **Batch Processing**: Process multiple MKV files from a file list
- **Single File Mode**: Convert individual MKV files
- **Track Information**: Display all available tracks with codec and language information
- **Smart Warnings**: Alerts for non-TV-compatible codecs with conversion options
- **Customizable Output**: Specify destination folder for converted files

## Requirements

This tool requires the following to be installed and available in your system PATH:

- **Python 3.7+**: The main scripting language
- **MKVToolNix**: For MKV file manipulation
  - Specifically requires: `mkvmerge` and `mkvextract`
  - Download from: https://mkvtoolnix.download/
- **FFmpeg**: For audio/video encoding and conversion
  - Download from: https://ffmpeg.org/download.html

### Installation

1. **Install MKVToolNix**
   - Download and install from https://mkvtoolnix.download/
   - During installation, ensure tools are added to PATH

2. **Install FFmpeg**
   - Download from https://ffmpeg.org/download.html
   - Add FFmpeg's `bin` folder to your system PATH

3. **No Python dependencies** beyond the standard library

## Usage

### Basic Syntax

```powershell
python mkv4tv.py --dest <output_folder> [--file <mkv_file> | --filelist <file_list>]
```

### Command Line Arguments

- `--dest <folder>`: Destination folder for output MKV files (required)
- `--file <path>`: Single MKV file to convert (mutually exclusive with `--filelist`)
- `--filelist <path>`: Text file containing paths to MKV files, one per line (mutually exclusive with `--file`)

### Examples

**Convert a single MKV file:**
```powershell
python .\mkv4tv.py --dest G:\output --file "C:\videos\movie.mkv"
```

**Batch convert multiple MKV files:**
```powershell
python .\mkv4tv.py --dest G:\ --filelist movielist.f
```

**Using relative paths:**
```powershell
python .\mkv4tv.py --dest ..\output --filelist mylist.txt
```

## File List Format

Create a text file (e.g., `movielist.f`) with one MKV file path per line:

```
D:\Movies\Series\Episode01.mkv
D:\Movies\Series\Episode02.mkv
D:\Movies\Series\Episode03.mkv
```

**Notes:**
- Paths can be relative or absolute
- Empty lines and lines starting with `#` are ignored (for comments)
- Paths with spaces should be quoted in the file

## How It Works

1. **File Validation**: Checks that input files exist and are MKV format
2. **Track Discovery**: Reads all tracks from the MKV file using `mkvmerge -J`
3. **User Selection**: Displays available tracks and prompts you to select:
   - Video track (usually 1 choice)
   - Audio track (with codec compatibility warnings)
   - Subtitle track (with codec compatibility warnings)
4. **Audio Conversion** (if needed): Converts non-E-AC-3 audio to E-AC-3 using FFmpeg
5. **Merging**: Uses `mkvmerge` to combine selected tracks into a new MKV file
6. **Output**: Saves the result to the destination folder with the original filename

## Audio Codec Handling

The tool targets **E-AC-3** as the standard audio codec for TV compatibility:

- **Already E-AC-3**: Used as-is with no conversion
- **Other Codecs**: Tool warns you and offers to convert
  - `[c]onvert`: Converts to E-AC-3 at 640kbps
  - `[r]eselect`: Choose a different audio track
  - `[k]eep`: Use the track without conversion (default)

## Subtitle Codec Handling

The tool targets **SubRip/SRT** as the standard subtitle format:

- **Already SRT**: Used as-is with no conversion
- **Other Codecs**: Tool warns you
  - `[r]eselect`: Choose a different subtitle track
  - `[k]eep`: Use the track as-is (you can convert manually later)

## Configuration

## Example Workflow

```powershell
# 1. Create a file list
echo D:\series\episode1.mkv > episodes.txt
echo D:\series\episode2.mkv >> episodes.txt

# 2. Run the converter
python .\mkv4tv.py --dest G:\converted --filelist episodes.txt

# 3. When prompted, select tracks:
# Available tracks:
# Track ID    Codec                   Type        Language
# ----------------------------------------------------------------
# 0           H.265/HEVC              video       und
# 1           E-AC-3                  audio       eng
# 2           AC-3                    audio       spa
# 3           SubRip/SRT              subtitles   eng
#
# Enter video track ID [0]: 0
# Enter audio track ID [1, 2]: 1
# Enter subtitle track ID [3]: 3

# 4. Output files are saved to G:\converted\
```

## Troubleshooting

### "Command not found: mkvmerge"
- MKVToolNix is not installed or not in your system PATH
- Install MKVToolNix and add it to PATH
- Verify by running `mkvmerge --version` in PowerShell

### "Command not found: ffmpeg"
- FFmpeg is not installed or not in your system PATH
- Install FFmpeg and add its `bin` folder to PATH
- Verify by running `ffmpeg -version` in PowerShell

### "File does not exist: [path]"
- Check that the path in your file list is correct
- Use absolute paths if relative paths aren't resolving
- Verify file paths have proper quotes if they contain spaces

### "No tracks found"
- The MKV file may be corrupted
- Try running `mkvmerge -J "file.mkv"` directly to debug
- Try with a different MKV file

### Script exits with error after audio conversion
- Ensure FFmpeg and MKVToolNix are compatible versions
- Check that destination folder has write permissions
- Verify disk space is available

## Output

- **Success**: New MKV file saved to destination folder with selected tracks
- **Preserved metadata**: Original filename is retained
- **Temporary files**: Audio conversion temp files are cleaned up

## License

This project is provided as-is for personal use.