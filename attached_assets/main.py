import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import os

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing Software")
        self.root.state('zoomed')  # Maximized window

        self.total_amount = 0.0
        self.bill_items = []

        # Initialize database
        self.init_database()

        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create menu (ensure it's called only once)
        self.create_menu()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_billing_tab()
        self.create_storage_tab()

        # Initially show billing tab
        self.notebook.select(0)
    
    def create_menu(self):
        # Create the main menu bar
        menubar = tk.Menu(self.root)

        # Billing menu
        billing_menu = tk.Menu(menubar, tearoff=0)
        billing_menu.add_command(label="Billing", command=lambda: self.notebook.select(0))
        menubar.add_cascade(label="Billing", menu=billing_menu)

        # Storage menu
        storage_menu = tk.Menu(menubar, tearoff=0)
        storage_menu.add_command(label="Storage", command=lambda: self.notebook.select(1))
        menubar.add_cascade(label="Storage", menu=storage_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help", command=lambda: messagebox.showinfo("Help", "Help section coming soon!"))
        menubar.add_cascade(label="Help", menu=help_menu)

        # Set the menu for the root window
        self.root.config(menu=menubar)
    
    def init_database(self):
        # Get the directory of the executable
        app_directory = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(app_directory, "storage.db")
        
        if not os.path.exists(database_path):
            open(database_path, 'w').close()
        
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
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
                company_id INTEGER DEFAULT NULL,
                company_address TEXT DEFAULT NULL,
                company_gst TEXT DEFAULT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                gst_number TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def create_billing_tab(self):
        self.billing_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.billing_tab, text="Billing")
        
        # Customer Details Frame
        customer_frame = ttk.LabelFrame(self.billing_tab, text="Customer Details")
        customer_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Customer Name
        ttk.Label(customer_frame, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_name_entry = ttk.Entry(customer_frame, width=30)
        self.customer_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Mobile
        ttk.Label(customer_frame, text="Mobile:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_mobile_entry = ttk.Entry(customer_frame, width=30)
        self.customer_mobile_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Address
        ttk.Label(customer_frame, text="Address:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_address_entry = ttk.Entry(customer_frame, width=30)
        self.customer_address_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Item Selection Frame
        item_frame = ttk.LabelFrame(self.billing_tab, text="Item Selection")
        item_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Item
        ttk.Label(item_frame, text="Item:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.item_combobox = ttk.Combobox(item_frame, state="readonly")
        self.item_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.load_items()
        
        # Quantity
        ttk.Label(item_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.quantity_spinbox = ttk.Spinbox(item_frame, from_=1, to=1000, width=5)
        self.quantity_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Add Item Button
        add_button = ttk.Button(item_frame, text="Add Item", command=self.add_item_to_bill)
        add_button.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Bill Items Frame
        bill_frame = ttk.LabelFrame(self.billing_tab, text="Current Bill")
        bill_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bill List
        self.bill_listbox = tk.Listbox(bill_frame, height=10)
        self.bill_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Total Label
        self.total_label = ttk.Label(bill_frame, text="Total: ₹0.00", font=('Arial', 12, 'bold'))
        self.total_label.pack(pady=5)
        
        # Buttons Frame
        button_frame = ttk.Frame(self.billing_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Finalize Bill Button
        finalize_button = ttk.Button(button_frame, text="Finalize Bill", command=self.finalize_bill)
        finalize_button.pack(side=tk.LEFT, padx=5)
        
        # Print Bill Button
        print_button = ttk.Button(button_frame, text="Print Bill", command=self.print_bill)
        print_button.pack(side=tk.LEFT, padx=5)
    
    def create_storage_tab(self):
        self.storage_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.storage_tab, text="Storage")
        
        # Create a canvas and scrollbar
        canvas = tk.Canvas(self.storage_tab)
        scrollbar = ttk.Scrollbar(self.storage_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Company Details
        ttk.Label(scrollable_frame, text="Company Name*").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.company_name_combobox = ttk.Combobox(scrollable_frame, width=30)
        self.company_name_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.company_name_combobox.bind("<<ComboboxSelected>>", self.company_selected)
        self.load_companies()
        
        ttk.Label(scrollable_frame, text="Company Address").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.company_address_entry = ttk.Entry(scrollable_frame, width=40)
        self.company_address_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="GST Number").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.company_gst_entry = ttk.Entry(scrollable_frame, width=30)
        self.company_gst_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Save Company Button
        save_company_button = ttk.Button(scrollable_frame, text="Save Company", command=self.save_company)
        save_company_button.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Product Details
        ttk.Label(scrollable_frame, text="Product Name*").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.product_name_entry = ttk.Entry(scrollable_frame, width=30)
        self.product_name_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Date of Manufacture*").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.dom_picker = DateEntry(scrollable_frame, width=27, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.dom_picker.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Expiry Date*").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        self.expiry_picker = DateEntry(scrollable_frame, width=27, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.expiry_picker.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
        self.expiry_picker.set_date(datetime.now() + timedelta(days=365))  # Default to 1 year from now
        
        ttk.Label(scrollable_frame, text="Batch No*").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        self.batch_no_entry = ttk.Entry(scrollable_frame, width=30)
        self.batch_no_entry.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="MRP*").grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
        self.mrp_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.mrp_spinbox.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Discount (%)*").grid(row=9, column=0, padx=5, pady=5, sticky=tk.W)
        self.discount_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100, increment=0.01, format="%.2f")
        self.discount_spinbox.grid(row=9, column=1, padx=5, pady=5, sticky=tk.W)
        
        # HSN Code Field
        ttk.Label(scrollable_frame, text="HSN Code*").grid(row=10, column=0, padx=5, pady=5, sticky=tk.W)
        self.hsn_code_entry = ttk.Entry(scrollable_frame, width=30)
        self.hsn_code_entry.grid(row=10, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Right Column
        ttk.Label(scrollable_frame, text="Units*").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.units_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=10000, increment=1)
        self.units_spinbox.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Rate*").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.rate_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.rate_spinbox.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Taxable Amount*").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.taxable_amount_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.taxable_amount_spinbox.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="IGST*").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        self.igst_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.igst_spinbox.grid(row=3, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="CGST*").grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)
        self.cgst_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.cgst_spinbox.grid(row=4, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="SGST*").grid(row=5, column=2, padx=5, pady=5, sticky=tk.W)
        self.sgst_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.sgst_spinbox.grid(row=5, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Total Amount*").grid(row=6, column=2, padx=5, pady=5, sticky=tk.W)
        self.total_amount_spinbox = ttk.Spinbox(scrollable_frame, from_=0, to=100000, increment=0.01, format="%.2f")
        self.total_amount_spinbox.grid(row=6, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(scrollable_frame, text="Amount in Words*").grid(row=7, column=2, padx=5, pady=5, sticky=tk.W)
        self.amount_in_words_entry = tk.Text(scrollable_frame, width=30, height=3)
        self.amount_in_words_entry.grid(row=7, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Calculate Button
        calculate_button = ttk.Button(scrollable_frame, text="Calculate", command=self.calculate_amounts)
        calculate_button.grid(row=8, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=9, column=0, columnspan=4, pady=10)
        
        self.add_button = ttk.Button(button_frame, text="Add", command=self.add_product)
        self.add_button.pack(side=tk.LEFT, padx=5)
        
        self.update_button = ttk.Button(button_frame, text="Update", command=self.update_product)
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(button_frame, text="Delete", command=self.delete_product)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Product List
        self.product_tree = ttk.Treeview(scrollable_frame, columns=(
            "ID", "Product Name", "Batch No", "HSN Code", "MRP", "Rate", "Units", 
            "Expiry", "Total Amt", "Company Name", "Company Address", "GST Number"
        ), show="headings", height=10)
        
        self.product_tree.heading("ID", text="ID")
        self.product_tree.heading("Product Name", text="Product Name")
        self.product_tree.heading("Batch No", text="Batch No")
        self.product_tree.heading("HSN Code", text="HSN Code")
        self.product_tree.heading("MRP", text="MRP")
        self.product_tree.heading("Rate", text="Rate")
        self.product_tree.heading("Units", text="Units")
        self.product_tree.heading("Expiry", text="Expiry")
        self.product_tree.heading("Total Amt", text="Total Amt")
        self.product_tree.heading("Company Name", text="Company Name")
        self.product_tree.heading("Company Address", text="Company Address")
        self.product_tree.heading("GST Number", text="GST Number")
        
        self.product_tree.column("ID", width=50)
        self.product_tree.column("Product Name", width=150)
        self.product_tree.column("Batch No", width=80)
        self.product_tree.column("HSN Code", width=80)
        self.product_tree.column("MRP", width=70)
        self.product_tree.column("Rate", width=70)
        self.product_tree.column("Units", width=50)
        self.product_tree.column("Expiry", width=80)
        self.product_tree.column("Total Amt", width=80)
        self.product_tree.column("Company Name", width=150)
        self.product_tree.column("Company Address", width=200)
        self.product_tree.column("GST Number", width=150)
        
        self.product_tree.grid(row=10, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W+tk.E)
        self.product_tree.bind("<<TreeviewSelect>>", self.product_selected)
        
        # Load products
        self.load_products()
    
    def load_items(self):
        self.item_combobox['values'] = []
        self.cursor.execute("SELECT name FROM products WHERE units > 0")
        items = [row[0] for row in self.cursor.fetchall()]
        self.item_combobox['values'] = items
        if items:
            self.item_combobox.current(0)
    
    def add_item_to_bill(self):
        selected_item = self.item_combobox.get()
        quantity = int(self.quantity_spinbox.get())
        
        if not selected_item:
            messagebox.showerror("Error", "Please select an item.")
            return
        
        self.cursor.execute("SELECT id, rate, units FROM products WHERE name = ?", (selected_item,))
        result = self.cursor.fetchone()
        
        if not result:
            messagebox.showerror("Error", "Selected item not found in the database.")
            return
        
        product_id, rate, stock = result
        
        if quantity > stock:
            messagebox.showerror("Stock Error", f"Only {stock} units available for {selected_item}.")
            return
        
        item_total = quantity * rate
        self.total_amount += item_total
        self.bill_items.append((product_id, selected_item, quantity, rate, item_total))
        
        self.bill_listbox.insert(tk.END, f"{selected_item} - Qty: {quantity}, Rate: ₹{rate:.2f}, Total: ₹{item_total:.2f}")
        self.total_label.config(text=f"Total: ₹{self.total_amount:.2f}")
        
        # Reset quantity
        self.quantity_spinbox.delete(0, tk.END)
        self.quantity_spinbox.insert(0, "1")
    
    def finalize_bill(self):
        if not self.bill_items:
            messagebox.showinfo("Info", "No items in the bill to finalize.")
            return
        
        # Update stock in database
        for item in self.bill_items:
            product_id, _, quantity, _, _ = item
            self.cursor.execute("UPDATE products SET units = units - ? WHERE id = ?", (quantity, product_id))
        
        self.conn.commit()
        
        # Show bill summary
        bill_summary = "\n".join([f"{name} x {qty} = ₹{item_total:.2f}" for _, name, qty, _, item_total in self.bill_items])
        messagebox.showinfo("Bill Finalized", f"Items:\n{bill_summary}\n\nTotal: ₹{self.total_amount:.2f}")
        
        # Reset bill
        self.bill_listbox.delete(0, tk.END)
        self.total_amount = 0.0
        self.bill_items = []
        self.total_label.config(text="Total: ₹0.00")
        self.load_items()  # Refresh item selector
    
    def print_bill(self):
        # This is a simplified print function that shows a preview
        # In a real application, you would implement actual printing
        
        if not self.bill_items:
            messagebox.showinfo("Info", "No items to print.")
            return
        
        # Create a simple print preview window
        print_window = tk.Toplevel(self.root)
        print_window.title("Bill Print Preview")
        
        text = tk.Text(print_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Add bill content
        text.insert(tk.END, "COMPANY NAME\n")
        text.insert(tk.END, "123 Anywhere St., Any City, ST 12345\n")
        text.insert(tk.END, "Phone: 123-456-7890\n")
        text.insert(tk.END, "Email: hello@reallygreatsite.com\n")
        text.insert(tk.END, "Website: www.reallygreatsite.com\n\n")
        
        text.insert(tk.END, f"Date: {datetime.now().strftime('%d/%m/%Y')}\n")
        text.insert(tk.END, f"Customer: {self.customer_name_entry.get()}\n")
        text.insert(tk.END, f"Mobile: {self.customer_mobile_entry.get()}\n\n")
        
        text.insert(tk.END, "ITEM DESCRIPTION".ljust(30) + "PRICE".rjust(10) + "QTY".rjust(10) + "TOTAL".rjust(10) + "\n")
        text.insert(tk.END, "-" * 60 + "\n")
        
        for item in self.bill_items:
            _, name, qty, rate, item_total = item
            text.insert(tk.END, f"{name.ljust(30)}{f'₹{rate:.2f}'.rjust(10)}{str(qty).rjust(10)}{f'₹{item_total:.2f}'.rjust(10)}\n")
        
        text.insert(tk.END, "-" * 60 + "\n")
        text.insert(tk.END, "TOTAL:".rjust(50) + f"₹{self.total_amount:.2f}".rjust(10) + "\n")
        
        # Disable editing
        text.config(state=tk.DISABLED)
        
        # Print button
        print_button = ttk.Button(print_window, text="Print", command=lambda: messagebox.showinfo("Print", "Printing would be implemented here"))
        print_button.pack(pady=10)
    
    def load_companies(self):
        self.company_name_combobox['values'] = []
        self.cursor.execute("SELECT name FROM companies")
        companies = [row[0] for row in self.cursor.fetchall()]
        self.company_name_combobox['values'] = companies
    
    def company_selected(self, event):
        selected_company = self.company_name_combobox.get()
        if not selected_company:
            return
        
        self.cursor.execute("SELECT address, gst_number FROM companies WHERE name = ?", (selected_company,))
        result = self.cursor.fetchone()
        
        if result:
            self.company_address_entry.delete(0, tk.END)
            self.company_address_entry.insert(0, result[0])
            self.company_gst_entry.delete(0, tk.END)
            self.company_gst_entry.insert(0, result[1])
    
    def calculate_amounts(self):
        try:
            rate = float(self.rate_spinbox.get())
            units = int(self.units_spinbox.get())
            discount = float(self.discount_spinbox.get())
            mrp = float(self.mrp_spinbox.get())
            
            # Calculate taxable amount (after discount)
            taxable_amount = (rate * units) * (1 - discount / 100)
            self.taxable_amount_spinbox.delete(0, tk.END)
            self.taxable_amount_spinbox.insert(0, f"{taxable_amount:.2f}")
            
            # Get GST values
            igst = float(self.igst_spinbox.get())
            cgst = float(self.cgst_spinbox.get())
            sgst = float(self.sgst_spinbox.get())
            
            # If only IGST is entered, split to CGST and SGST
            if igst > 0 and cgst == 0 and sgst == 0:
                cgst = igst / 2
                sgst = igst / 2
                self.cgst_spinbox.delete(0, tk.END)
                self.cgst_spinbox.insert(0, f"{cgst:.2f}")
                self.sgst_spinbox.delete(0, tk.END)
                self.sgst_spinbox.insert(0, f"{sgst:.2f}")
            
            # Calculate total amount
            total_amount = taxable_amount + igst + cgst + sgst
            self.total_amount_spinbox.delete(0, tk.END)
            self.total_amount_spinbox.insert(0, f"{total_amount:.2f}")
            
            # Convert to words
            self.amount_in_words_entry.delete("1.0", tk.END)
            self.amount_in_words_entry.insert("1.0", self.number_to_words(int(total_amount)) + " rupees only")
        
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
    
    def number_to_words(self, number):
        if number == 0:
            return "zero"
        
        if number < 0:
            return "minus " + self.number_to_words(abs(number))
        
        words = ""
        
        if (number // 1000000) > 0:
            words += self.number_to_words(number // 1000000) + " million "
            number %= 1000000
        
        if (number // 1000) > 0:
            words += self.number_to_words(number // 1000) + " thousand "
            number %= 1000
        
        if (number // 100) > 0:
            words += self.number_to_words(number // 100) + " hundred "
            number %= 100
        
        if number > 0:
            if words != "":
                words += "and "
            
            units_map = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", 
                         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", 
                         "seventeen", "eighteen", "nineteen"]
            tens_map = ["zero", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
            
            if number < 20:
                words += units_map[number]
            else:
                words += tens_map[number // 10]
                if (number % 10) > 0:
                    words += "-" + units_map[number % 10]
        
        return words
    
    def add_product(self):
        if not self.product_name_entry.get() or not self.company_name_combobox.get():
            messagebox.showerror("Error", "Product name and company name are required!")
            return
        
        hsn_code = self.hsn_code_entry.get()
        if not hsn_code:
            messagebox.showerror("Error", "HSN Code is required!")
            return
        
        if not hsn_code.isdigit():
            messagebox.showerror("Error", "HSN Code must be numeric!")
            return
        
        try:
            # Get company details
            self.cursor.execute("SELECT id, address, gst_number FROM companies WHERE name = ?", 
                              (self.company_name_combobox.get(),))
            company = self.cursor.fetchone()
            
            if not company:
                messagebox.showerror("Error", "Selected company does not exist!")
                return
            
            company_id, company_address, company_gst = company
            
            # Insert product
            self.cursor.execute('''
                INSERT INTO products (
                    hsn_code, name, dom, expiry, batch_no, mrp, discount, 
                    units, rate, taxable_amount, igst, cgst, sgst, 
                    total_amount, amount_in_words, company_id, company_address, company_gst
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hsn_code,
                self.product_name_entry.get(),
                self.dom_picker.get_date().strftime('%Y-%m-%d'),
                self.expiry_picker.get_date().strftime('%Y-%m-%d'),
                self.batch_no_entry.get(),
                float(self.mrp_spinbox.get()),
                float(self.discount_spinbox.get()),
                int(self.units_spinbox.get()),
                float(self.rate_spinbox.get()),
                float(self.taxable_amount_spinbox.get()),
                float(self.igst_spinbox.get()),
                float(self.cgst_spinbox.get()),
                float(self.sgst_spinbox.get()),
                float(self.total_amount_spinbox.get()),
                self.amount_in_words_entry.get("1.0", tk.END).strip(),
                company_id,
                company_address,
                company_gst
            ))
            
            self.conn.commit()
            self.load_products()
            self.clear_product_form()
            messagebox.showinfo("Success", "Product added successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add product: {str(e)}")
    
    def update_product(self):
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a product to update!")
            return
        
        try:
            product_id = self.product_tree.item(selected_item)['values'][0]
            
            hsn_code = self.hsn_code_entry.get()
            if not hsn_code.isdigit():
                messagebox.showerror("Error", "HSN Code must be numeric!")
                return
            
            # Get company details
            self.cursor.execute("SELECT id, address, gst_number FROM companies WHERE name = ?", 
                              (self.company_name_combobox.get(),))
            company = self.cursor.fetchone()
            
            if not company:
                messagebox.showerror("Error", "Selected company does not exist!")
                return
            
            company_id, company_address, company_gst = company
            
            # Update product
            self.cursor.execute('''
                UPDATE products SET 
                    hsn_code = ?, 
                    name = ?, 
                    dom = ?, 
                    expiry = ?, 
                    batch_no = ?, 
                    mrp = ?, 
                    discount = ?, 
                    units = ?, 
                    rate = ?, 
                    taxable_amount = ?, 
                    igst = ?, 
                    cgst = ?, 
                    sgst = ?, 
                    total_amount = ?, 
                    amount_in_words = ?,
                    company_id = ?,
                    company_address = ?,
                    company_gst = ?
                WHERE id = ?
            ''', (
                hsn_code,
                self.product_name_entry.get(),
                self.dom_picker.get_date().strftime('%Y-%m-%d'),
                self.expiry_picker.get_date().strftime('%Y-%m-%d'),
                self.batch_no_entry.get(),
                float(self.mrp_spinbox.get()),
                float(self.discount_spinbox.get()),
                int(self.units_spinbox.get()),
                float(self.rate_spinbox.get()),
                float(self.taxable_amount_spinbox.get()),
                float(self.igst_spinbox.get()),
                float(self.cgst_spinbox.get()),
                float(self.sgst_spinbox.get()),
                float(self.total_amount_spinbox.get()),
                self.amount_in_words_entry.get("1.0", tk.END).strip(),
                company_id,
                company_address,
                company_gst,
                product_id
            ))
            
            self.conn.commit()
            self.load_products()
            messagebox.showinfo("Success", "Product updated successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update product: {str(e)}")
    
    def delete_product(self):
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a product to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this product?"):
            try:
                product_id = self.product_tree.item(selected_item)['values'][0]
                self.cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                self.conn.commit()
                self.load_products()
                self.clear_product_form()
                messagebox.showinfo("Success", "Product deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {str(e)}")
    
    def product_selected(self, event):
        selected_item = self.product_tree.selection()
        if not selected_item:
            return
        
        product_id = self.product_tree.item(selected_item)['values'][0]
        
        self.cursor.execute('''
            SELECT p.*, c.name AS company_name 
            FROM products p
            LEFT JOIN companies c ON p.company_id = c.id
            WHERE p.id = ?
        ''', (product_id,))
        
        product = self.cursor.fetchone()
        
        if product:
            self.product_name_entry.delete(0, tk.END)
            self.product_name_entry.insert(0, product[1])
            
            self.dom_picker.set_date(datetime.strptime(product[2], '%Y-%m-%d'))
            self.expiry_picker.set_date(datetime.strptime(product[3], '%Y-%m-%d'))
            
            self.batch_no_entry.delete(0, tk.END)
            self.batch_no_entry.insert(0, product[4])
            
            self.mrp_spinbox.delete(0, tk.END)
            self.mrp_spinbox.insert(0, product[5])
            
            self.discount_spinbox.delete(0, tk.END)
            self.discount_spinbox.insert(0, product[6])
            
            self.hsn_code_entry.delete(0, tk.END)
            self.hsn_code_entry.insert(0, product[7])  # Assuming HSN Code is at index 7
            
            self.units_spinbox.delete(0, tk.END)
            self.units_spinbox.insert(0, product[8])
            
            self.rate_spinbox.delete(0, tk.END)
            self.rate_spinbox.insert(0, product[9])
            
            self.taxable_amount_spinbox.delete(0, tk.END)
            self.taxable_amount_spinbox.insert(0, product[10])
            
            self.igst_spinbox.delete(0, tk.END)
            self.igst_spinbox.insert(0, product[11])
            
            self.cgst_spinbox.delete(0, tk.END)
            self.cgst_spinbox.insert(0, product[12])
            
            self.sgst_spinbox.delete(0, tk.END)
            self.sgst_spinbox.insert(0, product[13])
            
            self.total_amount_spinbox.delete(0, tk.END)
            self.total_amount_spinbox.insert(0, product[14])
            
            self.amount_in_words_entry.delete("1.0", tk.END)
            self.amount_in_words_entry.insert("1.0", product[15])
            
            self.company_name_combobox.set(product[17])  # company_name from the join
            self.company_address_entry.delete(0, tk.END)
            self.company_address_entry.insert(0, product[16] or "")
            self.company_gst_entry.delete(0, tk.END)
            self.company_gst_entry.insert(0, product[17] or "")
    
    def load_products(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        self.cursor.execute('''
            SELECT p.id, p.name, p.batch_no, p.hsn_code, p.mrp, p.rate, p.units, 
                   p.expiry, p.total_amount, c.name AS company_name, 
                   p.company_address, p.company_gst
            FROM products p
            LEFT JOIN companies c ON p.company_id = c.id
        ''')
        
        for product in self.cursor.fetchall():
            self.product_tree.insert("", tk.END, values=(
                product[0], product[1], product[2], product[3], product[4], 
                product[5], product[6], product[7], product[8], product[9],
                product[10], product[11]
            ))
    
    def clear_product_form(self):
        self.product_name_entry.delete(0, tk.END)
        self.dom_picker.set_date(datetime.now())
        self.expiry_picker.set_date(datetime.now() + timedelta(days=365))
        self.batch_no_entry.delete(0, tk.END)
        self.mrp_spinbox.delete(0, tk.END)
        self.mrp_spinbox.insert(0, "0.00")
        self.discount_spinbox.delete(0, tk.END)
        self.discount_spinbox.insert(0, "0.00")
        self.hsn_code_entry.delete(0, tk.END)
        self.units_spinbox.delete(0, tk.END)
        self.units_spinbox.insert(0, "0")
        self.rate_spinbox.delete(0, tk.END)
        self.rate_spinbox.insert(0, "0.00")
        self.taxable_amount_spinbox.delete(0, tk.END)
        self.taxable_amount_spinbox.insert(0, "0.00")
        self.igst_spinbox.delete(0, tk.END)
        self.igst_spinbox.insert(0, "0.00")
        self.cgst_spinbox.delete(0, tk.END)
        self.cgst_spinbox.insert(0, "0.00")
        self.sgst_spinbox.delete(0, tk.END)
        self.sgst_spinbox.insert(0, "0.00")
        self.total_amount_spinbox.delete(0, tk.END)
        self.total_amount_spinbox.insert(0, "0.00")
        self.amount_in_words_entry.delete("1.0", tk.END)
        self.company_name_combobox.set('')
        self.company_address_entry.delete(0, tk.END)
        self.company_gst_entry.delete(0, tk.END)
    
    def save_company(self):
        name = self.company_name_combobox.get()
        address = self.company_address_entry.get()
        gst_number = self.company_gst_entry.get()
        
        if not name or not address or not gst_number:
            messagebox.showerror("Error", "All fields are required to save a company!")
            return
        
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO companies (name, address, gst_number)
                VALUES (?, ?, ?)
            ''', (name, address, gst_number))
            
            self.conn.commit()
            self.load_companies()
            messagebox.showinfo("Success", "Company saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save company: {str(e)}")
    
    def test_hsn_code(self):
        print(self.hsn_code_entry.get())

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()