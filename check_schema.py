import sqlite3

conn = sqlite3.connect('storage.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='products'")
schema = cursor.fetchone()
print("Products Table Schema:")
print(schema[0])

# Get sample data
cursor.execute("SELECT * FROM products LIMIT 1")
sample = cursor.fetchone()
if sample:
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    print("\nColumns:")
    for column in columns:
        print(f"{column[1]} ({column[2]})")
    
    print("\nSample Data:")
    for i, col in enumerate(columns):
        if i < len(sample):
            print(f"{col[1]}: {sample[i]}")
else:
    print("\nNo sample data found")

conn.close()