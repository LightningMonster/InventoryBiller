# Billing and Inventory Management System

A Windows desktop application for managing billing and inventory for retail businesses.

## Features

- **Billing System**: Create, manage, and print invoices for customers
- **Inventory Management**: Track products, batches, expiry dates, and stock levels
- **Company Management**: Save company details for product suppliers
- **Reporting**: View and generate sales reports by date range

## Installation

1. Ensure you have Python 3.x installed
2. Install required dependencies:
   ```
   pip install tkinter tkcalendar reportlab
   ```
3. Run the application:
   ```
   python main.py
   ```

## Creating an Executable

To convert this application to a standalone executable:

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Create the executable:
   ```
   pyinstaller --onefile --windowed main.py
   ```
3. Find the executable in the `dist` folder

## Usage

### Billing Tab
- Select a company and product
- Enter quantity and add to bill
- Add customer details
- Finalize and print bills

### Inventory Tab
- Add new companies and their details
- Add new products with all required information
- Search and manage existing inventory

### Reports Tab
- Select date range for sales report
- View bill history
- Print or export reports

## Development

This application uses:
- Python for core logic
- Tkinter for the GUI
- SQLite for database storage
- ReportLab for PDF generation

## License

This software is proprietary and intended for internal business use only.
