# Video-Repair-Tool

![Screenshot from 2024-05-03 09-15-21](https://github.com/DRCRecoveryData/Video-Repair-Tool/assets/85211068/92acaa17-f4dd-46fc-853b-476159ad5c8a)

![Build Status](https://img.shields.io/github/actions/workflow/status/DRCRecoveryData/Video-Repair-Tool/build.yml)
![License](https://img.shields.io/github/license/DRCRecoveryData/Video-Repair-Tool)
![Version](https://img.shields.io/github/v/release/DRCRecoveryData/Video-Repair-Tool)

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)
- [Contact](#contact)

## Overview

This Python script is tailored to fix corrupted MOV/MP4 files. It swaps out the header section with data from a reference file, allowing for the removal of specific bytes from the end of the corrupted file. This process ensures that MOV/MP4 video files maintain their integrity and remain usable.

## Installation

To install the Video-Repair-Tool:

1. Download the latest release from the [releases page](https://github.com/DRCRecoveryData/Video-Repair-Tool/releases).
2. Extract the contents to a directory.
3. Ensure you have Python installed. You can download it from [python.org](https://www.python.org/).
4. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. **Clone the repository**:
    ```bash
    git clone https://github.com/DRCRecoveryData/Video-Repair-Tool.git
    cd Video-Repair-Tool
    ```

2. **Run the script**:
    ```bash
    python video_repair_tool.py
    ```
    This will launch the tool where you can specify the necessary parameters.

3. **Specify the Reference File and Corrupted File**:
    - Use the tool's interface to select the reference MOV/MP4 file and the corrupted file.

4. **Click Start** to begin the repair process.

5. **Monitor Progress**:
    - The progress of the repair will be displayed in the terminal or GUI interface.
    - Upon completion, the repaired file will be saved to the specified directory.

## Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Submit a pull request.

For issues or suggestions, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [Python Programming Language](https://www.python.org/)
- [PyQt6 Library](https://pypi.org/project/PyQt6/)

## Contact

For support or questions, please contact us at [hanaloginstruments@gmail.com](mailto:hanaloginstruments@gmail.com)
