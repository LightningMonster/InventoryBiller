
import sqlite3
from datetime import datetime
from config import DATABASE_PATH

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
        self.initialize_database()
        
    def initialize_database(self):
        # Create required tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dom TEXT NOT NULL,
                expiry TEXT NOT NULL,
                batch_no TEXT NOT NULL,
                mrp REAL NOT NULL,
                discount REAL NOT NULL,
                hsn_code TEXT NOT NULL,
                units INTEGER NOT NULL,
                rate REAL NOT NULL,
                taxable_amount REAL NOT NULL,
                igst REAL NOT NULL,
                cgst REAL NOT NULL,
                sgst REAL NOT NULL,
                total_amount REAL NOT NULL,
                amount_in_words TEXT NOT NULL,
                company_id INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')
        # Add other table creation statements...
        
    def save_product(self, product_data):
        try:
            self.cursor.execute('''
                INSERT INTO products (name, dom, expiry, batch_no, mrp, discount, 
                                    hsn_code, units, rate, taxable_amount, igst, 
                                    cgst, sgst, total_amount, amount_in_words, 
                                    company_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product_data)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e
            
    # Add other database operations...
