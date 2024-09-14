import os
import subprocess
from pathlib import Path

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with error: {e}")

def process_files(corrupted_folder, repaired_folder, temp_folder, reference_file, recover_mp4_path, ffmpeg_path):
    # Create Repaired and Temp directories if not exist
    os.makedirs(repaired_folder, exist_ok=True)
    os.makedirs(temp_folder, exist_ok=True)

    # Step 1: Analyze the reference MP4 file
    print(f"Analyzing reference file: {reference_file}")
    analyze_command = f"{recover_mp4_path} {reference_file} --analyze"
    run_command(analyze_command)
    
    # Ensure audio.hdr and video.hdr files are created
    if not (Path("audio.hdr").exists() and Path("video.hdr").exists()):
        print("Error: audio.hdr or video.hdr not found after analysis. Exiting.")
        return
    
    # Step 2: Process corrupted MP4 files
    corrupted_files = [f for f in os.listdir(corrupted_folder) if f.endswith('.MP4')]
    
    for file in corrupted_files:
        base_name = Path(file).stem  # e.g., C0071
        corrupted_mp4_path = os.path.join(corrupted_folder, file)
        h264_path = os.path.join(temp_folder, f"{base_name}.h264")
        wav_path = os.path.join(temp_folder, f"{base_name}.wav")

        # Run recover_mp4 for each corrupted file
        print(f"Processing corrupted file: {file}")
        recover_command = f"{recover_mp4_path} {corrupted_mp4_path} {h264_path} {wav_path} --sony"
        run_command(recover_command)

        # Step 3: Use ffmpeg to merge the .h264 and .wav files into a repaired MP4
        output_mp4_path = os.path.join(repaired_folder, file)
        ffmpeg_command = f"{ffmpeg_path} -r 30000/1001 -i {h264_path} -i {wav_path} -c:v copy -c:a copy {output_mp4_path}"
        run_command(ffmpeg_command)

        print(f"Repaired file saved as: {output_mp4_path}")

if __name__ == "__main__":
    # Prompt for folder paths
    corrupted_folder = input("Enter the path to the Corrupted folder: ")
    repaired_folder = os.path.join(Path(corrupted_folder).parent, "Repaired")
    temp_folder = os.path.join(Path(corrupted_folder).parent, "Temp")
    reference_file = input("Enter the path to the reference MP4 file: ")
    
    # Paths to the tools (adjust these paths if needed)
    recover_mp4_path = "recover_mp4.exe"
    ffmpeg_path = "ffmpeg.exe"

    process_files(corrupted_folder, repaired_folder, temp_folder, reference_file, recover_mp4_path, ffmpeg_path)
