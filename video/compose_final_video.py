import os
import shutil
import subprocess

def compose():
    base_dir = "/Volumes/DiskD/Devpost/Ma/video"
    raw_dir = os.path.join(base_dir, "raw_recordings")
    narration_audio = os.path.join(base_dir, "narration_full.mp3")
    final_video_2min = os.path.join(base_dir, "alexa_plus_swasth_ma_2min_demo.mp4")
    legacy_video = os.path.join(base_dir, "alexa_plus_swasth_ma_2_5min_demo.mp4")

    # Find the recorded webm file
    webms = [f for f in os.listdir(raw_dir) if f.endswith(".webm")]
    if not webms:
        raise RuntimeError("No raw recording found.")
    raw_video = os.path.join(raw_dir, webms[0])

    # Get narration duration
    res = subprocess.run([
        "/opt/homebrew/bin/ffprobe", "-i", narration_audio,
        "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ], capture_output=True, text=True)
    narration_duration = float(res.stdout.strip())
    print(f"Narration duration: {narration_duration:.2f}s")

    # Check video duration
    res_v = subprocess.run([
        "/opt/homebrew/bin/ffprobe", "-i", raw_video,
        "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ], capture_output=True, text=True)
    video_duration = float(res_v.stdout.strip())
    print(f"Raw video duration: {video_duration:.2f}s")

    # Generate 432 Hz gentle soothing ambient drone (warm, lowpass filtered, volume 0.035)
    ambient_audio = os.path.join(base_dir, "ambient_432hz.mp3")
    fade_out_start = max(0, narration_duration - 4)
    subprocess.run([
        "/opt/homebrew/bin/ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=432:sample_rate=48000:duration={narration_duration + 2}",
        "-af", f"lowpass=f=450,volume=0.035,afade=t=in:ss=0:d=3,afade=t=out:st={fade_out_start:.2f}:d=4",
        ambient_audio
    ], check=True)

    # Mix narration (1.0) with ambient (0.8)
    mixed_audio = os.path.join(base_dir, "mixed_audio.mp3")
    subprocess.run([
        "/opt/homebrew/bin/ffmpeg", "-y",
        "-i", narration_audio,
        "-i", ambient_audio,
        "-filter_complex", "[0:a]volume=1.0[v];[1:a]volume=0.8[a];[v][a]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        mixed_audio
    ], check=True)

    # Final composite: encode video with H.264, trim/pad to narration duration, add mixed audio
    video_fade_out = max(0, narration_duration - 3)
    print(f"Muxing final video to {final_video_2min}...")
    subprocess.run([
        "/opt/homebrew/bin/ffmpeg", "-y",
        "-i", raw_video,
        "-i", mixed_audio,
        "-vf", f"fade=t=in:st=0:d=1,fade=t=out:st={video_fade_out:.2f}:d=3",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_video_2min
    ], check=True)

    # Keep legacy file updated as well
    shutil.copyfile(final_video_2min, legacy_video)

    print(f"SUCCESS! 2-Minute broadcast-quality video rendered at: {final_video_2min}")
    size_mb = os.path.getsize(final_video_2min) / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")

if __name__ == "__main__":
    compose()
