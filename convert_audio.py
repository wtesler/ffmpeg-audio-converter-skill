import os
import subprocess
import sys
import re
from pathlib import Path

def fuzzy_match(query, filename):
    """
    Simple fuzzy match: checks if all words in the query are present in the filename (case-insensitive).
    """
    # Clean query: remove special characters, handle dots/spaces
    query_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', query).lower()
    query_words = query_clean.split()
    
    # Clean filename: replace dots/hyphens with spaces for easier matching
    filename_clean = filename.lower().replace('.', ' ').replace('-', ' ')
    
    return all(word in filename_clean for word in query_words)

def find_movie(base_path, movie_title):
    """
    Recursively find a movie file matching the title in base_path.
    """
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.wmv'}
    
    matches = []
    
    # Handle the specific case where the path might not exist exactly as provided
    # but could be a drive letter or relative path.
    # For now, we use the provided path but add a fallback check.
    search_path = Path(base_path)
    if not search_path.exists():
        # Try to find a 'Videos' folder in any drive if the specific path fails?
        # For simplicity, we'll inform the user if it's missing, but let's try to be smart.
        print(f"DEBUG: Path {base_path} not found. Searching in current directory as fallback.")
        search_path = Path(".")

    for root, dirs, files in os.walk(search_path):
        for file in files:
            path = Path(file)
            if path.suffix.lower() in video_extensions:
                if fuzzy_match(movie_title, file):
                    matches.append(os.path.join(root, file))
    
    return matches

def get_duration_seconds(file_path):
    """
    Extract duration of input file using ffmpeg metadata output.
    """
    try:
        # ffmpeg -i without an output file prints file info to stderr and exits with error
        cmd = ["ffmpeg", "-i", str(file_path)]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        output = result.stderr
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", output)
        if match:
            hours, h_min, h_sec, h_ms = map(int, match.groups())
            return hours * 3600 + h_min * 60 + h_sec + h_ms / 100
    except Exception as e:
        print(f"DEBUG: Could not extract duration: {e}")
    return None

def time_to_seconds(time_str):
    """Convert HH:MM:SS.ms to total seconds."""
    try:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        pass
    return 0

def convert_audio(movie_path, output_format):
    """
    Executes ffmpeg to convert audio with progress monitoring.
    """
    path_obj = Path(movie_path)
    ext = path_obj.suffix
    stem = path_obj.stem
    output_path = str(path_obj.with_name(f"{stem}2{ext}"))
    
    total_duration = get_duration_seconds(movie_path)
    if total_duration:
        print(f"DEBUG: Total Duration: {total_duration:.2f} seconds")
    
    # Construct command:
    # ffmpeg -i <input> -c:v copy -c:a <format> -b:a 640k -c:s copy <output>
    # Adding -y to overwrite output if it exists (for safety)
    cmd = [
        "ffmpeg", "-y",
        "-i", movie_path,
        "-c:v", "copy",
        "-c:a", output_format,
        "-b:a", "640k",
        "-c:s", "copy",
        output_path
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        # We use -progress pipe:1 to get parseable progress, but ffmpeg stderr info is also useful.
        # Actually, simpler to just parse stderr lines which are standard.
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            bufsize=1
        )
        
        stderr = process.stderr
        if stderr is None:
            print("Error: Could not capture ffmpeg output.")
            return False

        # Track progress state in a dictionary to work around a linter bug (Pyre2)
        # where types of local variables are lost inside loop iterations.
        state = {
            "last_pct": -10,
            "duration": float(total_duration) if total_duration else 0.0
        }
        
        # FFmpeg prints progress to stderr
        while True:
            line = stderr.readline()
            if not line and process.poll() is not None:
                break
            
            if not line:
                continue
                
            # Search for time=HH:MM:SS.ms
            match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
            if match and state["duration"] > 0:
                current_time_str = match.group(1)
                current_seconds = time_to_seconds(current_time_str)
                
                # Calculate and clamp percentage
                raw_pct = (current_seconds / state["duration"]) * 100
                percentage = min(100, max(0, int(raw_pct)))
                
                if percentage >= state["last_pct"] + 10:
                    print(f"Progress: {percentage}%")
                    state["last_pct"] = (percentage // 10) * 10
        
        process.wait()
        if process.returncode == 0:
            print(f"Success! Created {output_path}")
            print(f"Conversion Complete: {output_path}")
            return True
        else:
            print(f"Error: FFmpeg exited with code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"Error during ffmpeg conversion: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_audio.py <MovieTitle> <Format> [BasePath]")
        sys.exit(1)
        
    movie_title = sys.argv[1]
    output_format = sys.argv[2]
    base_path = sys.argv[3] if len(sys.argv) > 3 else "/Volumes/External Storage/Videos"
    
    print(f"Searching for '{movie_title}' in {base_path}...")
    matches = find_movie(base_path, movie_title)
    
    if not matches:
        print(f"No matches found for '{movie_title}'.")
    elif len(matches) > 1:
        print("Multiple matches found. Please choose a number or be more specific:")
        for i, m in enumerate(matches, 1):
            print(f" [{i}] {m}")
    else:
        movie_path = matches[0]
        print(f"Found: {movie_path}")
        convert_audio(movie_path, output_format)
