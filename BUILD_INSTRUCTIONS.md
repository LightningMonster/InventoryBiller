# Building the Billing App Executable

This document provides instructions on how to build an executable (.exe) file from the BillingApp Python application.

## Prerequisites

- Windows operating system (for creating a Windows .exe)
- Python 3.x installed
- Required Python packages: pyinstaller, tkcalendar, reportlab, etc.

## Steps to Build the Executable

### Option 1: Using the Batch File (Windows)

1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run the batch file by typing:
   ```
   build_exe.bat
   ```
4. Wait for the build process to complete
5. The executable will be created in the `dist` folder as `BillingApp.exe`

### Option 2: Using PyInstaller Directly

1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run the following command:
   ```
   pyinstaller --clean billing_app.spec
   ```
4. The executable will be created in the `dist` folder as `BillingApp.exe`

## Running the Application

After building, you can run the application by:

1. Navigating to the `dist` folder
2. Double-clicking `BillingApp.exe`

## Distribution

To distribute the application to other computers:

1. Copy the entire `dist/BillingApp` folder
2. The application can be run on any Windows computer without requiring Python installation

## Troubleshooting

If you encounter issues:

1. Ensure all dependencies are installed: `pip install pyinstaller tkcalendar reportlab`
2. Check the PyInstaller spec file (`billing_app.spec`) for correct configuration
3. Run PyInstaller with the debug flag to get more information:
   ```
   pyinstaller --clean --debug all billing_app.spec
   ```

## Notes

- The executable will include the SQLite database file (`storage.db`)
- The application will create a `bills` folder for storing generated PDFs if it doesn't exist
- All dependencies are bundled into the executable, so users don't need to install Python