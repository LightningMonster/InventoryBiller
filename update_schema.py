import sqlite3

def update_database_schema():
    conn = sqlite3.connect('storage.db')
    cursor = conn.cursor()
    
    # Check if total_units column already exists
    cursor.execute("PRAGMA table_info(products)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'total_units' not in columns:
        print("Adding total_units column to products table...")
        try:
            # Add the total_units column with a default value equal to units
            cursor.execute("ALTER TABLE products ADD COLUMN total_units INTEGER DEFAULT 0")
            
            # Update existing rows to set total_units equal to units
            cursor.execute("UPDATE products SET total_units = units")
            
            conn.commit()
            print("Database schema updated successfully!")
        except sqlite3.Error as e:
            print(f"Error updating database schema: {e}")
            conn.rollback()
    else:
        print("total_units column already exists.")
    
    conn.close()

if __name__ == "__main__":
    update_database_schema()