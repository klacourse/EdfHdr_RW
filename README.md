# EdfHdr_RW
A tool for viewing and repairing EDF (European Data Format) file headers.

## Features
- Read and parse EDF file headers.
- Modify specific fields in the EDF header.
- Validate and repair corrupted EDF headers.
- Write updated EDF headers back to the file.

## Prerequisites
- Python 3.10.9
- Required dependencies listed in `requirements.txt`.

## How to Set Up and Run the Tool
1. **Create a Python virtual environment**:
   ```bash
   python -m venv venv
   ```
2. **Activate the virtual environment**:
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the tool**:
   Navigate to the `src/main/python` directory and execute the main script:
   ```bash
   python main.py
   ```

## Directory Structure
```
EdfHdr_RW/
├── README.md
├── requirements.txt
├── src/
│   ├── main/
│   │   ├── python/
│   │   │   ├── CEAMS_edfLib.py
│   │   │   └── main.py
```

## Usage
- Use the `read_edf_header` function to read and parse the header of an EDF file.
- Use the `write_edf_hdr` function to modify and save changes to the EDF header.
- Refer to the `CEAMS_edfLib.py` file for additional utility functions.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact
For questions or support, contact:
**Karine Lacourse**  
Email: karine.lacourse.cnmtl@ssss.gouv.qc.ca




