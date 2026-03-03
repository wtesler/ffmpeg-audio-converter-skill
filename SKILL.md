---
name: ffmpeg-audio-converter
description: "Audio conversion for movies using ffmpeg with fuzzy matching for metadata-heavy filenames."
metadata: {"openclaw": {"requires": {"bins": ["ffmpeg", "python3"]}}}
---

# Instructions
When the user asks to "convert" movie audio:

1. **Extraction & Sanitization**
   - Identify the **Movie Title** and the **Desired Format** (e.g., "eac3", "ac3", "mp3").
   - Extract any specific bitrate or channel preferences if provided (default to 640k if unspecified).

2. **Phase 1: Execution & Monitoring**
   - **ACTION:** Run the following command directly:
     `python3 {baseDir}/convert_audio.py "<Movie Title>" "<Format>"`
   - **AMBIGUITY:** If the script outputs "Multiple matches found", relay the numbered list to the user and ask them to select a number or provide a more specific title.
   - **MONITORING:** The script outputs progress in the format `Progress: X%`. Relay these updates to the user via Telegram (e.g., at 10%, 20%, etc.). 
   - **COMPLETION:** Once the output like `Conversion Complete: <path>` appears, send a final completion message via Telegram and proceed to Phase 2.
 
3. **Phase 2: Plex Library Refresh**
   - **ACTION:** Trigger the `scan-plex-skill` to scan for the new file.
   - **TELEGRAM:** Notify the user: "✅ **Plex Library Updated!**" once the scan is finished.

## Global Guardrails
- **PATH SAFETY:** Always use recursive walking to find files, as movies may be nested in folders like `Movies/Title/File.mkv`.
- **PRESERVATION:** Ensure video (`-c:v copy`) and subtitles (`-c:s copy`) are preserved without re-encoding to save time and quality.
