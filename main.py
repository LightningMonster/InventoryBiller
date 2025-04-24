import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os
import sys
from utils import convert_to_words

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Basic Billing System")

        # Initialize variables
        self.total_amount = 0.0
        self.bill_items = []

        # Initialize database
        self.init_database()

        # Create main frame
        self.create_basic_gui()

    def init_database(self):
        if getattr(sys, 'frozen', False):
            user_data_dir = os.path.join(os.path.expanduser("~"), "BillingApp")
            os.makedirs(user_data_dir, exist_ok=True)
            database_path = os.path.join(user_data_dir, "storage.db")
            bills_dir = os.path.join(user_data_dir, "bills")
            os.makedirs(bills_dir, exist_ok=True)
            self.conn = sqlite3.connect(database_path)
            self.cursor = self.conn.cursor()
            self.database_path = database_path
            self.user_data_dir = user_data_dir
        else:
            app_directory = os.path.dirname(os.path.abspath(__file__))
            database_path = os.path.join(app_directory, "storage.db")
            if not os.path.exists(database_path):
                open(database_path, 'w').close()
            self.conn = sqlite3.connect(database_path)
            self.cursor = self.conn.cursor()
            self.database_path = database_path
            self.user_data_dir = app_directory

        # Create basic tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                units INTEGER NOT NULL,
                price REAL NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                total_amount REAL NOT NULL,
                bill_date TEXT NOT NULL
            )
        ''')

        self.conn.commit()

    def create_basic_gui(self):
        # Product Entry Frame
        product_frame = tk.LabelFrame(self.root, text="Add Product")
        product_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(product_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        self.product_name = tk.Entry(product_frame)
        self.product_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(product_frame, text="Units:").grid(row=0, column=2, padx=5, pady=5)
        self.product_units = tk.Entry(product_frame)
        self.product_units.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(product_frame, text="Price:").grid(row=0, column=4, padx=5, pady=5)
        self.product_price = tk.Entry(product_frame)
        self.product_price.grid(row=0, column=5, padx=5, pady=5)

        tk.Button(product_frame, text="Add Product", command=self.add_product).grid(row=0, column=6, padx=5, pady=5)

        # Billing Frame
        billing_frame = tk.LabelFrame(self.root, text="Billing")
        billing_frame.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(billing_frame, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5)
        self.customer_name = tk.Entry(billing_frame)
        self.customer_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(billing_frame, text="Product:").grid(row=1, column=0, padx=5, pady=5)
        self.product_list = tk.Listbox(billing_frame, height=10)
        self.product_list.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(billing_frame, text="Quantity:").grid(row=1, column=2, padx=5, pady=5)
        self.quantity = tk.Entry(billing_frame)
        self.quantity.grid(row=1, column=3, padx=5, pady=5)

        tk.Button(billing_frame, text="Add to Bill", command=self.add_to_bill).grid(row=1, column=4, padx=5, pady=5)

        # Bill Display
        self.bill_text = tk.Text(billing_frame, height=10, width=50)
        self.bill_text.grid(row=2, column=0, columnspan=5, padx=5, pady=5)

        # Total and Finalize
        tk.Label(billing_frame, text="Total:").grid(row=3, column=0, padx=5, pady=5)
        self.total_label = tk.Label(billing_frame, text="₹0.00")
        self.total_label.grid(row=3, column=1, padx=5, pady=5)

        tk.Button(billing_frame, text="Finalize Bill", command=self.finalize_bill).grid(row=3, column=4, padx=5, pady=5)

        # Load products
        self.load_products()

    def load_products(self):
        self.product_list.delete(0, tk.END)
        self.cursor.execute("SELECT name FROM products")
        for product in self.cursor.fetchall():
            self.product_list.insert(tk.END, product[0])

    def add_product(self):
        name = self.product_name.get()
        try:
            units = int(self.product_units.get())
            price = float(self.product_price.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid units or price")
            return

        self.cursor.execute("INSERT INTO products (name, units, price) VALUES (?, ?, ?)",
                          (name, units, price))
        self.conn.commit()
        self.load_products()

        # Clear entries
        self.product_name.delete(0, tk.END)
        self.product_units.delete(0, tk.END)
        self.product_price.delete(0, tk.END)

    def add_to_bill(self):
        selection = self.product_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a product")
            return

        product_name = self.product_list.get(selection[0])
        try:
            quantity = int(self.quantity.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return

        self.cursor.execute("SELECT price, units FROM products WHERE name = ?", (product_name,))
        price, available_units = self.cursor.fetchone()

        if quantity > available_units:
            messagebox.showerror("Error", f"Only {available_units} units available")
            return

        total = price * quantity
        self.total_amount += total

        # Update bill display
        self.bill_text.insert(tk.END, f"{product_name} x {quantity} = ₹{total:.2f}\n")
        self.total_label.config(text=f"₹{self.total_amount:.2f}")

        # Update inventory
        self.cursor.execute("UPDATE products SET units = units - ? WHERE name = ?",
                          (quantity, product_name))
        self.conn.commit()

        # Clear quantity
        self.quantity.delete(0, tk.END)

    def finalize_bill(self):
        if self.total_amount <= 0:
            messagebox.showerror("Error", "No items in bill")
            return

        customer_name = self.customer_name.get()
        if not customer_name:
            messagebox.showerror("Error", "Enter customer name")
            return

        date = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute("INSERT INTO bills (customer_name, total_amount, bill_date) VALUES (?, ?, ?)",
                          (customer_name, self.total_amount, date))
        self.conn.commit()

        messagebox.showinfo("Success", "Bill finalized")

        # Clear everything
        self.bill_text.delete(1.0, tk.END)
        self.customer_name.delete(0, tk.END)
        self.total_amount = 0
        self.total_label.config(text="₹0.00")
        self.load_products()

def main():
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()