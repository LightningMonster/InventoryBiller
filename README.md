# Billing and Inventory Management System

A comprehensive Windows-based billing and inventory management software designed for small to medium businesses, offering robust product tracking and financial management capabilities.

## Features

- **Graphical User Interface**: Built with Python Tkinter
- **Database Integration**: SQLite database for data storage
- **Product Management**: Add, edit, and delete products
- **Company Management**: Manage supplier/company records
- **Billing System**: Generate and print invoices
- **Low Stock Alerts**: Highlights products when inventory falls below critical levels
- **HSN Code Support**: Properly handles HSN codes for taxation
- **Report Generation**: Create and export reports
- **PDF Bills**: Generate professional bills in PDF format

## Installation

### Option 1: Run as Executable (Windows)

1. Download the latest release from the releases section
2. Unzip the package
3. Run `BillingApp.exe`

### Option 2: Run from Source Code

1. Ensure Python 3.x is installed
2. Install required packages:
   ```
   pip install tkcalendar reportlab
   ```
3. Run the application:
   ```
   python main.py
   ```

## Building the Executable

To build the executable version of the application:

1. Follow the instructions in `BUILD_INSTRUCTIONS.md`
2. Run the batch file: `build_exe.bat` (Windows) or `./build_exe.sh` (Linux/Mac)

## Usage

### Billing Module

1. Select a company from the dropdown
2. Select products to add to the bill
3. Specify quantities
4. Click "Add to Bill" to include items
5. Click "Finalize Bill" to generate and save the bill
6. Use "Print Bill" to get a physical printout

### Inventory Management

1. Navigate to the Inventory tab
2. Use "Add Product" to register new items
3. Edit or delete products using the context menu
4. Search functionality allows quick product lookup

### Low Stock Alerts

- Products with stock below 25% of total capacity are highlighted in red
- A warning icon (⚠️) appears next to low stock items

## Technical Details

- Built with Python Tkinter for GUI
- Uses SQLite for database operations
- Implements Report generation with ReportLab
- Date picking functionality with tkcalendar
- Packaged as executable with PyInstaller

## License

This software is proprietary and confidential.
Unauthorized copying, transfer or use is strictly prohibited.