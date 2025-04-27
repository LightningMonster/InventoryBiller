import os
import sys
import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_base_path():
    """Get base path for application data"""
    try:
        if getattr(sys, 'frozen', False):
            # If running as exe
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # If running as script
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return base_dir
    except Exception:
        return os.getcwd()

def initialize_database():
    """Initialize database with required tables"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create customers table with created_at column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile TEXT UNIQUE NOT NULL,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                address TEXT,
                gst_number TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dom TEXT NOT NULL,
                expiry TEXT NOT NULL,
                batch_no TEXT UNIQUE NOT NULL,
                mrp REAL NOT NULL,
                discount REAL DEFAULT 0,
                hsn_code TEXT,
                units INTEGER NOT NULL,
                rate REAL NOT NULL,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # Create bills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_mobile TEXT NOT NULL,
                customer_address TEXT,
                bill_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                bill_items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

def migrate_database():
    """Add missing columns to existing tables"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if created_at column exists in customers table
        cursor.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in columns:
            cursor.execute('''
                ALTER TABLE customers 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ''')
            
        conn.commit()
        conn.close()
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database migration error: {str(e)}")
        return False

# Define paths
BASE_DIR = get_base_path()
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
BILLS_DIR = os.path.join(BASE_DIR, 'bills')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
for directory in [DATABASE_DIR, BILLS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Database path
DATABASE_PATH = os.path.join(DATABASE_DIR, 'storage.db')

# Initialize database if it doesn't exist
if not os.path.exists(DATABASE_PATH):
    if not initialize_database():
        logger.error("Failed to initialize database")
        raise RuntimeError("Database initialization failed")

# Migrate database if it exists
if os.path.exists(DATABASE_PATH):
    migrate_database()