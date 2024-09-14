import sys
import os
import subprocess
from pathlib import Path
import re
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal

def run_command(command):
    try:
        result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with error: {e}")
        return ""

def extract_framerate_and_filenames(output):
    # Regex to extract the framerate and the filenames for the .h264 and .wav
    framerate_match = re.search(r"-r\s([\d\.]+)", output)
    framerate = framerate_match.group(1) if framerate_match else None

    # Regex to extract the h264 and wav filenames from the output
    result_file_match = re.search(r"recover_mp4\.exe\s+\S+\s+(\S+)\s+(\S+)\s", output)
    h264_file, wav_file = result_file_match.groups() if result_file_match else (None, None)

    if framerate and h264_file and wav_file:
        print(f"Detected framerate: {framerate}")
        print(f"Detected .h264 output: {h264_file}")
        print(f"Detected .wav output: {wav_file}")
    else:
        print("Error: Could not extract necessary parameters from the log.")

    return framerate, h264_file, wav_file

def process_files(corrupted_folder, repaired_folder, temp_folder, reference_file, recover_mp4_path, ffmpeg_path, log_signal):
    # Create Repaired and Temp directories if they don't exist
    os.makedirs(repaired_folder, exist_ok=True)
    os.makedirs(temp_folder, exist_ok=True)

    # Step 1: Analyze the reference MP4 file
    log_signal.emit(f"Analyzing reference file: {reference_file}")
    analyze_command = f"{recover_mp4_path} {reference_file} --analyze"
    analyze_output = run_command(analyze_command)

    # Extract the framerate and .h264/.wav filenames from the analysis output
    framerate, h264_file_template, wav_file_template = extract_framerate_and_filenames(analyze_output)

    if not framerate or not h264_file_template or not wav_file_template:
        log_signal.emit("Error: Missing framerate or file templates. Exiting.")
        return

    # Ensure audio.hdr and video.hdr files are created
    if not (Path("audio.hdr").exists() and Path("video.hdr").exists()):
        log_signal.emit("Error: audio.hdr or video.hdr not found after analysis. Exiting.")
        return

    # Step 2: Process corrupted MP4 files
    corrupted_files = [f for f in os.listdir(corrupted_folder) if f.endswith('.MP4')]
    
    for file in corrupted_files:
        base_name = Path(file).stem  # e.g., C0071
        corrupted_mp4_path = os.path.join(corrupted_folder, file)
        h264_path = os.path.join(temp_folder, f"{base_name}.h264")
        wav_path = os.path.join(temp_folder, f"{base_name}.wav")

        # Run recover_mp4 for each corrupted file, dynamically generating the .h264 and .wav files
        log_signal.emit(f"Processing corrupted file: {file}")
        recover_command = f"{recover_mp4_path} {corrupted_mp4_path} {h264_path} {wav_path} --sony"
        run_command(recover_command)

        # Step 3: Use ffmpeg to merge the .h264 and .wav files into a repaired MP4
        output_mp4_path = os.path.join(repaired_folder, f"{base_name}.MP4")
        ffmpeg_command = f"{ffmpeg_path} -r {framerate} -i {h264_path} -i {wav_path} -c:v copy -c:a copy {output_mp4_path}"
        run_command(ffmpeg_command)

        log_signal.emit(f"Repaired file saved as: {output_mp4_path}")

class FileRepairWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    repair_finished = pyqtSignal(str)

    def __init__(self, reference_file_path, encrypted_folder_path):
        super().__init__()
        self.reference_file_path = reference_file_path
        self.encrypted_folder_path = encrypted_folder_path

    def run(self):
        reference_file_path = self.reference_file_path
        encrypted_folder_path = self.encrypted_folder_path
        repaired_folder = os.path.join(encrypted_folder_path, "Repaired")
        temp_folder = os.path.join(encrypted_folder_path, "Temp")
        recover_mp4_path = "recover_mp4.exe"  # Adjust if needed
        ffmpeg_path = "ffmpeg.exe"  # Adjust if needed

        try:
            process_files(encrypted_folder_path, repaired_folder, temp_folder, reference_file_path, recover_mp4_path, ffmpeg_path, self.log_updated)
            self.repair_finished.emit("Repaired files saved to the 'Repaired' folder.")

        except Exception as e:
            self.log_updated.emit(f"Error: {str(e)}")

class FileRepairApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Repair Tool")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        self.reference_label = QLabel("Reference File:")
        self.reference_path_edit = QLineEdit()
        self.reference_browse_button = QPushButton("Browse", self)
        self.reference_browse_button.setObjectName("browseButton")
        self.reference_browse_button.clicked.connect(self.browse_reference_file)

        self.encrypted_label = QLabel("Encrypted Folder:")
        self.encrypted_path_edit = QLineEdit()
        self.encrypted_browse_button = QPushButton("Browse", self)
        self.encrypted_browse_button.setObjectName("browseButton")
        self.encrypted_browse_button.clicked.connect(self.browse_encrypted_folder)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.repair_button = QPushButton("Repair", self)
        self.repair_button.setObjectName("blueButton")
        self.repair_button.clicked.connect(self.repair_files)

        layout.addWidget(self.reference_label)
        layout.addWidget(self.reference_path_edit)
        layout.addWidget(self.reference_browse_button)
        layout.addWidget(self.encrypted_label)
        layout.addWidget(self.encrypted_path_edit)
        layout.addWidget(self.encrypted_browse_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_box)
        layout.addWidget(self.repair_button)

        self.setLayout(layout)

        self.setStyleSheet("""
        #browseButton, #blueButton {
            background-color: #3498db;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 4px;
        }
        #browseButton:hover, #blueButton:hover {
            background-color: #2980b9;
        }
        """)

    def browse_reference_file(self):
        reference_file, _ = QFileDialog.getOpenFileName(self, "Select Reference File", "", "All Files (*)")
        if reference_file:
            self.reference_path_edit.setText(reference_file)

    def browse_encrypted_folder(self):
        encrypted_folder = QFileDialog.getExistingDirectory(self, "Select Encrypted Folder")
        if encrypted_folder:
            self.encrypted_path_edit.setText(encrypted_folder)

    def repair_files(self):
        reference_file_path = self.reference_path_edit.text()
        encrypted_folder_path = self.encrypted_path_edit.text()

        if not os.path.exists(reference_file_path):
            self.show_message("Error", "Reference file does not exist.")
            return
        if not os.path.exists(encrypted_folder_path):
            self.show_message("Error", "Encrypted folder does not exist.")
            return

        self.worker = FileRepairWorker(reference_file_path, encrypted_folder_path)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_updated.connect(self.update_log)
        self.worker.repair_finished.connect(self.repair_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_box.append(message)

    def repair_finished(self, message):
        self.show_message("Success", message)

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileRepairApp()
    window.show()
    sys.exit(app.exec())
