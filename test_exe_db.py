"""
Test script to verify executable database handling
"""
import os
import sys
import sqlite3
import tkinter as tk
from tkinter import messagebox

def test_database_path():
    # Determine if running as executable or script
    if getattr(sys, 'frozen', False):
        # Running as executable - use user's documents folder
        user_data_dir = os.path.join(os.path.expanduser("~"), "BillingApp")
        os.makedirs(user_data_dir, exist_ok=True)
        database_path = os.path.join(user_data_dir, "storage.db")
        
        # Also create a bills directory in the user data folder
        bills_dir = os.path.join(user_data_dir, "bills")
        os.makedirs(bills_dir, exist_ok=True)
        
        # Print paths for debugging
        print(f"Running as executable. Database path: {database_path}")
        print(f"Bills directory: {bills_dir}")
        
        # If database doesn't exist yet, look for a packaged one to copy
        if not os.path.exists(database_path):
            app_directory = os.path.dirname(sys.executable)
            packaged_db = os.path.join(app_directory, "storage.db")
            print(f"Looking for packaged database at: {packaged_db}")
            
            if os.path.exists(packaged_db):
                try:
                    import shutil
                    shutil.copy2(packaged_db, database_path)
                    print(f"Copied packaged database to {database_path}")
                except Exception as e:
                    print(f"Warning: Could not copy packaged database: {e}")
        
        is_executable = True
    else:
        # Running in development mode - use local directory
        app_directory = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(app_directory, "storage.db")
        print(f"Running in development mode. Database path: {database_path}")
        is_executable = False
    
    # Create empty database file if it doesn't exist
    if not os.path.exists(database_path):
        print(f"Creating new database at {database_path}")
        open(database_path, 'w').close()
    
    # Test database connection
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Create a test table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER NOT NULL
            )
        ''')
        
        # Insert a test record
        cursor.execute('''
            INSERT INTO test_table (name, value)
            VALUES (?, ?)
        ''', (f"Test Record {'EXE' if is_executable else 'DEV'}", 42))
        
        conn.commit()
        
        # Read back the records
        cursor.execute('SELECT * FROM test_table')
        records = cursor.fetchall()
        
        print("Database test results:")
        for record in records:
            print(f"  - {record}")
        
        conn.close()
        return True, database_path
    
    except Exception as e:
        print(f"Database test failed: {str(e)}")
        return False, str(e)

# Run test when script is executed directly
if __name__ == "__main__":
    success, result = test_database_path()
    
    if success:
        print("Database test successful!")
        # Show a GUI message if this is an executable
        if getattr(sys, 'frozen', False):
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            messagebox.showinfo("Database Test", f"Database test successful!\nPath: {result}")
    else:
        print(f"Database test failed: {result}")
        # Show error in GUI if this is an executable
        if getattr(sys, 'frozen', False):
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            messagebox.showerror("Database Test", f"Database test failed!\nError: {result}")