import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QTextEdit, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal


def find_last_moov_offset(corrupt_data):
    try:
        # Find the last offset of 'moov' in the corrupt data
        last_moov_offset = -1
        offset = 0
        while True:
            offset = corrupt_data.find(b'moov', offset + 1)
            if offset == -1:
                break
            last_moov_offset = offset
        if last_moov_offset == -1:
            raise Exception("Cannot find 'moov' in the corrupt file.")

        # Adjust the offset to the end of the 'moov' box
        last_moov_offset += 4  # Adding the length of 'moov' box (4 bytes)

        return last_moov_offset

    except Exception as e:
        print("Error:", str(e))
        return None


def calculate_length_to_moov(corrupt_data, last_moov_offset):
    try:
        # Calculate the length from the last 'moov' to offset 8 from the start of the file
        length_to_offset_8 = last_moov_offset - 8

        print("Length from last 'moov' to offset 8 (in dec):", length_to_offset_8)
        return length_to_offset_8

    except Exception as e:
        print("Error:", str(e))
        return None


def repair_single_video(args, log_signal):
    corrupt_file_path, reference_file_path, output_directory = args

    try:
        # Read the reference file data
        with open(reference_file_path, 'rb') as reference_file:
            reference_data = reference_file.read()

        # Read the corrupt file data
        with open(corrupt_file_path, 'rb') as corrupt_file:
            corrupt_data = corrupt_file.read()

        # Get the base file name without extension
        file_name, _ = os.path.splitext(os.path.basename(corrupt_file_path))
        log_signal.emit(f"Processing {file_name}...")

        # Find the last 'moov' offset
        last_moov_offset = find_last_moov_offset(corrupt_data)
        if last_moov_offset is None:
            return

        # Calculate the length from the last 'moov' to offset 8 from the start of the file
        length_to_offset_8 = calculate_length_to_moov(corrupt_data, last_moov_offset)
        if length_to_offset_8 is None:
            return

        # Modify the corrupt file data
        length_to_moov_bytes = length_to_offset_8.to_bytes(8, byteorder='big')
        repaired_data = b'\x00\x00\x00\x01mdat' + length_to_moov_bytes + corrupt_data[16:]

        # Remove 334 bytes from the end of the repaired data
        repaired_data = repaired_data[:-334]

        # Create the repaired file name with the same extension as the original file
        repaired_file_name = file_name + ".mov"

        # Save the repaired file to the output directory with the same name
        repaired_file_path = os.path.join(output_directory, repaired_file_name)
        with open(repaired_file_path, 'wb') as repaired_file:
            repaired_file.write(repaired_data)

        print("File repaired and saved as:", repaired_file_path)

        # Remove the extension from the saved file if there is one
        base_name, _ = os.path.splitext(repaired_file_path)
        if os.path.exists(repaired_file_path):
            new_repaired_file_path = base_name
            os.rename(repaired_file_path, new_repaired_file_path)
            print("File renamed to:", new_repaired_file_path)

        log_signal.emit(f"{file_name} repaired.")

    except Exception as e:
        print("Error:", str(e))
        return None


def repair_files_in_directory(corrupted_folder_path, reference_file_path, output_directory, log_signal):
    try:
        # List all files in the corrupted folder
        corrupted_files = [
            f for f in os.listdir(corrupted_folder_path)
            if os.path.isfile(os.path.join(corrupted_folder_path, f))
        ]

        for corrupted_file in corrupted_files:
            # Get the full path to the corrupted file
            corrupt_file_path = os.path.join(corrupted_folder_path, corrupted_file)

            args = (corrupt_file_path, reference_file_path, output_directory)

            # Repair the video file
            repair_single_video(args, log_signal)

    except Exception as e:
        print("Error:", str(e))


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
        output_directory = os.path.join(encrypted_folder_path, "Repaired")

        try:
            # Create the output directory if it doesn't exist
            os.makedirs(output_directory, exist_ok=True)

            # Repair files in the corrupted folder
            repair_files_in_directory(encrypted_folder_path, reference_file_path, output_directory, self.log_updated)

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
