import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import os
import re
import string
import random
from fixed_bill_generator import generate_bill_pdf
from utils import convert_to_words
from config import DATABASE_PATH, BILLS_DIR

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing & Inventory Management System")
        # Use geometry instead of 'zoomed' state which is Windows-specific
        self.root.geometry("1200x700")  # Default size
        self.root.state('normal')  # Normal window state
        
        # Variable to track product being edited
        self.current_editing_product_id = None
        
        # Create a single menubar
        self.create_menu()
        
        self.total_amount = 0.0
        self.bill_items = []
        
        # Initialize database
        self.init_database()
        
        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_billing_tab()
        self.create_storage_tab()
        self.create_reports_tab()
        self.create_management_tab()
        
        # Initially show billing tab
        self.notebook.select(0)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def init_database(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
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
                company_id INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                gst_number TEXT NOT NULL UNIQUE
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_mobile TEXT,
                customer_address TEXT,
                bill_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                bill_items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_identifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT UNIQUE NOT NULL,
                identifier TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL UNIQUE,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                batch_no TEXT NOT NULL,
                company_name TEXT NOT NULL,
                initial_units INTEGER NOT NULL,
                dom TEXT NOT NULL,
                expiry TEXT NOT NULL,
                emptied_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def create_billing_tab(self):
        """Creates the Billing tab"""
        self.billing_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.billing_tab, text="Billing")
        
        # Create left and right frames for layout
        left_frame = ttk.Frame(self.billing_tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(self.billing_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Customer Details Frame
        customer_frame = ttk.LabelFrame(left_frame, text="Customer Details")
        customer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Customer Details Grid
        customer_grid = ttk.Frame(customer_frame)
        customer_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Customer Name
        ttk.Label(customer_grid, text="Customer Name*:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Only show the combobox for customer selection
        self.customer_name_combo = ttk.Combobox(customer_grid, width=40)
        self.customer_name_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Bind combobox selection event
        self.customer_name_combo.bind('<<ComboboxSelected>>', self.customer_selected_billing)
        
        # Load existing customer names
        self.load_customer_names_billing()
        
        # Mobile
        ttk.Label(customer_grid, text="Mobile:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.customer_mobile_entry = ttk.Entry(customer_grid, width=20)
        self.customer_mobile_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Address
        ttk.Label(customer_grid, text="Address:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_address_entry = ttk.Entry(customer_grid, width=50)
        self.customer_address_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Item Selection Frame
        item_frame = ttk.LabelFrame(left_frame, text="Item Selection")
        item_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Company Selection
        ttk.Label(item_frame, text="Company:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.bill_company_combobox = ttk.Combobox(item_frame, state="readonly", width=30)
        self.bill_company_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.load_companies_for_billing()
        
        # Item Selection
        ttk.Label(item_frame, text="Product:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.item_combobox = ttk.Combobox(item_frame, state="readonly", width=30)
        self.item_combobox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.bill_company_combobox.bind("<<ComboboxSelected>>", self.load_items_by_company)
        self.item_combobox.bind("<<ComboboxSelected>>", self.product_selected)
        
        # Quantity
        ttk.Label(item_frame, text="Quantity:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.quantity_spinbox = ttk.Spinbox(item_frame, from_=1, to=1000, width=10)
        self.quantity_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # HSN Code Display
        ttk.Label(item_frame, text="HSN Code:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.hsn_display = ttk.Label(item_frame, text="", width=15)
        self.hsn_display.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Price Display
        ttk.Label(item_frame, text="Price (₹):").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.price_display = ttk.Label(item_frame, text="0.00", width=15)
        self.price_display.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Add Item Button
        add_button = ttk.Button(item_frame, text="Add Item", command=self.add_item_to_bill)
        add_button.grid(row=3, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Remove Item Button
        remove_button = ttk.Button(item_frame, text="Remove Selected", command=self.remove_selected_item)
        remove_button.grid(row=3, column=3, padx=5, pady=10, sticky=tk.W)
        
        # Bill Preview Frame
        bill_frame = ttk.LabelFrame(right_frame, text="Current Bill")
        bill_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bill Items Tree
        columns = ("no", "item", "hsn", "qty", "rate", "total")
        self.bill_tree = ttk.Treeview(bill_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        self.bill_tree.heading("no", text="#")
        self.bill_tree.heading("item", text="Item Name")
        self.bill_tree.heading("hsn", text="HSN")
        self.bill_tree.heading("qty", text="Qty")
        self.bill_tree.heading("rate", text="Rate")
        self.bill_tree.heading("total", text="Total")
        
        # Column widths
        self.bill_tree.column("no", width=40)
        self.bill_tree.column("item", width=200)
        self.bill_tree.column("hsn", width=100)
        self.bill_tree.column("qty", width=60)
        self.bill_tree.column("rate", width=100)
        self.bill_tree.column("total", width=100)
        
        # Scrollbar for the treeview
        tree_scroll = ttk.Scrollbar(bill_frame, orient="vertical", command=self.bill_tree.yview)
        self.bill_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Packing
        self.bill_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Summary Frame
        summary_frame = ttk.Frame(right_frame)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Subtotal, Tax, Total
        ttk.Label(summary_frame, text="Subtotal:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.subtotal_label = ttk.Label(summary_frame, text="₹0.00", width=10)
        self.subtotal_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(summary_frame, text="Tax:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.tax_label = ttk.Label(summary_frame, text="₹0.00", width=10)
        self.tax_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(summary_frame, text="Total:", font=('Arial', 10, 'bold')).grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.total_label = ttk.Label(summary_frame, text="₹0.00", width=10, font=('Arial', 10, 'bold'))
        self.total_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Action Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Clear Bill Button
        clear_button = ttk.Button(button_frame, text="Clear Bill", command=self.clear_bill)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Finalize Bill Button
        finalize_button = ttk.Button(button_frame, text="Finalize Bill", command=self.finalize_bill)
        finalize_button.pack(side=tk.LEFT, padx=5)
        
        # Print Bill Button
        print_button = ttk.Button(button_frame, text="Print Bill", command=self.print_bill)
        print_button.pack(side=tk.LEFT, padx=5)
    
    def load_customer_names_billing(self):
        """Loads existing customer names into the billing combobox"""
        try:
            self.cursor.execute('SELECT name FROM customers ORDER BY name')
            customers = self.cursor.fetchall()
            customer_names = [customer[0] for customer in customers]
            self.customer_name_combo['values'] = customer_names
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load customer names: {str(e)}")

    def customer_selected_billing(self, event=None):
        """Handles customer selection in billing tab"""
        selected_name = self.customer_name_combo.get()
        if selected_name:
            try:
                self.cursor.execute('''
                    SELECT mobile, address 
                    FROM customers 
                    WHERE name = ?
                ''', (selected_name,))
                
                customer = self.cursor.fetchone()
                if customer:
                    # Auto-fill mobile and address
                    self.customer_mobile_entry.delete(0, tk.END)
                    self.customer_mobile_entry.insert(0, customer[0])
                    
                    self.customer_address_entry.delete(0, tk.END)
                    self.customer_address_entry.insert(0, customer[1])
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load customer details: {str(e)}")

    def create_storage_tab(self):
        self.storage_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.storage_tab, text="Inventory")
        
        # Create a container with scrollbar
        main_container = ttk.Frame(self.storage_tab)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top and bottom frames
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Product entry form
        form_frame = ttk.LabelFrame(top_frame, text="Product Details")
        form_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create a grid layout for the form
        grid_frame = ttk.Frame(form_frame)
        grid_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Company Details
        ttk.Label(grid_frame, text="Company Name*:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.company_name_combobox = ttk.Combobox(grid_frame, width=30)
        self.company_name_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.company_name_combobox.bind("<<ComboboxSelected>>", self.company_selected)
        
        # "Add New Company" Button
        add_company_btn = ttk.Button(grid_frame, text="Add New Company", command=self.add_new_company)
        add_company_btn.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        self.load_companies()
        
        ttk.Label(grid_frame, text="Company Address:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.company_address_entry = ttk.Entry(grid_frame, width=40)
        self.company_address_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(grid_frame, text="GST Number:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.company_gst_entry = ttk.Entry(grid_frame, width=30)
        self.company_gst_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Save Company Button
        save_company_button = ttk.Button(grid_frame, text="Save Company", command=self.save_company)
        save_company_button.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Separator
        ttk.Separator(grid_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # Product Details
        ttk.Label(grid_frame, text="Product Name*:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.product_name_combobox = ttk.Combobox(grid_frame, width=27)
        self.product_name_combobox.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        self.product_name_combobox.bind('<<ComboboxSelected>>', self.product_name_selected)
        self.load_product_names()
        
        ttk.Label(grid_frame, text="HSN Code*:").grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)
        self.hsn_code_entry = ttk.Entry(grid_frame, width=20)
        self.hsn_code_entry.grid(row=4, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="Date of Manufacture*:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.dom_picker = DateEntry(grid_frame, width=17, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.dom_picker.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="Date of Expiry*:").grid(row=5, column=2, padx=5, pady=5, sticky=tk.W)
        self.expiry_picker = DateEntry(grid_frame, width=17, 
                                     background='darkblue',
                                     foreground='white',
                                     borderwidth=2,
                                     date_pattern='yyyy-mm-dd',
                                     state='readonly')
        self.expiry_picker.grid(row=5, column=3, padx=5, pady=5, sticky=tk.W)

        # Set default expiry date to 1 year from manufacturing date
        def update_expiry_date(event=None):
            try:
                mfg_date = self.dom_picker.get_date()
                self.expiry_picker.set_date(mfg_date + timedelta(days=365))
            except Exception as e:
                print(f"Error updating expiry date: {e}")

        # Bind the manufacturing date change to update expiry date
        self.dom_picker.bind("<<DateEntrySelected>>", update_expiry_date)
        
        ttk.Label(grid_frame, text="Batch No*:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Create a frame for batch number components
        batch_frame = ttk.Frame(grid_frame)
        batch_frame.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Identifier display (read-only)
        self.batch_prefix_label = ttk.Label(batch_frame, width=3, relief="solid", anchor="center")
        self.batch_prefix_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Month dropdown
        months = [(str(i).zfill(2), i) for i in range(1, 13)]
        self.batch_month_var = tk.StringVar()
        self.batch_month_combo = ttk.Combobox(batch_frame, textvariable=self.batch_month_var,
                                             values=[m[0] for m in months], width=3, state="readonly")
        self.batch_month_combo.pack(side=tk.LEFT, padx=2)
        
        # Year dropdown
        current_year = datetime.now().year
        years = [str(y)[2:] for y in range(current_year, current_year + 6)]
        self.batch_year_var = tk.StringVar()
        self.batch_year_combo = ttk.Combobox(batch_frame, textvariable=self.batch_year_var,
                                            values=years, width=3, state="readonly")
        self.batch_year_combo.pack(side=tk.LEFT, padx=2)
        
        # Sequence number combobox
        self.batch_seq_var = tk.StringVar()
        self.batch_seq_combo = ttk.Combobox(batch_frame, textvariable=self.batch_seq_var,
                                            width=3, state="readonly")
        self.batch_seq_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind the sequence combobox to update the full batch number
        self.batch_seq_combo.bind('<<ComboboxSelected>>', self.update_batch_number)
        
        # Hidden entry to store full batch number
        self.batch_no_entry = ttk.Entry(grid_frame)
        self.batch_no_entry.grid_remove()  # Hide this entry

        # Set default values
        self.batch_month_var.set(datetime.now().strftime('%m'))
        self.batch_year_var.set(str(datetime.now().year)[2:])

        # Add binding to update batch number when month/year changes
        self.batch_month_combo.bind('<<ComboboxSelected>>', self.update_batch_number)
        self.batch_year_combo.bind('<<ComboboxSelected>>', self.update_batch_number)
        
        ttk.Label(grid_frame, text="Units*:").grid(row=6, column=2, padx=5, pady=5, sticky=tk.W)
        self.units_spinbox = ttk.Spinbox(grid_frame, from_=0, to=10000, increment=1, width=10)
        self.units_spinbox.grid(row=6, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="MRP*:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        self.mrp_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=0.01, format="%.2f", width=12)
        self.mrp_spinbox.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="Discount (%)*:").grid(row=7, column=2, padx=5, pady=5, sticky=tk.W)
        self.discount_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.discount_spinbox.grid(row=7, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="Rate*:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
        self.rate_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=0.01, format="%.2f", width=12)
        self.rate_spinbox.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="Taxable Amount*:").grid(row=8, column=2, padx=5, pady=5, sticky=tk.W)
        self.taxable_amount_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=0.01, format="%.2f", width=12)
        self.taxable_amount_spinbox.grid(row=8, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="IGST*:").grid(row=9, column=0, padx=5, pady=5, sticky=tk.W)
        self.igst_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.igst_spinbox.grid(row=9, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="CGST*:").grid(row=9, column=2, padx=5, pady=5, sticky=tk.W)
        self.cgst_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.cgst_spinbox.grid(row=9, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="SGST*:").grid(row=10, column=0, padx=5, pady=5, sticky=tk.W)
        self.sgst_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.sgst_spinbox.grid(row=10, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(grid_frame, text="Total Amount*:").grid(row=10, column=2, padx=5, pady=5, sticky=tk.W)
        self.total_amount_spinbox = ttk.Spinbox(grid_frame, from_=0, to=1000000, increment=0.01, format="%.2f", width=12)
        self.total_amount_spinbox.grid(row=10, column=3, padx=5, pady=5, sticky=tk.W)

        # Calculate button
        calculate_btn = ttk.Button(grid_frame, text="Calculate Amounts", command=self.calculate_product_amounts)
        calculate_btn.grid(row=10, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Button Frame
        btn_frame = ttk.Frame(grid_frame)
        btn_frame.grid(row=11, column=0, columnspan=4, pady=10, sticky=tk.EW)
        
        # Save Product Button
        self.save_product_button = ttk.Button(btn_frame, text="Save Product", command=self.save_product)
        self.save_product_button.pack(side=tk.LEFT, padx=10)
        
        # Clear Form Button
        clear_form_button = ttk.Button(btn_frame, text="Clear Form", command=self.clear_product_form)
        clear_form_button.pack(side=tk.LEFT, padx=10)
        
        # Inventory List
        bottom_frame = ttk.LabelFrame(main_container, text="Inventory List")
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search Frame
        search_frame = ttk.Frame(bottom_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search Product:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        search_btn = ttk.Button(search_frame, text="Search", command=self.search_products)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(search_frame, text="Refresh", command=self.refresh_product_list)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Add Import/Export buttons to the search frame
        import_btn = ttk.Button(search_frame, text="Import from Excel", command=self.import_from_excel)
        import_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(search_frame, text="Export to Excel", command=self.export_to_excel)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Inventory TreeView
        columns = (
            "id", "name", "hsn", "company", "batch", "dom", "expiry", "units", 
            "mrp", "discount", "rate", "taxable_amount", "igst", "cgst", "sgst", "total", "amount_in_words"
        )
        self.inventory_tree = ttk.Treeview(bottom_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        self.inventory_tree.heading("id", text="ID")
        self.inventory_tree.heading("name", text="Product Name")
        self.inventory_tree.heading("hsn", text="HSN Code")
        self.inventory_tree.heading("company", text="Company")
        self.inventory_tree.heading("batch", text="Batch No")
        self.inventory_tree.heading("dom", text="Date of MFG")
        self.inventory_tree.heading("expiry", text="Expiry Date")
        self.inventory_tree.heading("units", text="Units")
        self.inventory_tree.heading("mrp", text="MRP")
        self.inventory_tree.heading("discount", text="Discount (%)")
        self.inventory_tree.heading("rate", text="Rate")
        self.inventory_tree.heading("taxable_amount", text="Taxable Amount")
        self.inventory_tree.heading("igst", text="IGST")
        self.inventory_tree.heading("cgst", text="CGST")
        self.inventory_tree.heading("sgst", text="SGST")
        self.inventory_tree.heading("total", text="Total Amount")
        self.inventory_tree.heading("amount_in_words", text="Amount in Words")
        
        # Column widths
        self.inventory_tree.column("id", width=50)
        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("hsn", width=100)
        self.inventory_tree.column("company", width=120)
        self.inventory_tree.column("batch", width=100)
        self.inventory_tree.column("dom", width=100)
        self.inventory_tree.column("expiry", width=100)
        self.inventory_tree.column("units", width=60)
        self.inventory_tree.column("mrp", width=80)
        self.inventory_tree.column("discount", width=80)
        self.inventory_tree.column("rate", width=80)
        self.inventory_tree.column("taxable_amount", width=120)
        self.inventory_tree.column("igst", width=80)
        self.inventory_tree.column("cgst", width=80)
        self.inventory_tree.column("sgst", width=80)
        self.inventory_tree.column("total", width=120)
        self.inventory_tree.column("amount_in_words", width=200)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(bottom_frame, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(xscrollcommand=x_scrollbar.set)
        
        # Pack the treeview and scrollbars
        self.inventory_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Right-click menu for tree
        self.tree_menu = tk.Menu(self.inventory_tree, tearoff=0)
        self.tree_menu.add_command(label="Edit", command=self.edit_selected_product)
        self.tree_menu.add_command(label="Delete", command=self.delete_selected_product)
        
        self.inventory_tree.bind("<Button-3>", self.show_tree_menu)
        self.inventory_tree.bind("<Double-1>", lambda event: self.edit_selected_product())
        
        # Load products
        self.refresh_product_list()
    
    def update_batch_number(self, event=None):
        """Updates the batch number when month or year is changed"""
        if hasattr(self, 'batch_prefix_label'):
            prefix = self.batch_prefix_label.cget('text')
            if prefix:
                month = self.batch_month_var.get()
                year = self.batch_year_var.get()
                
                # Get sequence number for this combination
                self.cursor.execute('''
                    SELECT COUNT(*) 
                    FROM products 
                    WHERE batch_no LIKE ? || ? || ? || '%'
                ''', (prefix, month, year))
                count = self.cursor.fetchone()[0]
                sequence = str(count + 1)
                
                # Update sequence combobox values
                self.batch_seq_combo['values'] = [str(i) for i in range(1, count + 2)]
                self.batch_seq_var.set(sequence)
                
                # Update hidden batch number entry
                full_batch = f"{prefix}{month}{year}{sequence}"
                self.batch_no_entry.delete(0, tk.END)
                self.batch_no_entry.insert(0, full_batch)
    
    def product_name_selected(self, event=None):
        """Handles product selection in the inventory tab"""
        selected_name = self.product_name_combobox.get()
        if selected_name:
            # First check for identifier
            self.cursor.execute('''
                SELECT identifier 
                FROM product_identifiers 
                WHERE product_name = ?
            ''', (selected_name,))
            
            result = self.cursor.fetchone()
            if result:
                # Update the batch prefix label with the identifier
                self.batch_prefix_label.config(text=result[0])
                
                # Update batch number with current month/year and sequence
                month = self.batch_month_var.get()
                year = self.batch_year_var.get()
                
                # Get sequence number for this combination
                self.cursor.execute('''
                    SELECT COUNT(*) 
                    FROM products 
                    WHERE batch_no LIKE ? || ? || ? || '%'
                ''', (result[0], month, year))
                count = self.cursor.fetchone()[0]
                
                # Update sequence combobox values and full batch number
                self.batch_seq_combo['values'] = [str(i) for i in range(1, count + 2)]
                self.batch_seq_var.set(str(count + 1))
                
                full_batch = f"{result[0]}{month}{year}{count + 1}"
                self.batch_no_entry.delete(0, tk.END)
                self.batch_no_entry.insert(0, full_batch)
            
            # Get other product details as before
            self.cursor.execute('''
                SELECT p.*, c.name as company_name 
                FROM products p
                LEFT JOIN companies c ON p.company_id = c.id
                WHERE p.name = ?
                ORDER BY p.dom DESC LIMIT 1
            ''', (selected_name,))
            
            product = self.cursor.fetchone()
            if product:
                # Auto-fill HSN code and other details
                self.hsn_code_entry.delete(0, tk.END)
                self.hsn_code_entry.insert(0, product[7])  # HSN code
                
                # Set MRP
                self.mrp_spinbox.delete(0, tk.END)
                self.mrp_spinbox.insert(0, f"{product[5]:.2f}")  # MRP
                
                # Set company if available
                if product[-1]:  # company_name
                    self.company_name_combobox.set(product[-1])
                    self.company_selected()
    
    def company_selected(self, event=None):
        """Handles company selection and auto-fills company details"""
        company_name = self.company_name_combobox.get()
        if not company_name:
            return
            
        try:
            # Get company details from database
            self.cursor.execute('''
                SELECT address, gst_number 
                FROM companies 
                WHERE name = ?
            ''', (company_name,))
            
            company = self.cursor.fetchone()
            if company:
                # Auto-fill address and GST fields
                self.company_address_entry.delete(0, tk.END)
                self.company_address_entry.insert(0, company[0])
                
                self.company_gst_entry.delete(0, tk.END)
                self.company_gst_entry.insert(0, company[1])
                
                self.status_bar.config(text=f"Loaded details for company: {company_name}")
            else:
                # Clear fields if company not found
                self.company_address_entry.delete(0, tk.END)
                self.company_gst_entry.delete(0, tk.END)
                self.status_bar.config(text="Company not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load company details: {str(e)}")

    def create_reports_tab(self):
        """Creates the Reports tab with multiple report options"""
        # Create main reports frame
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reports")
        
        # Report Type Selection Frame
        report_type_frame = ttk.LabelFrame(reports_frame, text="Report Type")
        report_type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Report type radiobuttons
        self.report_type = tk.StringVar(value="sales")
        ttk.Radiobutton(report_type_frame, text="Sales Report", 
                        variable=self.report_type, value="sales",
                        command=self.switch_report_view).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(report_type_frame, text="Batch History", 
                        variable=self.report_type, value="batch",
                        command=self.switch_report_view).pack(side=tk.LEFT, padx=10)
        
        # Date range selection frame
        self.date_frame = ttk.LabelFrame(reports_frame, text="Date Range")
        self.date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.date_frame, text="From:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = DateEntry(self.date_frame, width=12, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.date_frame, text="To:").grid(row=0, column=2, padx=5, pady=5)
        self.end_date = DateEntry(self.date_frame, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.grid(row=0, column=3, padx=5, pady=5)
        
        self.generate_btn = ttk.Button(self.date_frame, text="Generate Report", 
                                      command=self.generate_report)
        self.generate_btn.grid(row=0, column=4, padx=15, pady=5)
        
        # Create frames for different report types
        self.sales_frame = ttk.LabelFrame(reports_frame, text="Sales Report")
        self.batch_frame = ttk.LabelFrame(reports_frame, text="Batch History")
        
        # Sales Report TreeView
        columns = ("id", "date", "customer", "items", "amount")
        self.report_tree = ttk.Treeview(self.sales_frame, columns=columns, 
                                       show="headings", height=15)
        
        # Define headings for sales report
        self.report_tree.heading("id", text="Bill #")
        self.report_tree.heading("date", text="Date")
        self.report_tree.heading("customer", text="Customer")
        self.report_tree.heading("items", text="Items Count")
        self.report_tree.heading("amount", text="Total Amount")
        
        # Batch History TreeView
        columns = ("product", "batch", "company", "units", "dom", "expiry", "emptied")
        self.batch_tree = ttk.Treeview(self.batch_frame, columns=columns, 
                                      show="headings", height=15)
        
        # Define headings for batch history
        self.batch_tree.heading("product", text="Product Name")
        self.batch_tree.heading("batch", text="Batch No")
        self.batch_tree.heading("company", text="Company")
        self.batch_tree.heading("units", text="Initial Units")
        self.batch_tree.heading("dom", text="Mfg Date")
        self.batch_tree.heading("expiry", text="Expiry Date")
        self.batch_tree.heading("emptied", text="Emptied Date")
        
        # Add scrollbars to both trees
        self.setup_tree_scrollbars(self.report_tree, self.sales_frame)
        self.setup_tree_scrollbars(self.batch_tree, self.batch_frame)
        
        # Show sales report by default
        self.sales_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_tree_scrollbars(self, tree, parent):
        """Helper method to add scrollbars to a treeview"""
        scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

    def switch_report_view(self):
        """Switches between different report views"""
        report_type = self.report_type.get()
        
        if report_type == "sales":
            self.batch_frame.pack_forget()
            self.sales_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        else:
            self.sales_frame.pack_forget()
            self.batch_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clear previous data
        for tree in (self.report_tree, self.batch_tree):
            for item in tree.get_children():
                tree.delete(item)

    def generate_report(self):
        """Generates the selected type of report"""
        report_type = self.report_type.get()
        start_date = self.start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date.get_date().strftime('%Y-%m-%d')
        
        if report_type == "sales":
            self.generate_sales_report(start_date, end_date)
        else:
            self.generate_batch_report(start_date, end_date)

    def generate_batch_report(self, start_date, end_date):
        """Generates batch history report"""
        # Clear existing items
        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        
        # Query batch history within date range
        self.cursor.execute('''
            SELECT product_name, batch_no, company_name, initial_units,
                   dom, expiry, emptied_date
            FROM batch_history
            WHERE emptied_date BETWEEN ? AND ?
            ORDER BY emptied_date DESC
        ''', (start_date, end_date))
        
        batches = self.cursor.fetchall()
        
        for batch in batches:
            self.batch_tree.insert('', 'end', values=batch)
        
        self.status_bar.config(text=f"Generated batch history report: {len(batches)} records found")

    def create_management_tab(self):
        """Creates the Management tab with product identifiers and customer management"""
        self.management_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.management_tab, text="Management")
        
        # Create notebook for sub-tabs
        management_notebook = ttk.Notebook(self.management_tab)
        management_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Identifiers Tab
        identifiers_tab = ttk.Frame(management_notebook)
        management_notebook.add(identifiers_tab, text="Product Identifiers")
        
        # Add controls frame
        controls_frame = ttk.Frame(identifiers_tab)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add search functionality
        ttk.Label(controls_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.identifier_search = ttk.Entry(controls_frame, width=30)
        self.identifier_search.pack(side=tk.LEFT, padx=5)
        self.identifier_search.bind('<KeyRelease>', self.search_identifiers)
        
        # Add refresh button
        ttk.Button(controls_frame, text="Refresh", 
                   command=self.refresh_identifiers).pack(side=tk.LEFT, padx=5)
        
        # Create TreeView for identifiers
        columns = ("id", "product", "identifier", "created")
        self.identifiers_tree = ttk.Treeview(identifiers_tab, columns=columns, show="headings")
        
        # Define headings
        self.identifiers_tree.heading("id", text="ID")
        self.identifiers_tree.heading("product", text="Product Name")
        self.identifiers_tree.heading("identifier", text="Identifier")
        self.identifiers_tree.heading("created", text="Created Date")
        
        # Column widths
        self.identifiers_tree.column("id", width=50)
        self.identifiers_tree.column("product", width=200)
        self.identifiers_tree.column("identifier", width=100)
        self.identifiers_tree.column("created", width=150)
        
        # Right-click menu
        self.identifier_menu = tk.Menu(self.identifiers_tree, tearoff=0)
        self.identifier_menu.add_command(label="Edit", command=self.edit_identifier)
        self.identifier_menu.add_separator()
        self.identifier_menu.add_command(label="Delete", command=self.delete_identifier)
        
        self.identifiers_tree.bind("<Button-3>", self.show_identifier_menu)
        self.identifiers_tree.bind("<Double-1>", lambda e: self.edit_identifier())
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(identifiers_tab, orient=tk.VERTICAL, 
                                 command=self.identifiers_tree.yview)
        self.identifiers_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the tree and scrollbar
        self.identifiers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load identifiers
        self.refresh_identifiers()
        
        # Customer Tab
        customers_tab = ttk.Frame(management_notebook)
        management_notebook.add(customers_tab, text="Customers")
        
        # Customer Entry Frame
        entry_frame = ttk.LabelFrame(customers_tab, text="Customer Details")
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Customer Entry Fields
        ttk.Label(entry_frame, text="Name*:").grid(row=0, column=0, padx=5, pady=5)
        self.customer_name_manage = ttk.Entry(entry_frame, width=30)
        self.customer_name_manage.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(entry_frame, text="Mobile*:").grid(row=0, column=2, padx=5, pady=5)
        self.customer_mobile_manage = ttk.Entry(entry_frame, width=20)
        self.customer_mobile_manage.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(entry_frame, text="Address:").grid(row=1, column=0, padx=5, pady=5)
        self.customer_address_manage = ttk.Entry(entry_frame, width=50)
        self.customer_address_manage.grid(row=1, column=1, columnspan=3, padx=5, pady=5)
        
        # Buttons Frame
        self.customer_buttons_frame = ttk.Frame(entry_frame)  # Change to instance variable
        self.customer_buttons_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        self.save_customer_button = ttk.Button(self.customer_buttons_frame,  # Create instance variable
                                         text="Save Customer",
                                         command=self.save_customer_manage)
        self.save_customer_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.customer_buttons_frame, text="Clear Form", 
                   command=self.clear_customer_form_manage).pack(side=tk.LEFT, padx=5)
        
        # Customer List Frame
        list_frame = ttk.LabelFrame(customers_tab, text="Customer List")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Customer TreeView
        columns = ("id", "name", "mobile", "address", "created")
        self.customers_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        self.customers_tree.heading("id", text="ID")
        self.customers_tree.heading("name", text="Name")
        self.customers_tree.heading("mobile", text="Mobile")
        self.customers_tree.heading("address", text="Address")
        self.customers_tree.heading("created", text="Created Date")
        
        self.customers_tree.column("id", width=50)
        self.customers_tree.column("name", width=200)
        self.customers_tree.column("mobile", width=120)
        self.customers_tree.column("address", width=250)
        self.customers_tree.column("created", width=150)
        
        # Scrollbar for customers tree
        customers_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=customers_scroll.set)
        
        self.customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        customers_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right-click menu for customers
        self.customer_menu = tk.Menu(self.customers_tree, tearoff=0)
        self.customer_menu.add_command(label="Edit", command=self.edit_customer)
        self.customer_menu.add_command(label="Delete", command=self.delete_customer)
        
        self.customers_tree.bind("<Button-3>", self.show_customer_menu)
        self.customers_tree.bind("<Double-1>", lambda e: self.edit_customer())
        
        # Load customer list
        self.load_customers_list()
        
        # Companies Tab
        companies_tab = ttk.Frame(management_notebook)
        management_notebook.add(companies_tab, text="Companies")
        
        # Company Entry Frame
        company_entry_frame = ttk.LabelFrame(companies_tab, text="Company Details")
        company_entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Company Entry Fields
        ttk.Label(company_entry_frame, text="Name*:").grid(row=0, column=0, padx=5, pady=5)
        self.company_name_manage = ttk.Entry(company_entry_frame, width=30)
        self.company_name_manage.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(company_entry_frame, text="GST Number*:").grid(row=0, column=2, padx=5, pady=5)
        self.company_gst_manage = ttk.Entry(company_entry_frame, width=20)
        self.company_gst_manage.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(company_entry_frame, text="Address*:").grid(row=1, column=0, padx=5, pady=5)
        self.company_address_manage = ttk.Entry(company_entry_frame, width=60)
        self.company_address_manage.grid(row=1, column=1, columnspan=3, padx=5, pady=5)
        
        # Buttons Frame
        self.company_buttons_frame = ttk.Frame(company_entry_frame)
        self.company_buttons_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(self.company_buttons_frame, text="Save Company", 
                   command=self.save_company_manage).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.company_buttons_frame, text="Clear Form", 
                   command=self.clear_company_form_manage).pack(side=tk.LEFT, padx=5)
        
        # Company List Frame
        company_list_frame = ttk.LabelFrame(companies_tab, text="Company List")
        company_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Company TreeView
        columns = ("id", "name", "gst", "address", "created")
        self.companies_tree = ttk.Treeview(company_list_frame, columns=columns, show="headings")
        
        self.companies_tree.heading("id", text="ID")
        self.companies_tree.heading("name", text="Name")
        self.companies_tree.heading("gst", text="GST Number")
        self.companies_tree.heading("address", text="Address")
        self.companies_tree.heading("created", text="Created Date")
        
        self.companies_tree.column("id", width=50)
        self.companies_tree.column("name", width=200)
        self.companies_tree.column("gst", width=150)
        self.companies_tree.column("address", width=250)
        self.companies_tree.column("created", width=150)
        
        # Right-click menu for companies
        self.company_menu = tk.Menu(self.companies_tree, tearoff=0)
        self.company_menu.add_command(label="Edit", command=self.edit_company)
        self.company_menu.add_command(label="Delete", command=self.delete_company)
        
        self.companies_tree.bind("<Button-3>", self.show_company_menu)
        self.companies_tree.bind("<Double-1>", lambda e: self.edit_company())
        
        # Scrollbar for companies tree
        companies_scroll = ttk.Scrollbar(company_list_frame, orient=tk.VERTICAL, command=self.companies_tree.yview)
        self.companies_tree.configure(yscrollcommand=companies_scroll.set)
        
        self.companies_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        companies_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load company list
        self.load_companies_list_manage()
    
    def add_new_company(self):
        """Opens a dialog to add a new company"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Company")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Company Name
        ttk.Label(dialog, text="Company Name*:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Address
        ttk.Label(dialog, text="Address*:").grid(row=1, column=0, padx=5, pady=5)
        address_entry = ttk.Entry(dialog, width=40)
        address_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # GST Number
        ttk.Label(dialog, text="GST Number*:").grid(row=2, column=0, padx=5, pady=5)
        gst_entry = ttk.Entry(dialog, width=20)
        gst_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def save_company():
            name = name_entry.get().strip()
            address = address_entry.get().strip()
            gst = gst_entry.get().strip().upper()
            
            if not name or not address or not gst:
                messagebox.showerror("Error", "All fields are required!")
                return
                
            if not re.match(r'^[0-9A-Z]{15}$', gst):
                messagebox.showerror("Error", "Invalid GST Number format. It should be 15 alphanumeric characters.")
                return
                
            try:
                self.cursor.execute('''
                    INSERT INTO companies (name, address, gst_number)
                    VALUES (?, ?, ?)
                ''', (name, address, gst))
                
                self.conn.commit()
                self.load_companies()
                self.load_companies_for_billing()
                messagebox.showinfo("Success", "Company added successfully!")
                dialog.destroy()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Company name already exists!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add company: {str(e)}")
        
        # Add Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=save_company).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Center the dialog on screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def edit_identifier(self):
        selected = self.identifiers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a product identifier to edit")
            return
        
        item = self.identifiers_tree.item(selected[0])
        item_id = item['values'][0]
        current_product = item['values'][1]
        current_identifier = item['values'][2]
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Product Identifier")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Form fields
        ttk.Label(dialog, text="Product Name:").grid(row=0, column=0, padx=5, pady=5)
        product_entry = ttk.Entry(dialog, width=30)
        product_entry.insert(0, current_product)
        product_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Identifier:").grid(row=1, column=0, padx=5, pady=5)
        identifier_entry = ttk.Entry(dialog, width=30)
        identifier_entry.insert(0, current_identifier)
        identifier_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def save_changes():
            new_product = product_entry.get().strip()
            new_identifier = identifier_entry.get().strip().upper()
            
            if not new_product or not new_identifier:
                messagebox.showerror("Error", "Both fields are required!")
                return
            
            if len(new_identifier) != 2:
                messagebox.showerror("Error", "Identifier must be exactly 2 characters!")
                return
            
            try:
                # Check if new identifier is already used by another product
                self.cursor.execute('''
                    SELECT id FROM product_identifiers 
                    WHERE identifier = ? AND id != ?
                ''', (new_identifier, item_id))
                
                if self.cursor.fetchone():
                    messagebox.showerror("Error", "This identifier is already in use!")
                    return
                
                # Update both product_identifiers and products tables
                self.cursor.execute('''
                    UPDATE product_identifiers 
                    SET product_name = ?, identifier = ?
                    WHERE id = ?
                ''', (new_product, new_identifier, item_id))
                
                # Update all related batch numbers in products table
                self.cursor.execute('''
                    UPDATE products 
                    SET batch_no = ? || substr(batch_no, 3)
                    WHERE name = ?
                ''', (new_identifier, current_product))
                
                self.conn.commit()
                self.refresh_identifiers()
                dialog.destroy()
                messagebox.showinfo("Success", "Product identifier updated successfully!")
                
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Failed to update: {str(e)}")
        
        # Buttons
        ttk.Button(dialog, text="Save", command=save_changes).grid(row=2, column=1, pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=2, column=0, pady=20)
    
    def show_identifier_menu(self, event):
        item = self.identifiers_tree.identify_row(event.y)
        if item:
            self.identifiers_tree.selection_set(item)
            self.identifier_menu.post(event.x_root, event.y_root)
    
    def refresh_identifiers(self):
        for item in self.identifiers_tree.get_children():
            self.identifiers_tree.delete(item)
        
        self.cursor.execute('''
            SELECT id, product_name, identifier, created_at
            FROM product_identifiers
            ORDER BY product_name
        ''')
        
        for row in self.cursor.fetchall():
            self.identifiers_tree.insert('', 'end', values=row)
    
    def search_identifiers(self, event=None):
        search_term = self.identifier_search.get().strip()
        
        for item in self.identifiers_tree.get_children():
            self.identifiers_tree.delete(item)
        
        self.cursor.execute('''
            SELECT id, product_name, identifier, created_at
            FROM product_identifiers
            WHERE product_name LIKE ? OR identifier LIKE ?
            ORDER BY product_name
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        for row in self.cursor.fetchall():
            self.identifiers_tree.insert('', 'end', values=row)
    
    def delete_identifier(self):
        selected = self.identifiers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a product identifier to delete")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this identifier?"):
            return
        
        item = self.identifiers_tree.item(selected[0])
        item_id = item['values'][0]
        product_name = item['values'][1]
        
        try:
            # First check if there are any products using this identifier
            self.cursor.execute('''
                SELECT COUNT(*) FROM products WHERE name = ?
            ''', (product_name,))
            
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", 
                    "Cannot delete: This identifier is being used by existing products!")
                return
            
            # Delete the identifier
            self.cursor.execute('DELETE FROM product_identifiers WHERE id = ?', (item_id,))
            self.conn.commit()
            self.refresh_identifiers()
            messagebox.showinfo("Success", "Product identifier deleted successfully!")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def load_identifiers_list(self):
        """Loads product identifiers into the identifiers tree"""
        for item in self.identifiers_tree.get_children():
            self.identifiers_tree.delete(item)
            
        self.cursor.execute('''
            SELECT product_name, identifier, created_at
            FROM product_identifiers
            ORDER BY product_name
        ''')
        
        for row in self.cursor.fetchall():
            self.identifiers_tree.insert('', 'end', values=row)
    
    def load_customers_list(self):
        """Load customers into the treeview"""
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Get all customers with created_at
        self.cursor.execute('''
            SELECT id, name, mobile, address, created_at 
            FROM customers 
            ORDER BY name
        ''')
        
        customers = self.cursor.fetchall()
        
        # Insert into treeview
        for customer in customers:
            self.customers_tree.insert('', 'end', values=customer)
    
    def save_customer_manage(self):
        """Saves customer from management tab"""
        name = self.customer_name_manage.get().strip()
        mobile = self.customer_mobile_manage.get().strip()
        address = self.customer_address_manage.get().strip()
        
        if not name or not mobile:
            messagebox.showerror("Error", "Name and Mobile are required!")
            return
        
        try:
            self.cursor.execute('''
                INSERT INTO customers (name, mobile, address)
                VALUES (?, ?, ?)
            ''', (name, mobile, address))
            
            self.conn.commit()
            self.load_customers_list()
            self.clear_customer_form_manage()
            messagebox.showinfo("Success", "Customer saved successfully!")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Mobile number already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save customer: {str(e)}")
    
    def clear_customer_form_manage(self):
        """Clears the customer form in management tab"""
        self.customer_name_manage.delete(0, tk.END)
        self.customer_mobile_manage.delete(0, tk.END)
        self.customer_address_manage.delete(0, tk.END)
    
    def save_company_manage(self):
        """Saves company from management tab"""
        name = self.company_name_manage.get().strip()
        gst = self.company_gst_manage.get().strip().upper()
        address = self.company_address_manage.get().strip()
        
        if not name or not gst or not address:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        if not re.match(r'^[0-9A-Z]{15}$', gst):
            messagebox.showerror("Error", "Invalid GST Number format. It should be 15 alphanumeric characters.")
            return
        
        try:
            # Check if GST already exists
            self.cursor.execute("SELECT name FROM companies WHERE gst_number = ? AND name != ?", (gst, name))
            existing_gst = self.cursor.fetchone()
            if existing_gst:
                messagebox.showerror("Error", f"GST Number already registered to company: {existing_gst[0]}")
                return
                
            self.cursor.execute('''
                INSERT INTO companies (name, gst_number, address)
                VALUES (?, ?, ?)
            ''', (name, gst, address))
            
            self.conn.commit()
            self.load_companies_list_manage()
            self.load_companies()  # Refresh other company lists
            self.load_companies_for_billing()
            self.clear_company_form_manage()
            messagebox.showinfo("Success", "Company saved successfully!")
            
        except sqlite3.IntegrityError as e:
            if "gst_number" in str(e):
                messagebox.showerror("Error", "This GST Number is already registered!")
            else:
                messagebox.showerror("Error", "Company name already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save company: {str(e)}")

    def clear_company_form_manage(self):
        """Clears the company form in management tab"""
        self.company_name_manage.delete(0, tk.END)
        self.company_gst_manage.delete(0, tk.END)
        self.company_address_manage.delete(0, tk.END)

    def load_companies_list_manage(self):
        """Loads companies into the companies tree"""
        for item in self.companies_tree.get_children():
            self.companies_tree.delete(item)
            
        self.cursor.execute('''
            SELECT id, name, gst_number, address, 
                   datetime('now') as created_at
            FROM companies
            ORDER BY name
        ''')
        
        for row in self.cursor.fetchall():
            self.companies_tree.insert('', 'end', values=row)

    def show_company_menu(self, event):
        """Shows the right-click menu for companies"""
        item = self.companies_tree.identify_row(event.y)
        if item:
            self.companies_tree.selection_set(item)
            self.company_menu.post(event.x_root, event.y_root)

    def edit_company(self):
        """Handles editing of selected company"""
        selected = self.companies_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a company to edit")
            return
        
        item = self.companies_tree.item(selected[0])
        company_id = item['values'][0]
        
        self.cursor.execute('''
            SELECT name, gst_number, address
            FROM companies
            WHERE id = ?
        ''', (company_id,))
        
        company = self.cursor.fetchone()
        if company:
            # Store the company ID for update operation
            self.current_editing_company_id = company_id
            
            # Populate form with company details
            self.company_name_manage.delete(0, tk.END)
            self.company_name_manage.insert(0, company[0])
            
            self.company_gst_manage.delete(0, tk.END)
            self.company_gst_manage.insert(0, company[1])
            
            self.company_address_manage.delete(0, tk.END)
            self.company_address_manage.insert(0, company[2])
            
            # Change save button to update mode
            self.company_buttons_frame.children['!button'].config(
                text="Update Company",
                command=self.update_company_manage
            )

    def update_company_manage(self):
        """Updates existing company details"""
        if not hasattr(self, 'current_editing_company_id'):
            messagebox.showerror("Error", "No company selected for update")
            return
            
        name = self.company_name_manage.get().strip()
        gst = self.company_gst_manage.get().strip().upper()
        address = self.company_address_manage.get().strip()
        
        if not name or not gst or not address:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        if not re.match(r'^[0-9A-Z]{15}$', gst):
            messagebox.showerror("Error", "Invalid GST Number format. It should be 15 alphanumeric characters.")
            return
        
        try:
            # Check if GST already exists for another company
            self.cursor.execute("""
                SELECT name FROM companies 
                WHERE gst_number = ? AND id != ?
            """, (gst, self.current_editing_company_id))
            existing_gst = self.cursor.fetchone()
            if existing_gst:
                messagebox.showerror("Error", f"GST Number already registered to company: {existing_gst[0]}")
                return
                
            self.cursor.execute('''
                UPDATE companies 
                SET name = ?, gst_number = ?, address = ?
                WHERE id = ?
            ''', (name, gst, address, self.current_editing_company_id))
            
            self.conn.commit()
            self.load_companies_list_manage()
            self.load_companies()  # Refresh other company lists
            self.load_companies_for_billing()
            self.clear_company_form_manage()
            
            # Reset button and editing state
            self.company_buttons_frame.children['!button'].config(
                text="Save Company",
                command=self.save_company_manage
            )
            del self.current_editing_company_id
            
            messagebox.showinfo("Success", "Company updated successfully!")
            
        except sqlite3.IntegrityError as e:
            if "gst_number" in str(e):
                messagebox.showerror("Error", "This GST Number is already registered!")
            else:
                messagebox.showerror("Error", "Company name already exists!")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to update company: {str(e)}")
    
    def delete_company(self):
        """Handles deletion of selected company"""
        selected = self.companies_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a company to delete")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this company?"):
            return
        
        item = self.companies_tree.item(selected[0])
        company_id = item['values'][0]
        
        try:
            # Check if company has associated products
            self.cursor.execute('SELECT COUNT(*) FROM products WHERE company_id = ?', (company_id,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", 
                    "Cannot delete: This company has associated products!")
                return
            
            # Delete the company
            self.cursor.execute('DELETE FROM companies WHERE id = ?', (company_id,))
            self.conn.commit()
            self.load_companies_list_manage()
            self.load_companies()  # Refresh other company lists
            self.load_companies_for_billing()
            messagebox.showinfo("Success", "Company deleted successfully!")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def load_companies(self):
        self.cursor.execute("SELECT name FROM companies ORDER BY name")
        companies = self.cursor.fetchall()
        company_names = [company[0] for company in companies]
        self.company_name_combobox['values'] = company_names
    
    def load_companies_for_billing(self):
        self.cursor.execute("SELECT name FROM companies ORDER BY name")
        companies = self.cursor.fetchall()
        company_names = [company[0] for company in companies]
        self.bill_company_combobox['values'] = company_names
    
    def load_product_names(self):
        try:
            self.cursor.execute('''
                SELECT DISTINCT name FROM products ORDER BY name
            ''')
            products = self.cursor.fetchall()
            product_names = [p[0] for p in products]
            
            # Allow new entries as well as selection from existing names
            self.product_name_combobox['values'] = product_names
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load product names: {str(e)}")
    
    def save_company(self):
        """Saves or updates company information"""
        
        if not name or not address or not gst:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        if not re.match(r'^[0-9A-Z]{15}$', gst):
            messagebox.showerror("Error", "Invalid GST Number format. It should be 15 alphanumeric characters.")
            return
        
        try:
            # Check if company exists
            self.cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
            result = self.cursor.fetchone()
            
            if result:
                # Update existing company
                self.cursor.execute('''
                    UPDATE companies 
                    SET address = ?, gst_number = ? 
                    WHERE name = ?
                ''', (address, gst, name))
                message = "Company updated successfully"
            else:
                # Insert new company
                self.cursor.execute('''
                    INSERT INTO companies (name, address, gst_number)
                    VALUES (?, ?, ?)
                ''', (name, address, gst))
                message = "Company added successfully"
            
            self.conn.commit()
            
            # Refresh company lists
            self.load_companies()
            self.load_companies_for_billing()
            
            # Show success message
            messagebox.showinfo("Success", message)
            self.status_bar.config(text=f"Company '{name}' saved successfully")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Company name already exists!")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to save company: {str(e)}")
    
    def calculate_product_amounts(self):
        try:
            # Get product name and arrival date
            product_name = self.product_name_combobox.get().strip()
            if not product_name:
                messagebox.showerror("Error", "Please enter Product Name first!")
                return
                
            arrival_date = self.dom_picker.get_date()
            
            # Generate batch number
            batch_no = self.generate_batch_number(product_name, arrival_date)
            
            # Update batch number field
            self.batch_no_entry.delete(0, tk.END)
            self.batch_no_entry.insert(0, batch_no)
            
            # Get values from input fields
            mrp = float(self.mrp_spinbox.get())
            discount_percent = float(self.discount_spinbox.get())
            units = int(self.units_spinbox.get())
            
            # Calculate rate (MRP minus discount)
            rate = mrp * (1 - discount_percent/100)
            
            # Calculate taxable amount (rate × units)
            taxable_amount = rate * units
            
            # Get GST percentages from user input
            igst_percent = float(self.igst_spinbox.get())
            cgst_percent = float(self.cgst_spinbox.get())
            sgst_percent = float(self.sgst_spinbox.get())
            
            # Calculate GST amounts based on taxable amount
            igst = taxable_amount * (igst_percent/100)
            cgst = taxable_amount * (cgst_percent/100)
            sgst = taxable_amount * (sgst_percent/100)
            
            # Calculate total amount
            total_amount = taxable_amount + igst + cgst + sgst
            
            # Update fields
            self.rate_spinbox.delete(0, tk.END)
            self.rate_spinbox.insert(0, f"{rate:.2f}")
            
            self.taxable_amount_spinbox.delete(0, tk.END)
            self.taxable_amount_spinbox.insert(0, f"{taxable_amount:.2f}")
            
            # Update GST amount fields (not percentages)
            self.total_amount_spinbox.delete(0, tk.END)
            self.total_amount_spinbox.insert(0, f"{total_amount:.2f}")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all fields.")
    
    def save_product(self):
        # Get company ID
        company_name = self.company_name_combobox.get()
        if not company_name:
            messagebox.showerror("Error", "Please select or add a company.")
            return

        self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
        company_result = self.cursor.fetchone()
        if not company_result:
            messagebox.showerror("Error", "Company not found. Please save the company first.")
            return

        company_id = company_result[0]

        # Get product details
        name = self.product_name_combobox.get().strip()
        dom = self.dom_picker.get_date()
        expiry = self.expiry_picker.get_date()
        hsn_code = self.hsn_code_entry.get().strip()

        # Validate required fields
        if not name or not hsn_code:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        try:
            # Generate batch number
            batch_no = self.generate_batch_number(name, dom)

            mrp = float(self.mrp_spinbox.get())
            discount = float(self.discount_spinbox.get())
            units = int(self.units_spinbox.get())
            rate = float(self.rate_spinbox.get())
            taxable_amount = float(self.taxable_amount_spinbox.get())
            igst = float(self.igst_spinbox.get())
            cgst = float(self.cgst_spinbox.get())
            sgst = float(self.sgst_spinbox.get())

            # Calculate total amount
            total_amount = taxable_amount + igst

            # Convert total to words
            amount_in_words = convert_to_words(total_amount)

            # Insert product into database
            self.cursor.execute('''
                INSERT INTO products (name, dom, expiry, batch_no, mrp, discount, hsn_code, 
                                     units, rate, taxable_amount, igst, cgst, sgst, 
                                     total_amount, amount_in_words, company_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, dom.strftime('%Y-%m-%d'), expiry.strftime('%Y-%m-%d'), batch_no, mrp, discount, hsn_code, 
                  units, rate, taxable_amount, igst, cgst, sgst, total_amount, amount_in_words, company_id))

            self.conn.commit()
            messagebox.showinfo("Success", "Product saved successfully.")
            self.clear_product_form()
            self.refresh_product_list()
            self.status_bar.config(text=f"Product '{name}' saved successfully")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all numeric fields.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def add_product(self):
        try:
            product_name = self.product_name_combobox.get().strip()
            if not product_name:
                messagebox.showerror("Error", "Product Name is required!")
                return

            # Get arrival date from DateEntry widget
            arrival_date = datetime.strptime(self.dom_picker.get(), '%Y-%m-%d')
            
            # Generate batch number
            batch_no = self.generate_batch_number(product_name, arrival_date)

            # Get other product details
            hsn_code = self.hsn_code_entry.get()
            expiry_date = datetime.strptime(self.expiry_picker.get(), '%Y-%m-%d')
            
            # ... rest of the add_product code ...

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def clear_product_form(self):
        self.product_name_combobox.set("")
        self.dom_picker.set_date(datetime.now())
        self.expiry_picker.set_date(datetime.now() + timedelta(days=365))
        self.batch_no_entry.delete(0, tk.END)
        self.hsn_code_entry.delete(0, tk.END)
        self.mrp_spinbox.delete(0, tk.END)
        self.mrp_spinbox.insert(0, "0.00")
        self.discount_spinbox.delete(0, tk.END)
        self.discount_spinbox.insert(0, "0.00")
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
        
        # Reset product editing state
        self.current_editing_product_id = None
        self.save_product_button.config(text="Save Product", command=self.save_product)
        self.status_bar.config(text="Ready")
    
    def refresh_product_list(self):
        # Clear the treeview
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get only products with available units
        self.cursor.execute('''
            SELECT p.id, p.name, p.hsn_code, c.name, p.batch_no, p.dom, p.expiry, 
                   p.units, p.mrp, p.discount, p.rate, p.taxable_amount, 
                   p.igst, p.cgst, p.sgst, p.total_amount, p.amount_in_words
            FROM products p
            LEFT JOIN companies c ON p.company_id = c.id
            WHERE p.units > 0
            ORDER BY p.name
        ''')
        
        products = self.cursor.fetchall()
        
        # Insert products into the treeview
        for product in products:
            self.inventory_tree.insert('', 'end', values=product)
        
        self.load_product_names()  # Reload product names in dropdown
    
    def search_products(self):
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.refresh_product_list()
            return
        
        # Clear the treeview
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Search by name, HSN code, or batch number
        self.cursor.execute('''
            SELECT p.id, p.name, p.hsn_code, c.name, p.batch_no, p.dom, p.expiry, p.units, 
                   p.mrp, p.discount, p.rate, p.taxable_amount, p.igst, p.cgst, p.sgst, 
                   p.total_amount, p.amount_in_words
            FROM products p
            LEFT JOIN companies c ON p.company_id = c.id
            WHERE p.name LIKE ? OR p.hsn_code LIKE ? OR p.batch_no LIKE ?
            ORDER BY p.name
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        products = self.cursor.fetchall()
        
        for product in products:
            self.inventory_tree.insert('', 'end', values=product)
        
        self.status_bar.config(text=f"Found {len(products)} matching products")
    
    def show_tree_menu(self, event):
        item = self.inventory_tree.identify_row(event.y)
        if item:
            self.inventory_tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)
    
    def create_menu(self):
        # Create the main menu bar
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Navigation menu
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Billing", command=lambda: self.notebook.select(0))
        nav_menu.add_command(label="Inventory", command=lambda: self.notebook.select(1))
        nav_menu.add_command(label="Reports", command=lambda: self.notebook.select(2))
        nav_menu.add_command(label="Management", command=lambda: self.notebook.select(3))
        menubar.add_cascade(label="Navigation", menu=nav_menu)
        
        # Bills menu - new menu for bill management
        bills_menu = tk.Menu(menubar, tearoff=0)
        bills_menu.add_command(label="Open Bills Folder", command=self.open_bills_folder)
        bills_menu.add_command(label="View Last Bill", command=self.view_last_bill)
        menubar.add_cascade(label="Bills", menu=bills_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Billing & Inventory Management System\nVersion 1.0"))
        help_menu.add_command(label="Help", command=lambda: messagebox.showinfo("Help", "Help section coming soon!"))
        menubar.add_cascade(label="Help", menu=help_menu)
        
        # Set the menu for the root window
        self.root.config(menu=menubar)
        
    def open_bills_folder(self):
        """Open the folder containing generated bills"""
        # Create the directory if it doesn't exist
        if not os.path.exists(BILLS_DIR):
            os.makedirs(BILLS_DIR)
            
        try:
            # Different commands based on OS
            if os.name == 'nt':  # For Windows
                os.startfile(BILLS_DIR)
            elif os.name == 'posix':  # For macOS and Linux
                import subprocess
                subprocess.Popen(['xdg-open', BILLS_DIR])
            self.status_bar.config(text=f"Opened bills folder: {BILLS_DIR}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open bills folder: {str(e)}")
    
    def view_last_bill(self):
        """View the most recently generated bill"""
        if not os.path.exists(BILLS_DIR):
            messagebox.showinfo("Info", "No bills have been generated yet.")
            return
            
        # Get list of PDF files in the bills directory
        bill_files = [f for f in os.listdir(BILLS_DIR) if f.lower().endswith('.pdf')]
        
        if not bill_files:
            messagebox.showinfo("Info", "No bills have been generated yet.")
            return
            
        # Sort by modification time (newest first)
        bill_files.sort(key=lambda x: os.path.getmtime(os.path.join(BILLS_DIR, x)), reverse=True)
        
        # Open the most recent bill
        latest_bill = os.path.join(BILLS_DIR, bill_files[0])
        try:
            # Different commands based on OS
            if os.name == 'nt':  # For Windows
                os.startfile(latest_bill)
            elif os.name == 'posix':  # For macOS and Linux
                import subprocess
                subprocess.Popen(['xdg-open', latest_bill])
            self.status_bar.config(text=f"Opened latest bill: {bill_files[0]}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open bill: {str(e)}")
    
    def update_product(self):
        try:
            if self.current_editing_product_id is None:
                messagebox.showerror("Error", "No product selected for update.")
                return

            # Get company ID
            company_name = self.company_name_combobox.get()
            if not company_name:
                messagebox.showerror("Error", "Please select or add a company.")
                return

            self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
            company_result = self.cursor.fetchone()
            if not company_result:
                messagebox.showerror("Error", "Company not found.")
                return

            company_id = company_result[0]
            product_name = self.product_name_combobox.get().strip()
            
            # Get the original product details for batch number comparison
            self.cursor.execute('''
                SELECT name, batch_no FROM products 
                WHERE id = ?
            ''', (self.current_editing_product_id,))
            original_product = self.cursor.fetchone()
            original_prefix = original_product[1][:2]

            # Update all batch numbers for the same product if prefix changed
            if product_name == original_product[0]:  # Same product name
                self.cursor.execute('''
                    SELECT id, batch_no FROM products 
                    WHERE name = ?
                ''', (product_name,))
                related_products = self.cursor.fetchall()
                
                # Update all related batch numbers with new prefix
                for prod_id, old_batch_no in related_products:
                    new_batch_no = self.batch_no_entry.get()[:2] + old_batch_no[2:]
                    self.cursor.execute('''
                        UPDATE products 
                        SET batch_no = ?
                        WHERE id = ?
                    ''', (new_batch_no, prod_id))

            # Update other fields
            self.cursor.execute('''
                UPDATE products 
                SET name = ?, dom = ?, expiry = ?, batch_no = ?, 
                    mrp = ?, discount = ?, hsn_code = ?, units = ?, 
                    rate = ?, taxable_amount = ?, igst = ?, cgst = ?, 
                    sgst = ?, total_amount = ?, company_id = ?
                WHERE id = ?
            ''', (
                product_name,
                self.dom_picker.get_date().strftime('%Y-%m-%d'),
                self.expiry_picker.get_date().strftime('%Y-%m-%d'),
                self.batch_no_entry.get(),
                float(self.mrp_spinbox.get()),
                float(self.discount_spinbox.get()),
                self.hsn_code_entry.get(),
                int(self.units_spinbox.get()),
                float(self.rate_spinbox.get()),
                float(self.taxable_amount_spinbox.get()),
                float(self.igst_spinbox.get()),
                float(self.cgst_spinbox.get()),
                float(self.sgst_spinbox.get()),
                float(self.total_amount_spinbox.get()),
                company_id,
                self.current_editing_product_id
            ))

            self.conn.commit()
            messagebox.showinfo("Success", "Product updated successfully!")
            self.refresh_product_list()
            self.clear_product_form()

        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Update failed: {str(e)}")

    def edit_selected_product(self):
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a product to edit.")
            return
        
        item_id = self.inventory_tree.item(selected_items[0], 'values')[0]
        
        # Store the current product ID for update operation
        self.current_editing_product_id = item_id
        
        self.cursor.execute('''
            SELECT p.*, c.name as company_name FROM products p
            LEFT JOIN companies c ON p.company_id = c.id
            WHERE p.id = ?
        ''', (item_id,))
        
        product = self.cursor.fetchone()
        if not product:
            messagebox.showerror("Error", "Product not found.")
            return
        
        # Populate form with product details
        self.product_name_combobox.set(product[1])  # name
        
        self.dom_picker.set_date(datetime.strptime(product[2], '%Y-%m-%d'))  # dom
        self.expiry_picker.set_date(datetime.strptime(product[3], '%Y-%m-%d'))  # expiry
        
        self.batch_no_entry.delete(0, tk.END)
        self.batch_no_entry.insert(0, product[4])  # batch_no
        
        self.hsn_code_entry.delete(0, tk.END)
        self.hsn_code_entry.insert(0, product[7])  # hsn_code
        
        self.mrp_spinbox.delete(0, tk.END)
        self.mrp_spinbox.insert(0, f"{product[5]:.2f}")  # mrp
        
        self.discount_spinbox.delete(0, tk.END)
        self.discount_spinbox.insert(0, f"{product[6]:.2f}")  # discount
        
        self.units_spinbox.delete(0, tk.END)
        self.units_spinbox.insert(0, product[8])  # units
        
        self.rate_spinbox.delete(0, tk.END)
        self.rate_spinbox.insert(0, f"{product[9]:.2f}")  # rate
        
        self.taxable_amount_spinbox.delete(0, tk.END)
        self.taxable_amount_spinbox.insert(0, f"{product[10]:.2f}")  # taxable_amount
        
        self.igst_spinbox.delete(0, tk.END)
        self.igst_spinbox.insert(0, f"{product[11]:.2f}")  # igst
        
        self.cgst_spinbox.delete(0, tk.END)
        self.cgst_spinbox.insert(0, f"{product[12]:.2f}")  # cgst
        
        self.sgst_spinbox.delete(0, tk.END)
        self.sgst_spinbox.insert(0, f"{product[13]:.2f}")  # sgst
        
        # Set company
        if product[-1]:  # company_name is last column
            self.company_name_combobox.set(product[-1])
            self.company_selected()
            
        # Change the Save button to Update mode
        self.save_product_button.config(text="Update Product", command=self.update_product)
        self.status_bar.config(text=f"Editing product: {product[1]}")
    
    def delete_selected_product(self):
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a product to delete.")
            return
        
        item_id = self.inventory_tree.item(selected_items[0], 'values')[0]
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            self.cursor.execute("DELETE FROM products WHERE id = ?", (item_id,))
            self.conn.commit()
            self.refresh_product_list()
            messagebox.showinfo("Success", "Product deleted successfully.")
            self.status_bar.config(text="Product deleted successfully")
    
    def load_items_by_company(self, event=None):
        """Loads products with available stock for selected company"""
        company_name = self.bill_company_combobox.get()
        if not company_name:
            return
        
        # Get company ID
        self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
        company_result = self.cursor.fetchone()
        if not company_result:
            return
        
        company_id = company_result[0]
        
        # Get only products with available stock
        self.cursor.execute('''
            SELECT DISTINCT name 
            FROM products 
            WHERE company_id = ? AND units > 0
            ORDER BY name
        ''', (company_id,))
        
        products = self.cursor.fetchall()
        product_names = [product[0] for product in products]
        self.item_combobox['values'] = product_names
    
    def product_selected(self, event=None):
        product_name = self.item_combobox.get()
        company_name = self.bill_company_combobox.get()
        
        if not product_name or not company_name:
            return
        
        # Get company ID
        self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
        company_result = self.cursor.fetchone()
        if not company_result:
            return
        
        company_id = company_result[0]
        
        # Get product details
        self.cursor.execute('''
            SELECT id, hsn_code, rate FROM products 
            WHERE name = ? AND company_id = ?
        ''', (product_name, company_id))
        
        product = self.cursor.fetchone()
        if product:
            # Make sure to display the HSN code - fixing the HSN code issue
            hsn_code = product[1] if product[1] else "N/A"
            self.hsn_display.config(text=hsn_code)
            self.price_display.config(text=f"₹{product[2]:.2f}")
    
    def add_item_to_bill(self):
        product_name = self.item_combobox.get()
        company_name = self.bill_company_combobox.get()
        
        if not product_name:
            messagebox.showerror("Error", "Please select a product.")
            return
        
        if not company_name:
            messagebox.showerror("Error", "Please select a company.")
            return
        
        try:
            quantity = int(self.quantity_spinbox.get())
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        # Get company ID
        self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
        company_result = self.cursor.fetchone()
        if not company_result:
            messagebox.showerror("Error", "Company not found.")
            return
        
        company_id = company_result[0]
        
        # Get all batches of the product with available units
        self.cursor.execute('''
            SELECT id, hsn_code, rate, units, batch_no 
            FROM products 
            WHERE name = ? AND company_id = ? AND units > 0
            ORDER BY dom ASC  -- First In First Out
        ''', (product_name, company_id))
        
        available_batches = self.cursor.fetchall()
        
        if not available_batches:
            messagebox.showerror("Error", "No stock available for this product.")
            return
        
        # Calculate total available units across all batches
        total_available = sum(batch[3] for batch in available_batches)
        
        if quantity > total_available:
            messagebox.showerror("Error", f"Not enough stock. Only {total_available} units available.")
            return
        
        remaining_quantity = quantity
        used_batches = []
        
        # Use units from each batch until the required quantity is met
        for batch in available_batches:
            product_id, hsn_code, rate, available_units, batch_no = batch
            
            if remaining_quantity <= 0:
                break
                
            units_from_this_batch = min(remaining_quantity, available_units)
            
            used_batches.append({
                "id": product_id,
                "name": product_name,
                "hsn_code": hsn_code,
                "batch_no": batch_no,
                "quantity": units_from_this_batch,
                "rate": rate,
                "total": rate * units_from_this_batch
            })
            
            remaining_quantity -= units_from_this_batch
        
        # Add items to bill
        for batch_item in used_batches:
            # Check if this batch already exists in bill
            existing_item = None
            for idx, item in enumerate(self.bill_items):
                if item["id"] == batch_item["id"]:
                    existing_item = (idx, item)
                    break
            
            if existing_item:
                # Update existing item
                idx, item = existing_item
                new_quantity = item["quantity"] + batch_item["quantity"]
                self.bill_items[idx]["quantity"] = new_quantity
                self.bill_items[idx]["total"] = item["rate"] * new_quantity
            else:
                # Add new item
                self.bill_items.append(batch_item)
        
        # Refresh the bill display
        self.refresh_bill_tree()
        self.update_bill_totals()
        
        # Clear selection
        self.quantity_spinbox.delete(0, tk.END)
        self.quantity_spinbox.insert(0, "1")
    
    def refresh_bill_tree(self):
        # Clear tree
        for item in self.bill_tree.get_children():
            self.bill_tree.delete(item)
        
        # Add items to tree
        for idx, item in enumerate(self.bill_items, 1):
            self.bill_tree.insert('', 'end', values=(
                idx,
                item["name"],
                item["hsn_code"],
                item["quantity"],
                f"{item['rate']:.2f}",
                f"{item['total']:.2f}"
            ))
    
    def update_bill_totals(self):
        subtotal = sum(item["total"] for item in self.bill_items)
        tax = subtotal * 0.18  # Assuming flat 18% tax for simplicity
        total = subtotal + tax
        
        self.subtotal_label.config(text=f"₹{subtotal:.2f}")
        self.tax_label.config(text=f"₹{tax:.2f}")
        self.total_label.config(text=f"₹{total:.2f}")
        
        self.total_amount = total
    
    def remove_selected_item(self):
        selected_items = self.bill_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select an item to remove.")
            return
        
        item_idx = int(self.bill_tree.item(selected_items[0], 'values')[0]) - 1
        if 0 <= item_idx < len(self.bill_items):
            del self.bill_items[item_idx]
            self.refresh_bill_tree()
            self.update_bill_totals()
    
    def clear_bill(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the current bill?"):
            self.bill_items = []
            self.refresh_bill_tree()
            self.update_bill_totals()
            
            # Clear customer details
            self.customer_name_entry.delete(0, tk.END)
            self.customer_mobile_entry.delete(0, tk.END)
            self.customer_address_entry.delete(0, tk.END)
            
            self.status_bar.config(text="Bill cleared")
    
    def finalize_bill(self):
        # Check if there are items in the bill
        if not self.bill_items:
            messagebox.showerror("Error", "Cannot finalize an empty bill.")
            return
        
        # Check if customer name is provided
        customer_name = self.customer_name_combo.get().strip()
        if not customer_name:
            messagebox.showerror("Error", "Please select a customer.")
            return
        
        customer_mobile = self.customer_mobile_entry.get().strip()
        customer_address = self.customer_address_entry.get().strip()
        
        # Ask for confirmation
        if not messagebox.askyesno("Confirm", "Finalize this bill?"):
            return
        
        try:
            # Save bill record
            bill_date = datetime.now().strftime('%Y-%m-%d')
            bill_items_json = str(self.bill_items)
            
            self.cursor.execute('''
                INSERT INTO bills (customer_name, customer_mobile, customer_address, 
                                  bill_date, total_amount, bill_items)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_name, customer_mobile, customer_address, 
                  bill_date, self.total_amount, bill_items_json))
            
            bill_id = self.cursor.lastrowid
            
            # Update inventory and check for empty batches
            for item in self.bill_items:
                product_id = item["id"]
                quantity = item["quantity"]
                
                # Get current product details
                self.cursor.execute("""
                    SELECT p.*, c.name as company_name 
                    FROM products p
                    LEFT JOIN companies c ON p.company_id = c.id
                    WHERE p.id = ?
                """, (product_id,))
                product = self.cursor.fetchone()
                
                # Calculate new units
                new_units = product[8] - quantity  # units is at index 8
                
                # Update stock
                self.cursor.execute("UPDATE products SET units = ? WHERE id = ?", 
                                  (new_units, product_id))
                
                # If batch becomes empty, move to history
                if new_units == 0:
                    self.cursor.execute('''
                        INSERT INTO batch_history (
                            product_name, batch_no, company_name, initial_units,
                            dom, expiry, emptied_date
                        ) VALUES (?, ?, ?, ?, ?, ?, date('now'))
                    ''', (
                        product[1],  # product name
                        product[4],  # batch_no
                        product[-1], # company_name
                        product[8],  # initial units
                        product[2],  # dom
                        product[3],  # expiry
                     ))
                    
                    # Log to console for debugging
                    print(f"Added to history: {product[1]} - Batch: {product[4]}")
            
            self.conn.commit()
            
            # Print bill if requested
            if messagebox.askyesno("Success", f"Bill #{bill_id} finalized. Print the bill now?"):
                self.print_bill(bill_id)
            
            # Clear the current bill and refresh all views
            self.bill_items = []
            self.refresh_bill_tree()
            self.update_bill_totals()
            self.clear_customer_selection()
            self.refresh_product_list()  # Refresh inventory to hide empty batches
            
            # If we're in the batch history view, refresh it
            if hasattr(self, 'report_type') and self.report_type.get() == "batch":
                self.generate_batch_report(
                    self.start_date.get_date().strftime('%Y-%m-%d'),
                    self.end_date.get_date().strftime('%Y-%m-%d')
                )
            
            self.status_bar.config(text=f"Bill #{bill_id} finalized successfully")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error in finalize_bill: {str(e)}")  # Debug print
    
    def print_bill(self, bill_id=None):
        if bill_id is None:
            # Print current bill in progress
            if not self.bill_items:
                messagebox.showerror("Error", "No items in the current bill.")
                return
            
            # Get customer details from combo box instead of entry
            customer_name = self.customer_name_combo.get().strip()
            customer_mobile = self.customer_mobile_entry.get().strip()
            customer_address = self.customer_address_entry.get().strip()
            
            if not customer_name:
                messagebox.showerror("Error", "Please select a customer.")
                return
            
            bill_data = {
                "id": "DRAFT",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "customer_name": customer_name,
                "customer_mobile": customer_mobile,
                "customer_address": customer_address,
                "items": self.bill_items,
                "subtotal": sum(item["total"] for item in self.bill_items),
                "tax": sum(item["total"] for item in self.bill_items) * 0.18,
                "total": self.total_amount
            }
        else:
            # Get saved bill data
            self.cursor.execute('''
                SELECT bill_date, customer_name, customer_mobile, 
                       customer_address, bill_items, total_amount
                FROM bills WHERE id = ?
            ''', (bill_id,))
            
            bill = self.cursor.fetchone()
            if not bill:
                messagebox.showerror("Error", f"Bill #{bill_id} not found.")
                return
                
            date, name, mobile, address, items_str, total = bill
            
            try:
                import ast
                items = ast.literal_eval(items_str)
            except:
                messagebox.showerror("Error", "Failed to parse bill items.")
                return
                
            bill_data = {
                "id": bill_id,
                "date": date,
                "customer_name": name,
                "customer_mobile": mobile,
                "customer_address": address,
                "items": items,
                "subtotal": sum(item["total"] for item in items),
                "tax": sum(item["total"] for item in items) * 0.18,
                "total": total
            }
        
        # Generate and open the PDF bill
        try:
            pdf_path = generate_bill_pdf(bill_data)
            if pdf_path:
                if os.name == 'nt':  # For Windows
                    os.startfile(pdf_path)
                else:  # For Linux/Mac
                    import subprocess
                    subprocess.Popen(['xdg-open', pdf_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate bill PDF: {str(e)}")
    
    def generate_report(self):
        start_date = self.start_date.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date.get_date().strftime('%Y-%m-%d')
        
        # Clear existing tree items
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        # Query bills within date range
        self.cursor.execute('''
            SELECT id, bill_date, customer_name, bill_items, total_amount
            FROM bills
            WHERE bill_date BETWEEN ? AND ?
            ORDER BY bill_date DESC
        ''', (start_date, end_date))
        
        bills = self.cursor.fetchall()
        
        total_sales = 0
        for bill in bills:
            bill_id, date, customer, bill_items_str, amount = bill
            
            # Count items
            import ast
            try:
                bill_items = ast.literal_eval(bill_items_str)
                item_count = sum(item["quantity"] for item in bill_items)
            except:
                item_count = 0
            
            self.report_tree.insert('', 'end', values=(
                bill_id,
                date,
                customer,
                item_count,
                f"₹{amount:.2f}"
            ))
            
            total_sales += amount
        
        # Update summary
        self.total_sales_label.config(text=f"₹{total_sales:.2f}")
        self.total_bills_label.config(text=str(len(bills)))
        
        self.status_bar.config(text=f"Generated report from {start_date} to {end_date}")
    
    def export_report(self):
        # This would export the current report to CSV or Excel
        messagebox.showinfo("Info", "Export functionality will be implemented in a future update.")
    
    def print_report(self):
        # This would print the current report
        messagebox.showinfo("Info", "Report printing will be implemented in a future update.")
    
    def view_bill_details(self, event):
        selected_items = self.report_tree.selection()
        if not selected_items:
            return
        
        bill_id = self.report_tree.item(selected_items[0], 'values')[0]
        self.print_bill(bill_id)
    
    def generate_batch_number(self, product_name, arrival_date):
        try:
            # First check if product already has an identifier
            self.cursor.execute('''
                SELECT identifier 
                FROM product_identifiers 
                WHERE product_name = ?
            ''', (product_name,))
            
            existing_identifier = self.cursor.fetchone()
            
            if existing_identifier:
                prefix = existing_identifier[0]
            else:
                # Generate new prefix from product name
                words = [word for word in product_name.strip().split() if word]
                
                if len(words) >= 2:
                    # For multi-word products
                    first_word = words[0].upper()
                    second_word = words[1].upper()
                    possible_prefixes = [
                        first_word[0] + second_word[0],
                        first_word[0] + second_word[-1],
                        first_word[-1] + second_word[0]
                    ]
                else:
                    # For single-word products
                    word = words[0].upper()
                    possible_prefixes = []
                    
                    # Add first + last letter combination
                    if len(word) > 1:
                        possible_prefixes.append(word[0] + word[-1])
                        possible_prefixes.append(word[0] + word[1])
                    else:
                        possible_prefixes.append(word[0] + 'X')
                    
                    # Add numeric combinations
                    for i in range(1, 10):
                        possible_prefixes.append(word[0] + str(i))
                
                # Get all used identifiers
                self.cursor.execute('SELECT identifier FROM product_identifiers')
                used_identifiers = {row[0] for row in self.cursor.fetchall()}
                
                # Find first available prefix
                prefix = None
                for p in possible_prefixes:
                    if p not in used_identifiers:
                        prefix = p
                        break
                
                if not prefix:
                    # If no prefix is available, create one with a number
                    base_letter = words[0][0].upper()
                    counter = 1
                    while f"{base_letter}{counter}" in used_identifiers:
                        counter += 1
                    prefix = f"{base_letter}{counter}"
                
                # Save the new identifier
                try:
                    self.cursor.execute('''
                        INSERT INTO product_identifiers (product_name, identifier)
                        VALUES (?, ?)
                    ''', (product_name, prefix))
                    self.conn.commit()
                except sqlite3.IntegrityError:
                    # Handle rare case of concurrent insertion
                    self.conn.rollback()
                    return self.generate_batch_number(product_name, arrival_date)

            # Add month and year digits (e.g., 0425 for April 2025)
            month_year = f"{arrival_date.month:02d}{str(arrival_date.year)[2:]}"
            batch_base = f"{prefix}{month_year}"

            # Get count of existing batches with same prefix and month/year
            self.cursor.execute('''
                SELECT COUNT(*) 
                FROM products 
                WHERE batch_no LIKE ? || '%' 
                AND strftime('%m%Y', dom) = strftime('%m%Y', ?)
            ''', (batch_base, arrival_date.strftime('%Y-%m-%d')))
            count = self.cursor.fetchone()[0]

            # Generate final batch number with sequence
            batch_no = f"{batch_base}{count + 1}"
            return batch_no
                
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to generate batch number: {str(e)}")
            return None

    def import_from_excel(self):
        try:
            from tkinter import filedialog
            import pandas as pd
            
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if not file_path:
                return
                
            df = pd.read_excel(file_path)
            required_columns = ['Product Name', 'Company Name', 'HSN Code', 
                              'Date of MFG', 'Units', 'MRP', 'Discount']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messagebox.showerror("Error", f"Missing required columns: {', '.join(missing_columns)}")
                return

            def handle_duplicate_batch(existing_product, new_product):
                dialog = tk.Toplevel()
                dialog.title("Duplicate Batch Number Found")
                dialog.geometry("600x400")
                dialog.transient(self.root)
                dialog.grab_set()

                ttk.Label(dialog, text="A product with this batch number already exists. Choose action:").pack(pady=10)

                # Show comparison of both entries
                comparison_frame = ttk.Frame(dialog)
                comparison_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

                ttk.Label(comparison_frame, text="Field").grid(row=0, column=0, padx=5, pady=5)
                ttk.Label(comparison_frame, text="Existing").grid(row=0, column=1, padx=5, pady=5)
                ttk.Label(comparison_frame, text="New").grid(row=0, column=2, padx=5, pady=5)
                ttk.Label(comparison_frame, text="Keep").grid(row=0, column=3, padx=5, pady=5)

                # Compare all fields
                fields = ['Product Name', 'HSN Code', 'Units', 'MRP', 'Discount', 'Rate']
                row_choices = {}

                for idx, field in enumerate(fields, 1):
                    ttk.Label(comparison_frame, text=field).grid(row=idx, column=0, padx=5, pady=2)
                    ttk.Label(comparison_frame, text=str(existing_product[field])).grid(row=idx, column=1, padx=5, pady=2)
                    ttk.Label(comparison_frame, text=str(new_product[field])).grid(row=idx, column=2, padx=5, pady=2)
                    
                    choice_var = tk.StringVar(value="existing")
                    existing_radio = ttk.Radiobutton(comparison_frame, text="", value="existing", variable=choice_var)
                    new_radio = ttk.Radiobutton(comparison_frame, text="", value="new", variable=choice_var)
                    
                    existing_radio.grid(row=idx, column=3, padx=5, pady=2)
                    new_radio.grid(row=idx, column=4, padx=5, pady=2)
                    
                    row_choices[field] = choice_var

                action = tk.StringVar(value="merge")
                
                def on_action_selected():
                    for field in fields:
                        row_choices[field].set("existing" if action.get() == "keep_existing" else "new")

                ttk.Radiobutton(dialog, text="Keep Existing (Delete New)", 
                              value="keep_existing", variable=action,
                              command=on_action_selected).pack(pady=5)
                ttk.Radiobutton(dialog, text="Keep New (Delete Existing)", 
                              value="keep_new", variable=action,
                              command=on_action_selected).pack(pady=5)
                ttk.Radiobutton(dialog, text="Merge (Select fields to keep)", 
                              value="merge", variable=action).pack(pady=5)

                result = {"action": None, "choices": None}

                def on_confirm():
                    result["action"] = action.get()
                    result["choices"] = {field: choice.get() for field, choice in row_choices.items()}
                    dialog.destroy()

                ttk.Button(dialog, text="Confirm", command=on_confirm).pack(pady=10)
                
                dialog.wait_window()
                return result["action"], result["choices"]

            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    company_name = row['Company Name']
                    self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
                    company_result = self.cursor.fetchone()
                    
                    if not company_result:
                        messagebox.showerror("Error", f"Company '{company_name}' not found. Please add company first.")
                        continue
                    
                    company_id = company_result[0]
                    dom = pd.to_datetime(row['Date of MFG']).date()
                    batch_no = self.generate_batch_number(row['Product Name'], dom)

                    # Check for existing batch number
                    self.cursor.execute("SELECT * FROM products WHERE batch_no = ?", (batch_no,))
                    existing_product = self.cursor.fetchone()

                    if existing_product:
                        # Convert existing product to dictionary
                        existing_dict = {
                            'Product Name': existing_product[1],
                            'HSN Code': existing_product[7],
                            'Units': existing_product[8],
                            'MRP': existing_product[5],
                            'Discount': existing_product[6],
                            'Rate': existing_product[9]
                        }

                        # New product dictionary
                        new_dict = {
                            'Product Name': row['Product Name'],
                            'HSN Code': row['HSN Code'],
                            'Units': row['Units'],
                            'MRP': row['MRP'],
                            'Discount': row['Discount'],
                            'Rate': float(row['MRP']) * (1 - float(row['Discount'])/100)
                        }

                        action, choices = handle_duplicate_batch(existing_dict, new_dict)

                        if action == "keep_existing":
                            continue
                        elif action == "keep_new":
                            self.cursor.execute("DELETE FROM products WHERE batch_no = ?", (batch_no,))
                        else:  # merge
                            # Create merged dictionary based on user choices
                            merged_data = {}
                            for field, choice in choices.items():
                                merged_data[field] = existing_dict[field] if choice == "existing" else new_dict[field]

                            # Update existing product with merged data
                            self.cursor.execute('''
                                UPDATE products 
                                SET name=?, hsn_code=?, units=?, mrp=?, discount=?, rate=?
                                WHERE batch_no=?
                            ''', (
                                merged_data['Product Name'],
                                merged_data['HSN Code'],
                                merged_data['Units'],
                                merged_data['MRP'],
                                merged_data['Discount'],
                                merged_data['Rate'],
                                batch_no
                            ))
                            continue

                    # Insert new product if no duplicate or after handling duplicate
                    # ... rest of your existing insert code ...
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {row['Product Name']} - {str(e)}")
            
            self.conn.commit()
            self.refresh_product_list()
            messagebox.showinfo("Import Complete", 
                              f"Successfully imported {success_count} products.\n"
                              f"Failed to import {error_count} products.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {str(e)}")

    def export_to_excel(self):
        try:
            from tkinter import filedialog
            import pandas as pd
            
            # Ask user where to save the Excel file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Export Inventory to Excel"
            )
            
            if not file_path:
                return
                
            # Get all products with company information
            self.cursor.execute('''
                SELECT p.*, c.name as company_name, c.address as company_address,
                       c.gst_number as company_gst
                FROM products p
                LEFT JOIN companies c ON p.company_id = c.id
                ORDER BY p.name
            ''')
            
            columns = [desc[0] for desc in self.cursor.description]
            data = self.cursor.fetchall()
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            # Rename columns for better readability
            column_mapping = {
                'name': 'Product Name',
                'dom': 'Date of MFG',
                'expiry': 'Date of Expiry',
                'batch_no': 'Batch No',
                'mrp': 'MRP',
                'discount': 'Discount (%)',
                'hsn_code': 'HSN Code',
                'units': 'Units',
                'rate': 'Rate',
                'taxable_amount': 'Taxable Amount',
                'igst': 'IGST',
                'cgst': 'CGST',
                'sgst': 'SGST',
                'total_amount': 'Total Amount',
                'amount_in_words': 'Amount in Words',
                'company_name': 'Company Name',
                'company_address': 'Company Address',
                'company_gst': 'Company GST'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Export to Excel
            df.to_excel(file_path, index=False, sheet_name='Inventory')
            
            messagebox.showinfo("Success", "Inventory exported successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def view_product_identifiers(self):
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Product Identifiers")
            dialog.geometry("400x500")
            
            # Create Treeview
            columns = ("product", "identifier")
            tree = ttk.Treeview(dialog, columns=columns, show="headings")
            
            tree.heading("product", text="Product Name")
            tree.heading("identifier", text="Identifier")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Load data
            self.cursor.execute('''
                SELECT product_name, identifier 
                FROM product_identifiers 
                ORDER BY product_name
            ''')
            
            for row in self.cursor.fetchall():
                tree.insert("", "end", values=row)
            
            # Pack widgets
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load product identifiers: {str(e)}")

    def edit_customer(self):
        """Handles editing of selected customer"""
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to edit")
            return
        
        item = self.customers_tree.item(selected[0])
        customer_id = item['values'][0]
        
        self.cursor.execute('''
            SELECT name, mobile, address
            FROM customers
            WHERE id = ?
        ''', (customer_id,))
        
        customer = self.cursor.fetchone()
        if customer:
            # Store the customer ID for update operation
            self.current_editing_customer_id = customer_id
            
            # Populate form with customer details
            self.customer_name_manage.delete(0, tk.END)
            self.customer_name_manage.insert(0, customer[0])
            
            self.customer_mobile_manage.delete(0, tk.END)
            self.customer_mobile_manage.insert(0, customer[1])
            
            self.customer_address_manage.delete(0, tk.END)
            self.customer_address_manage.insert(0, customer[2])
            
            # Change save button to update mode
            self.customer_buttons_frame.children['!button'].config(
                text="Update Customer",
                command=self.update_customer_manage
            )

    def update_customer_manage(self):
        """Updates existing customer details"""
        if not hasattr(self, 'current_editing_customer_id'):
            messagebox.showerror("Error", "No customer selected for update")
            return
            
        name = self.customer_name_manage.get().strip()
        mobile = self.customer_mobile_manage.get().strip()
        address = self.customer_address_manage.get().strip()
        
        if not name or not mobile:
            messagebox.showerror("Error", "Name and Mobile are required!")
            return
        
        try:
            # Check if mobile already exists for another customer
            self.cursor.execute("""
                SELECT name FROM customers 
                WHERE mobile = ? AND id != ?
            """, (mobile, self.current_editing_customer_id))
            existing_mobile = self.cursor.fetchone()
            if existing_mobile:
                messagebox.showerror("Error", f"Mobile number already registered to customer: {existing_mobile[0]}")
                return
                
            self.cursor.execute('''
                UPDATE customers 
                SET name = ?, mobile = ?, address = ?
                WHERE id = ?
            ''', (name, mobile, address, self.current_editing_customer_id))
            
            self.conn.commit()
            self.load_customers_list()
            self.clear_customer_form_manage()
            
            # Reset button and editing state
            self.customer_buttons_frame.children['!button'].config(
                text="Save Customer",
                command=self.save_customer_manage
            )
            del self.current_editing_customer_id
            
            messagebox.showinfo("Success", "Customer updated successfully!")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Mobile number already exists!")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to update: {str(e)}")

    def delete_customer(self):
        """Handles deletion of selected customer"""
        selected = self.customers_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a customer to delete")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this customer?"):
            return
        
        item = self.customers_tree.item(selected[0])
        customer_id = item['values'][0]
        
        try:
            # Check if customer has associated bills
            self.cursor.execute('''
                SELECT COUNT(*) FROM bills 
                WHERE customer_mobile = (
                    SELECT mobile FROM customers WHERE id = ?
                )
            ''', (customer_id,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", 
                    "Cannot delete: This customer has associated bills!")
                return
            
            # Delete the customer
            self.cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
            self.conn.commit()
            self.load_customers_list()
            messagebox.showinfo("Success", "Customer deleted successfully!")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")
    
    def show_customer_menu(self, event):
        """Shows the right-click menu for customers"""
        item = self.customers_tree.identify_row(event.y)
        if item:
            self.customers_tree.selection_set(item)
            self.customer_menu.post(event.x_root, event.y_root)

    def clear_customer_selection(self):
        """Clears customer selection in billing tab"""
        self.customer_name_combo.set('')
        self.customer_mobile_entry.delete(0, tk.END)
        self.customer_address_entry.delete(0, tk.END)

def main():
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
