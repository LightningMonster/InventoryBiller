import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import os
import sys
import re
from fixed_bill_generator import generate_bill_pdf
from utils import convert_to_words

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing & Inventory Management System")
        self.root.geometry("1200x700")
        self.root.state('normal')

        # Configure custom styles
        style = ttk.Style()
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("TButton", padding=10, font=('Helvetica', 10))
        style.configure("Accent.TButton", background="#4CAF50", padding=10, font=('Helvetica', 10, 'bold'))
        style.configure("TEntry", padding=5)
        style.configure("TFrame", background="#f5f5f5")
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Total.TLabel", font=('Helvetica', 14, 'bold'))

        # Configure Treeview
        style.configure("Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            font=('Helvetica', 9)
        )
        style.configure("Treeview.Heading", 
            font=('Helvetica', 10, 'bold'),
            padding=5
        )

        # Configure Notebook tabs
        style.configure("TNotebook", padding=5)
        style.configure("TNotebook.Tab", padding=[10, 5], font=('Helvetica', 10))

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

        # Initially show billing tab
        self.notebook.select(0)

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Check for low stock items on startup
        self.check_low_stock_alert()

    def init_database(self):
        # Determine if running as executable or script
        if getattr(sys, 'frozen', False):
            # Running as executable - use user's documents folder
            user_data_dir = os.path.join(os.path.expanduser("~"), "BillingApp")
            os.makedirs(user_data_dir, exist_ok=True)
            database_path = os.path.join(user_data_dir, "storage.db")

            # Also create a bills directory in the user data folder
            bills_dir = os.path.join(user_data_dir, "bills")
            os.makedirs(bills_dir, exist_ok=True)

            # Always create a fresh database when running as exe
            self.conn = sqlite3.connect(database_path)
            self.cursor = self.conn.cursor()

            # Store the paths
            self.database_path = database_path
            self.user_data_dir = user_data_dir
        else:
            # Running in development mode - use local directory
            app_directory = os.path.dirname(os.path.abspath(__file__))
            database_path = os.path.join(app_directory, "storage.db")

        # Create empty database file if it doesn't exist
        if not os.path.exists(database_path):
            open(database_path, 'w').close()

        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()

        # Store the database and user data paths
        self.database_path = database_path
        if getattr(sys, 'frozen', False):
            self.user_data_dir = user_data_dir
        else:
            self.user_data_dir = app_directory

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
                total_units INTEGER NOT NULL,
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
                gst_number TEXT NOT NULL
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

        self.conn.commit()

    def create_billing_tab(self):
        self.billing_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.billing_tab, text="Billing")

        # Main container with left and right panels
        billing_paned = ttk.PanedWindow(self.billing_tab, orient=tk.HORIZONTAL)
        billing_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel for customer details and item selection
        left_frame = ttk.Frame(billing_paned)
        billing_paned.add(left_frame, weight=1)

        # Right panel for bill preview
        right_frame = ttk.Frame(billing_paned)
        billing_paned.add(right_frame, weight=1)

        # Customer Details Frame
        customer_frame = ttk.LabelFrame(left_frame, text="Customer Details", padding=10)
        customer_frame.pack(fill=tk.X, padx=10, pady=10)

        # Customer Details Grid
        customer_grid = ttk.Frame(customer_frame)
        customer_grid.pack(fill=tk.X, padx=5, pady=5)

        # Customer Name
        ttk.Label(customer_grid, text="Customer Name*:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_name_entry = ttk.Entry(customer_grid, width=30)
        self.customer_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

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
        add_button = ttk.Button(item_frame, text="Add Item", command=self.add_item_to_bill, style="Accent.TButton")
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
        self.total_label = ttk.Label(summary_frame, text="₹0.00", width=12, style="Total.TLabel")
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

    def create_storage_tab(self):
        self.storage_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.storage_tab, text="Inventory")

        # Create main canvas for scrolling
        main_canvas = tk.Canvas(self.storage_tab)
        scrollbar = ttk.Scrollbar(self.storage_tab, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Create main container frame
        main_container = ttk.Frame(main_canvas)
        main_container.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        # Create window in canvas
        main_canvas.create_window((0, 0), window=main_container, anchor="nw", width=main_canvas.winfo_width())

        # Configure canvas to expand
        main_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # Configure canvas scrolling
        main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig(main_canvas.find_all()[0], width=e.width-10))
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

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
        self.product_name_entry = ttk.Entry(grid_frame, width=30)
        self.product_name_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="HSN Code*:").grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)
        self.hsn_code_entry = ttk.Entry(grid_frame, width=20)
        self.hsn_code_entry.grid(row=4, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Date of Manufacture*:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.dom_picker = DateEntry(grid_frame, width=17, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.dom_picker.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Expiry Date*:").grid(row=5, column=2, padx=5, pady=5, sticky=tk.W)
        self.expiry_picker = DateEntry(grid_frame, width=17, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.expiry_picker.grid(row=5, column=3, padx=5, pady=5, sticky=tk.W)
        self.expiry_picker.set_date(datetime.now() + timedelta(days=365))  # Default to 1 year from now

        ttk.Label(grid_frame, text="Batch No*:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        self.batch_no_entry = ttk.Entry(grid_frame, width=30)
        self.batch_no_entry.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Units*:").grid(row=6, column=2, padx=5, pady=5, sticky=tk.W)
        self.units_spinbox = ttk.Spinbox(grid_frame, from_=0, to=10000, increment=1, width=10)
        self.units_spinbox.grid(row=6, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Total Units*:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
        self.total_units_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=1, width=10)
        self.total_units_spinbox.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="MRP*:").grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
        self.mrp_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=0.01, format="%.2f", width=12)
        self.mrp_spinbox.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Discount (%)*:").grid(row=8, column=2, padx=5, pady=5, sticky=tk.W)
        self.discount_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.discount_spinbox.grid(row=8, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Rate*:").grid(row=9, column=0, padx=5, pady=5, sticky=tk.W)
        self.rate_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=0.01, format="%.2f", width=12)
        self.rate_spinbox.grid(row=9, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="Taxable Amount*:").grid(row=9, column=2, padx=5, pady=5, sticky=tk.W)
        self.taxable_amount_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100000, increment=0.01, format="%.2f", width=12)
        self.taxable_amount_spinbox.grid(row=9, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="IGST*:").grid(row=10, column=0, padx=5, pady=5, sticky=tk.W)
        self.igst_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.igst_spinbox.grid(row=10, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="CGST*:").grid(row=10, column=2, padx=5, pady=5, sticky=tk.W)
        self.cgst_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.cgst_spinbox.grid(row=10, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(grid_frame, text="SGST*:").grid(row=11, column=0, padx=5, pady=5, sticky=tk.W)
        self.sgst_spinbox = ttk.Spinbox(grid_frame, from_=0, to=100, increment=0.01, format="%.2f", width=10)
        self.sgst_spinbox.grid(row=11, column=1, padx=5, pady=5, sticky=tk.W)

        # Calculate button
        calculate_btn = ttk.Button(grid_frame, text="Calculate Amounts", command=self.calculate_product_amounts)
        calculate_btn.grid(row=11, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Button Frame
        btn_frame = ttk.Frame(grid_frame)
        btn_frame.grid(row=12, column=0, columnspan=4, pady=10, sticky=tk.EW)

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

        # Inventory TreeView
        # Create a frame to hold the treeview and scrollbars
        scrollable_frame = ttk.Frame(bottom_frame)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(scrollable_frame, orient="vertical")
        x_scrollbar = ttk.Scrollbar(scrollable_frame, orient="horizontal")
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Configure the treeview with scrollbars
        self.inventory_tree = ttk.Treeview(scrollable_frame, columns=(
            "id", "name", "hsn", "company", "batch", "expiry", "units", "total_units", 
            "mrp", "discount", "rate", "taxable_amount", "igst", "cgst", "sgst"
        ), show="headings", height=10, yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Configure scrollbar commands
        y_scrollbar.config(command=self.inventory_tree.yview)
        x_scrollbar.config(command=self.inventory_tree.xview)

        # Define headings
        self.inventory_tree.heading("id", text="ID")
        self.inventory_tree.heading("name", text="Product Name")
        self.inventory_tree.heading("hsn", text="HSN Code")
        self.inventory_tree.heading("company", text="Company")
        self.inventory_tree.heading("batch", text="Batch No")
        self.inventory_tree.heading("expiry", text="Expiry Date")
        self.inventory_tree.heading("units", text="Units")
        self.inventory_tree.heading("total_units", text="Total Units")
        self.inventory_tree.heading("mrp", text="MRP")
        self.inventory_tree.heading("discount", text="Discount %")
        self.inventory_tree.heading("rate", text="Rate")
        self.inventory_tree.heading("taxable_amount", text="Taxable Amount")
        self.inventory_tree.heading("igst", text="IGST")
        self.inventory_tree.heading("cgst", text="CGST")
        self.inventory_tree.heading("sgst", text="SGST")

        # Column widths
        self.inventory_tree.column("id", width=50)
        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("hsn", width=100)
        self.inventory_tree.column("company", width=120)
        self.inventory_tree.column("batch", width=100)
        self.inventory_tree.column("expiry", width=100)
        self.inventory_tree.column("units", width=60)
        self.inventory_tree.column("total_units", width=80)
        self.inventory_tree.column("mrp", width=80)
        self.inventory_tree.column("discount", width=80)
        self.inventory_tree.column("rate", width=80)
        self.inventory_tree.column("taxable_amount", width=100)
        self.inventory_tree.column("igst", width=80)
        self.inventory_tree.column("cgst", width=80)
        self.inventory_tree.column("sgst", width=80)

        # Column widths
        self.inventory_tree.column("id", width=50)
        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("hsn", width=100)
        self.inventory_tree.column("company", width=120)
        self.inventory_tree.column("batch", width=100)
        self.inventory_tree.column("expiry", width=100)
        self.inventory_tree.column("units", width=60)
        self.inventory_tree.column("mrp", width=80)
        self.inventory_tree.column("rate", width=80)

        # Pack the treeview and scrollbars
        self.inventory_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)


        # Right-click menu for tree
        self.tree_menu = tk.Menu(self.inventory_tree, tearoff=0)
        self.tree_menu.add_command(label="Edit", command=self.edit_selected_product)
        self.tree_menu.add_command(label="Delete", command=self.delete_selected_product)

        self.inventory_tree.bind("<Button-3>", self.show_tree_menu)
        self.inventory_tree.bind("<Double-1>", lambda event: self.edit_selected_product())

        # Load products
        self.refresh_product_list()

    def create_reports_tab(self):
        self.reports_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_tab, text="Reports")

        # Reports container
        reports_frame = ttk.Frame(self.reports_tab)
        reports_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Date range selection
        date_frame = ttk.LabelFrame(reports_frame, text="Select Date Range")
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(date_frame, text="From Date:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_date = DateEntry(date_frame, width=17, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(date_frame, text="To Date:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.end_date = DateEntry(date_frame, width=17, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        generate_btn = ttk.Button(date_frame, text="Generate Report", command=self.generate_report)
        generate_btn.grid(row=0, column=4, padx=15, pady=5, sticky=tk.W)

        # Report display
        report_display = ttk.LabelFrame(reports_frame, text="Sales Report")
        report_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Report columns
        columns = ("id", "date", "customer", "items", "amount")
        self.report_tree = ttk.Treeview(report_display, columns=columns, show="headings", height=15)

        # Define headings
        self.report_tree.heading("id", text="Bill #")
        self.report_tree.heading("date", text="Date")
        self.report_tree.heading("customer", text="Customer")
        self.report_tree.heading("items", text="Items Count")
        self.report_tree.heading("amount", text="Total Amount")

        # Column widths
        self.report_tree.column("id", width=60)
        self.report_tree.column("date", width=100)
        self.report_tree.column("customer", width=200)
        self.report_tree.column("items", width=100)
        self.report_tree.column("amount", width=120)

        # Scrollbar
        report_scroll = ttk.Scrollbar(report_display, orient="vertical", command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=report_scroll.set)

        # Packing
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        report_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Summary frame
        summary_frame = ttk.Frame(reports_frame)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(summary_frame, text="Total Sales:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.total_sales_label = ttk.Label(summary_frame, text="₹0.00", font=('Arial', 10, 'bold'))
        self.total_sales_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(summary_frame, text="Total Bills:").grid(row=0, column=2, padx=15, pady=5, sticky=tk.E)
        self.total_bills_label = ttk.Label(summary_frame, text="0", font=('Arial', 10, 'bold'))
        self.total_bills_label.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # Action buttons
        button_frame = ttk.Frame(reports_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        export_btn = ttk.Button(button_frame, text="Export Report", command=self.export_report)
        export_btn.pack(side=tk.LEFT, padx=5)

        print_report_btn = ttk.Button(button_frame, text="Print Report", command=self.print_report)
        print_report_btn.pack(side=tk.LEFT, padx=5)

        # Double-click to view bill details
        self.report_tree.bind("<Double-1>", self.view_bill_details)

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

    def company_selected(self, event=None):
        selected_company = self.company_name_combobox.get()
        if selected_company:
            self.cursor.execute("SELECT address, gst_number FROM companies WHERE name = ?", (selected_company,))
            result = self.cursor.fetchone()
            if result:
                self.company_address_entry.delete(0, tk.END)
                self.company_address_entry.insert(0, result[0])
                self.company_gst_entry.delete(0, tk.END)
                self.company_gst_entry.insert(0, result[1])

    def add_new_company(self):
        company_dialog = tk.Toplevel(self.root)
        company_dialog.title("Add New Company")
        company_dialog.geometry("400x300")
        company_dialog.transient(self.root)
        company_dialog.grab_set()

        # Create form fields
        ttk.Label(company_dialog, text="Company Name*:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(company_dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(company_dialog, text="Address*:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        address_entry = ttk.Entry(company_dialog, width=30)
        address_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(company_dialog, text="GST Number*:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        gst_entry = ttk.Entry(company_dialog, width=30)
        gst_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        def save_and_close():
            name = name_entry.get().strip()
            address = address_entry.get().strip()
            gst = gst_entry.get().strip()

            if not name or not address or not gst:
                messagebox.showerror("Error", "Please fill all required fields.")
                return

            # Validate GST format (15 chars, alphanumeric)
            if not re.match(r'^[0-9A-Z]{15}$', gst):
                messagebox.showerror("Error", "Invalid GST Number format. It should be 15 alphanumeric characters.")
                return

            try:
                self.cursor.execute("INSERT INTO companies (name, address, gst_number) VALUES (?, ?, ?)", 
                                   (name, address, gst))
                self.conn.commit()
                messagebox.showinfo("Success", "Company added successfully.")
                self.load_companies()
                self.load_companies_for_billing()
                self.company_name_combobox.set(name)
                self.company_selected()
                company_dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", f"Company '{name}' already exists.")

        # Save Button
        save_btn = ttk.Button(company_dialog, text="Save Company", command=save_and_close)
        save_btn.grid(row=3, column=1, padx=10, pady=20, sticky=tk.E)

        # Cancel Button
        cancel_btn = ttk.Button(company_dialog, text="Cancel", command=company_dialog.destroy)
        cancel_btn.grid(row=3, column=0, padx=10, pady=20, sticky=tk.W)

    def save_company(self):
        name = self.company_name_combobox.get().strip()
        address = self.company_address_entry.get().strip()
        gst = self.company_gst_entry.get().strip()

        if not name or not address or not gst:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        # Validate GST format (15 chars, alphanumeric)
        if not re.match(r'^[0-9A-Z]{15}$', gst):
            messagebox.showerror("Error", "Invalid GST Number format. It should be 15 alphanumeric characters.")
            return

        try:
            # Check if company exists
            self.cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
            result = self.cursor.fetchone()

            if result:
                # Update existing company
                self.cursor.execute("UPDATE companies SET address = ?, gst_number = ? WHERE name = ?", 
                                   (address, gst, name))
                self.conn.commit()
                messagebox.showinfo("Success", "Company updated successfully.")
            else:
                # Insert new company
                self.cursor.execute("INSERT INTO companies (name, address, gst_number) VALUES (?, ?, ?)", 
                                   (name, address, gst))
                self.conn.commit()
                messagebox.showinfo("Success", "Company added successfully.")

            self.load_companies()
            self.load_companies_for_billing()
            self.status_bar.config(text=f"Company '{name}' saved successfully")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def calculate_product_amounts(self):
        try:
            # Get inputs
            mrp = float(self.mrp_spinbox.get())
            discount_percent = float(self.discount_spinbox.get())
            units = int(self.units_spinbox.get())
            rate = float(self.rate_spinbox.get())

            # Calculate discounted amount
            discount_amount = mrp * (discount_percent / 100)
            discounted_price = mrp - discount_amount
            
            # Calculate taxable amount
            taxable_amount = discounted_price * units
            
            # Calculate GST components (assuming 18% total)
            igst = taxable_amount * 0.18
            cgst = taxable_amount * 0.09
            sgst = taxable_amount * 0.09
            
            # Total amount including tax
            total_amount = taxable_amount + igst

            # Calculate rate (MRP minus discount)
            rate = mrp * (1 - discount_percent/100)

            # Calculate taxable amount (rate × units)
            taxable_amount = rate * units

            # Assume GST rates (these could be retrieved from HSN code in a real app)
            # For simplicity, we'll use 18% total GST (9% CGST, 9% SGST)
            igst = taxable_amount * 0.18
            cgst = taxable_amount * 0.09
            sgst = taxable_amount * 0.09

            # Update fields
            self.rate_spinbox.delete(0, tk.END)
            self.rate_spinbox.insert(0, f"{rate:.2f}")

            self.taxable_amount_spinbox.delete(0, tk.END)
            self.taxable_amount_spinbox.insert(0, f"{taxable_amount:.2f}")

            self.igst_spinbox.delete(0, tk.END)
            self.igst_spinbox.insert(0, f"{igst:.2f}")

            self.cgst_spinbox.delete(0, tk.END)
            self.cgst_spinbox.insert(0, f"{cgst:.2f}")

            self.sgst_spinbox.delete(0, tk.END)
            self.sgst_spinbox.insert(0, f"{sgst:.2f}")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers.")

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
        name = self.product_name_entry.get().strip()
        dom = self.dom_picker.get_date().strftime('%Y-%m-%d')
        expiry = self.expiry_picker.get_date().strftime('%Y-%m-%d')
        batch_no = self.batch_no_entry.get().strip()
        hsn_code = self.hsn_code_entry.get().strip()

        # Validate required fields
        if not name or not batch_no or not hsn_code:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        try:
            mrp = float(self.mrp_spinbox.get())
            discount = float(self.discount_spinbox.get())
            units = int(self.units_spinbox.get())
            total_units = int(self.total_units_spinbox.get()) # Get total units
            rate = float(self.rate_spinbox.get())
            taxable_amount = float(self.taxable_amount_spinbox.get())
            igst = float(self.igst_spinbox.get())
            cgst = float(self.cgst_spinbox.get())
            sgst = float(self.sgst_spinbox.get())

            # Calculate total amount
            total_amount = taxable_amount + igst

            # Convert total to words
            amount_in_words = convert_to_words(total_amount)

            # Check if total_units column exists
            self.cursor.execute("PRAGMA table_info(products)")
            columns = [column[1] for column in self.cursor.fetchall()]

            # Insert product with or without total_units based on schema
            if 'total_units' in columns:
                # Insert with total_units
                self.cursor.execute('''
                    INSERT INTO products (name, dom, expiry, batch_no, mrp, discount, hsn_code, 
                                         units, total_units, rate, taxable_amount, igst, cgst, sgst, 
                                         total_amount, amount_in_words, company_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, dom, expiry, batch_no, mrp, discount, hsn_code, units, total_units, rate, taxable_amount, 
                      igst, cgst, sgst, total_amount, amount_in_words, company_id))
            else:
                # Insert without total_units (backward compatibility)
                # First, try to add the column if it doesn't exist
                try:
                    self.cursor.execute("ALTER TABLE products ADD COLUMN total_units INTEGER DEFAULT 0")
                    self.conn.commit()
                    # Now the column exists, so use the version with total_units
                    self.cursor.execute('''
                        INSERT INTO products (name, dom, expiry, batch_no, mrp, discount, hsn_code, 
                                             units, total_units, rate, taxable_amount, igst, cgst, sgst, 
                                             total_amount, amount_in_words, company_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, dom, expiry, batch_no, mrp, discount, hsn_code, units, total_units, rate, taxable_amount, 
                          igst, cgst, sgst, total_amount, amount_in_words, company_id))
                except sqlite3.OperationalError:
                    # If we can't add the column, use the old schema without total_units
                    self.cursor.execute('''
                        INSERT INTO products (name, dom, expiry, batch_no, mrp, discount, hsn_code, 
                                             units, rate, taxable_amount, igst, cgst, sgst, 
                                             total_amount, amount_in_words, company_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, dom, expiry, batch_no, mrp, discount, hsn_code, units, rate, taxable_amount, 
                          igst, cgst, sgst, total_amount, amount_in_words, company_id))

            self.conn.commit()
            messagebox.showinfo("Success", "Product saved successfully.")
            self.clear_product_form()
            self.refresh_product_list()
            self.status_bar.config(text=f"Product '{name}' saved successfully")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all numeric fields.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def clear_product_form(self):
        self.product_name_entry.delete(0, tk.END)
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
        self.total_units_spinbox.delete(0, tk.END)
        self.total_units_spinbox.insert(0, "0")
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

        # Check if total_units column exists
        self.cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in self.cursor.fetchall()]

        # Use appropriate query based on whether total_units exists
        if 'total_units' in columns:
            # Get products with company names and total_units
            self.cursor.execute('''
                SELECT p.id, p.name, p.hsn_code, c.name, p.batch_no, p.expiry, p.units, p.mrp, p.rate, p.total_units
                FROM products p
                LEFT JOIN companies c ON p.company_id = c.id
                ORDER BY p.name
            ''')
        else:
            # Get products without total_units (for backward compatibility)
            self.cursor.execute('''
                SELECT p.id, p.name, p.hsn_code, c.name, p.batch_no, p.expiry, p.units, p.mrp, p.rate
                FROM products p
                LEFT JOIN companies c ON p.company_id = c.id
                ORDER BY p.name
            ''')

        products = self.cursor.fetchall()

        for product in products:
            # Check if it's a low stock item (less than 25% of total)
            units = product[6]  # Current units

            # If total_units column exists, use it, otherwise use current units
            if 'total_units' in columns and len(product) > 9:
                total_units = product[9] if product[9] else units  # Total units or current if total not set
            else:
                total_units = units  # Just use current units as total if column doesn't exist

            # Calculate if low stock (less than 25% of total)
            is_low_stock = False
            if total_units > 0:
                percentage = (units / total_units) * 100
                is_low_stock = percentage < 25

            # Change color for low stock items
            tag = 'low_stock' if is_low_stock else ''

            # If we have total_units, exclude it from display values
            if 'total_units' in columns and len(product) > 9:
                display_values = product[:-1]
            else:
                display_values = product

            item_id = self.inventory_tree.insert('', 'end', values=display_values, tags=(tag,))

            # If low stock, add a note in the status column
            if is_low_stock:
                self.inventory_tree.item(item_id, text="⚠️ Low Stock")

        # Configure the tag for low stock items
        self.inventory_tree.tag_configure('low_stock', background='#ffcccc')

    def search_products(self):
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.refresh_product_list()
            return

        # Clear the treeview
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        # Check if total_units column exists
        self.cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in self.cursor.fetchall()]

        # Use appropriate query based on whether total_units exists
        if 'total_units' in columns:
            # Search by name, HSN code, or batch number with total_units
            self.cursor.execute('''
                SELECT p.id, p.name, p.hsn_code, c.name, p.batch_no, p.expiry, p.units, p.mrp, p.rate, p.total_units
                FROM products p
                LEFT JOIN companies c ON p.company_id = c.id
                WHERE p.name LIKE ? OR p.hsn_code LIKE ? OR p.batch_no LIKE ?
                ORDER BY p.name
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        else:
            # Search without total_units (for backward compatibility)
            self.cursor.execute('''
                SELECT p.id, p.name, p.hsn_code, c.name, p.batch_no, p.expiry, p.units, p.mrp, p.rate
                FROM products p
                LEFT JOIN companies c ON p.company_id = c.id
                WHERE p.name LIKE ? OR p.hsn_code LIKE ? OR p.batch_no LIKE ?
                ORDER BY p.name
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))

        products = self.cursor.fetchall()

        for product in products:
            # Check if it's a low stock item (less than 25% of total)
            units = product[6]  # Current units

            # If total_units column exists, use it, otherwise use current units
            if 'total_units' in columns and len(product) > 9:
                total_units = product[9] if product[9] else units  # Total units or current if total not set
            else:
                total_units = units  # Just use current units as total if column doesn't exist

            # Calculate if low stock (less than 25% of total)
            is_low_stock = False
            if total_units > 0:
                percentage = (units / total_units) * 100
                is_low_stock = percentage < 25

            # Change color for low stock items
            tag = 'low_stock' if is_low_stock else ''

            # If we have total_units, exclude it from display values
            if 'total_units' in columns and len(product) > 9:
                display_values = product[:-1]
            else:
                display_values = product

            item_id = self.inventory_tree.insert('', 'end', values=display_values, tags=(tag,))

            # If low stock, add a note in the status column
            if is_low_stock:
                self.inventory_tree.item(item_id, text="⚠️ Low Stock")

        # Configure the tag for low stock items
        self.inventory_tree.tag_configure('low_stock', background='#ffcccc')

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
        menubar.add_cascade(label="Navigation", menu=nav_menu)

        # Bills menu - new menu for bill management
        bills_menu = tk.Menu(menubar, tearoff=0)
        bills_menu.add_command(label="Open Bills Folder", command=self.open_bills_folder)
        bills_menu.add_command(label="View Last Bill", command=self.view_last_bill)
        menubar.add_cascade(label="Bills", menu=bills_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Quick Start Guide", command=self.show_quick_start_guide)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_keyboard_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Set the menu for the root window
        self.root.config(menu=menubar)

    def show_quick_start_guide(self):
        help_text = """
Quick Start Guide:

1. Billing
   • Select a company from the dropdown
   • Choose products to add to the bill
   • Set quantities for each item
   • Click 'Add Item' to include in bill
   • Use 'Finalize Bill' when done
   • Print or save the bill as needed

2. Inventory Management
   • Use the Inventory tab to manage products
   • Add new products with the form
   • Right-click items to edit or delete
   • Watch for low stock alerts (in red)

3. Reports
   • Select date range
   • Generate reports of sales
   • Export or print reports as needed

Need more help? Check the keyboard shortcuts!
"""
        messagebox.showinfo("Quick Start Guide", help_text)

    def show_keyboard_shortcuts(self):
        shortcuts_text = """
Keyboard Shortcuts:

• Ctrl + B: Switch to Billing tab
• Ctrl + I: Switch to Inventory tab
• Ctrl + R: Switch to Reports tab
• Ctrl + P: Print current bill
• Ctrl + F: Finalize bill
• Ctrl + N: Clear current bill
• F5: Refresh product list
• Esc: Clear form fields
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)

    def show_about(self):
        about_text = """
Billing & Inventory Management System
Version 1.0

A comprehensive billing and inventory management 
solution for small to medium businesses.

Features:
• Product and inventory management
• Bill generation and printing
• Sales reporting
• Low stock alerts
• Multi-company support

Developer: Yash Dhadve

© 2024 All Rights Reserved
"""
        messagebox.showinfo("About", about_text)

        # Set the menu for the root window
        self.root.config(menu=menubar)

    def open_bills_folder(self):
        """Open the folder containing generated bills"""
        # Use the user_data_dir for bills if running as executable
        if getattr(sys, 'frozen', False):
            bills_dir = os.path.join(self.user_data_dir, "bills")
        else:
            bills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills")

        # Create the directory if it doesn't exist
        if not os.path.exists(bills_dir):
            os.makedirs(bills_dir)

        try:
            # Different commands based on OS
            if os.name == 'nt':  # For Windows
                os.startfile(bills_dir)
            elif os.name == 'posix':  # For macOS and Linux
                import subprocess
                subprocess.Popen(['xdg-open', bills_dir])
            self.status_bar.config(text=f"Opened bills folder: {bills_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open bills folder: {str(e)}")

    def view_last_bill(self):
        """View the most recently generated bill"""
        # Use the user_data_dir for bills if running as executable
        if getattr(sys, 'frozen', False):
            bills_dir = os.path.join(self.user_data_dir, "bills")
        else:
            bills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills")

        if not os.path.exists(bills_dir):
            messagebox.showinfo("Info", "No bills have been generated yet.")
            return

        # Get list of PDF files in the bills directory
        bill_files = [f for f in os.listdir(bills_dir) if f.lower().endswith('.pdf')]

        if not bill_files:
            messagebox.showinfo("Info", "No bills have been generated yet.")
            return

        # Sort by modification time (newest first)
        bill_files.sort(key=lambda x: os.path.getmtime(os.path.join(bills_dir, x)), reverse=True)

        # Open the most recent bill
        latest_bill = os.path.join(bills_dir, bill_files[0])
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
        """Update an existing product with new information"""
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
            messagebox.showerror("Error", "Company not found. Please save the company first.")
            return

        company_id = company_result[0]

        # Get product details
        name = self.product_name_entry.get().strip()
        dom = self.dom_picker.get_date().strftime('%Y-%m-%d')
        expiry = self.expiry_picker.get_date().strftime('%Y-%m-%d')
        batch_no = self.batch_no_entry.get().strip()
        hsn_code = self.hsn_code_entry.get().strip()

        # Validate required fields
        if not name or not batch_no or not hsn_code:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        try:
            mrp = float(self.mrp_spinbox.get())
            discount = float(self.discount_spinbox.get())
            units = int(self.units_spinbox.get())
            total_units = int(self.total_units_spinbox.get()) # Get total units
            rate = float(self.rate_spinbox.get())
            taxable_amount = float(self.taxable_amount_spinbox.get())
            igst = float(self.igst_spinbox.get())
            cgst = float(self.cgst_spinbox.get())
            sgst = float(self.sgst_spinbox.get())

            # Calculate total amount
            total_amount = taxable_amount + igst

            # Convert total to words
            amount_in_words = convert_to_words(total_amount)

            # Check if total_units column exists
            self.cursor.execute("PRAGMA table_info(products)")
            columns = [column[1] for column in self.cursor.fetchall()]

            # Update product with or without total_units based on schema
            if 'total_units' in columns:
                # Update with total_units
                self.cursor.execute('''
                    UPDATE products 
                    SET name=?, dom=?, expiry=?, batch_no=?, mrp=?, discount=?, 
                        hsn_code=?, units=?, total_units=?, rate=?, taxable_amount=?, igst=?, 
                        cgst=?, sgst=?, total_amount=?, amount_in_words=?, 
                        company_id=?
                    WHERE id=?
                ''', (name, dom, expiry, batch_no, mrp, discount, hsn_code, units, total_units,
                     rate, taxable_amount, igst, cgst, sgst, total_amount, 
                     amount_in_words, company_id, self.current_editing_product_id))
            else:
                # Update without total_units (backward compatibility)
                # First, try to add the column if it doesn't exist
                try:
                    self.cursor.execute("ALTER TABLE products ADD COLUMN total_units INTEGER DEFAULT 0")
                    self.conn.commit()
                    # Now the column exists, so use the version with total_units
                    self.cursor.execute('''
                        UPDATE products 
                        SET name=?, dom=?, expiry=?, batch_no=?, mrp=?, discount=?, 
                            hsn_code=?, units=?, total_units=?, rate=?, taxable_amount=?, igst=?, 
                            cgst=?, sgst=?, total_amount=?, amount_in_words=?, 
                            company_id=?
                        WHERE id=?
                    ''', (name, dom, expiry, batch_no, mrp, discount, hsn_code, units, total_units,
                         rate, taxable_amount, igst, cgst, sgst, total_amount, 
                         amount_in_words, company_id, self.current_editing_product_id))
                except sqlite3.OperationalError:
                    # If we can't add the column, use the old schema without total_units
                    self.cursor.execute('''
                        UPDATE products 
                        SET name=?, dom=?, expiry=?, batch_no=?, mrp=?, discount=?, 
                            hsn_code=?, units=?, rate=?, taxable_amount=?, igst=?, 
                            cgst=?, sgst=?, total_amount=?, amount_in_words=?, 
                            company_id=?
                        WHERE id=?
                    ''', (name, dom, expiry, batch_no, mrp, discount, hsn_code, units,
                         rate, taxable_amount, igst, cgst, sgst, total_amount, 
                         amount_in_words, company_id, self.current_editing_product_id))

            self.conn.commit()
            messagebox.showinfo("Success", "Product updated successfully.")
            self.clear_product_form()
            self.refresh_product_list()
            self.status_bar.config(text=f"Product '{name}' updated successfully")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all numeric fields.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

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
        self.product_name_entry.delete(0, tk.END)
        self.product_name_entry.insert(0, product[1])  # name

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

        # Get total units - might be at different index depending on the column position
        total_units_idx = None
        self.cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'total_units' in columns:
            total_units_idx = columns.index('total_units')
            # Ensure we have enough columns in the product tuple
            if total_units_idx < len(product):
                self.total_units_spinbox.delete(0, tk.END)
                self.total_units_spinbox.insert(0, product[total_units_idx])
            else:
                # Default to current units if total_units not available
                self.total_units_spinbox.delete(0, tk.END)
                self.total_units_spinbox.insert(0, product[8])  # Use units as default

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
        company_name = self.bill_company_combobox.get()
        if not company_name:
            return

        # Get company ID
        self.cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
        company_result = self.cursor.fetchone()
        if not company_result:
            return

        company_id = company_result[0]

        # Get products for this company
        self.cursor.execute('''
            SELECT id, name FROM products 
            WHERE company_id = ? AND units > 0
            ORDER BY name
        ''', (company_id,))

        products = self.cursor.fetchall()
        product_names = [f"{product[1]}" for product in products]
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

        # Get product details
        self.cursor.execute('''
            SELECT id, hsn_code, rate, units FROM products 
            WHERE name = ? AND company_id = ?
        ''', (product_name, company_id))

        product = self.cursor.fetchone()
        if not product:
            messagebox.showerror("Error", "Product not found.")
            return

        product_id, hsn_code, rate, available_units = product

        if quantity > available_units:
            messagebox.showerror("Error", f"Not enough stock. Only {available_units} units available.")
            return

        # Calculate item total
        item_total = rate * quantity

        # Add to bill items
        item_data = {
            "id": product_id,
            "name": product_name,
            "hsn_code": hsn_code,
            "quantity": quantity,
            "rate": rate,
            "total": item_total
        }

        # Check if item already exists in bill
        for idx, item in enumerate(self.bill_items):
            if item["id"] == product_id:
                # Update quantity and total
                new_quantity = item["quantity"] + quantity
                if new_quantity > available_units:
                    messagebox.showerror("Error", f"Not enough stock. Only {available_units} units available.")
                    return

                self.bill_items[idx]["quantity"] = new_quantity
                self.bill_items[idx]["total"] = rate * new_quantity

                # Update the tree
                self.refresh_bill_tree()
                self.update_bill_totals()
                return

        # Add new item
        self.bill_items.append(item_data)

        # Add item to tree
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
        customer_name = self.customer_name_entry.get().strip()
        if not customer_name:
            messagebox.showerror("Error", "Please enter customer name.")
            return

        customer_mobile = self.customer_mobile_entry.get().strip()
        customer_address = self.customer_address_entry.get().strip()

        # Ask for confirmation
        if not messagebox.askyesno("Confirm", "Finalize this bill?"):
            return

        try:
            # Save bill record
            bill_date = datetime.now().strftime('%Y-%m-%d')
            bill_items_json = str(self.bill_items)  # Simple conversion to string

            self.cursor.execute('''
                INSERT INTO bills (customer_name, customer_mobile, customer_address, 
                                  bill_date, total_amount, bill_items)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_name, customer_mobile, customer_address, 
                  bill_date, self.total_amount, bill_items_json))

            bill_id = self.cursor.lastrowid

            # Update inventory (reduce stock)
            for item in self.bill_items:
                product_id = item["id"]
                quantity = item["quantity"]

                # Get current units
                self.cursor.execute("SELECT units FROM products WHERE id = ?", (product_id,))
                current_units = self.cursor.fetchone()[0]

                # Update stock
                new_units = current_units - quantity
                self.cursor.execute("UPDATE products SET units = ? WHERE id = ?", (new_units, product_id))

            self.conn.commit()

            # Print bill if requested
            if messagebox.askyesno("Success", f"Bill #{bill_id} finalized. Print the bill now?"):
                self.print_bill(bill_id)

            # Clear the current bill
            self.bill_items = []
            self.refresh_bill_tree()
            self.update_bill_totals()

            # Clear customer details
            self.customer_name_entry.delete(0, tk.END)
            self.customer_mobile_entry.delete(0, tk.END)
            self.customer_address_entry.delete(0, tk.END)

            self.status_bar.config(text=f"Bill #{bill_id} finalized successfully")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def print_bill(self, bill_id=None):
        if bill_id is None:
            # Print current bill in progress
            if not self.bill_items:
                messagebox.showerror("Error", "No items in the current bill.")
                return

            customer_name = self.customer_name_entry.get().strip()
            customer_mobile = self.customer_mobile_entry.get().strip()
            customer_address = self.customer_address_entry.get().strip()

            if not customer_name:
                messagebox.showerror("Error", "Please enter customer name.")
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
            # Print existing bill
            self.cursor.execute('''
                SELECT id, bill_date, customer_name, customer_mobile, 
                       customer_address, bill_items, total_amount
                FROM bills WHERE id = ?
            ''', (bill_id,))

            bill_record = self.cursor.fetchone()
            if not bill_record:
                messagebox.showerror("Error", f"Bill #{bill_id} not found.")
                return

            # Parse bill items from stored string
            import ast
            bill_items = ast.literal_eval(bill_record[5])

            # Calculate subtotal and tax
            subtotal = sum(item["total"] for item in bill_items)
            tax = subtotal * 0.18  # Assuming 18% tax

            bill_data = {
                "id": bill_record[0],
                "date": bill_record[1],
                "customer_name": bill_record[2],
                "customer_mobile": bill_record[3],
                "customer_address": bill_record[4],
                "items": bill_items,
                "subtotal": subtotal,
                "tax": tax,
                "total": bill_record[6]
            }

        # Generate PDF bill
        try:
            pdf_path = generate_bill_pdf(bill_data)

            # Open PDF file
            import os
            try:
                if os.name == 'nt':  # For Windows
                    os.startfile(pdf_path)
                elif os.name == 'posix':  # For macOS and Linux
                    import subprocess
                    subprocess.Popen(['xdg-open', pdf_path])
            except Exception as e:
                messagebox.showinfo("PDF Created", f"Bill saved to: {pdf_path}\nNote: {str(e)}")

            self.status_bar.config(text=f"Bill printed successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate bill: {str(e)}")

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

    def check_low_stock_alert(self):
        """Check for low stock items and show alert if any found"""
        self.cursor.execute("""
            SELECT name, units, total_units 
            FROM products 
            WHERE units > 0 AND total_units > 0 
            AND CAST(units AS FLOAT) / total_units <= 0.25
        """)
        low_stock_items = self.cursor.fetchall()

        if low_stock_items:
            items_text = "\n".join([
                f"• {item[0]}: {item[1]} units remaining out of {item[2]}"
                for item in low_stock_items
            ])
            messagebox.showwarning(
                "Low Stock Alert",
                f"The following items are running low on stock:\n\n{items_text}"
            )

def main():
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
def get_available_units(self, product_id, quantity_needed):
    """Get units from available batches in order"""
    self.cursor.execute("""
        SELECT id, batch_no, units 
        FROM products 
        WHERE name = (SELECT name FROM products WHERE id = ?)
        AND units > 0 
        ORDER BY expiry, batch_no
    """, (product_id,))
    
    batches = self.cursor.fetchall()
    units_to_take = []
    remaining = quantity_needed
    
    for batch_id, batch_no, available in batches:
        if remaining <= 0:
            break
        units = min(available, remaining)
        units_to_take.append((batch_id, units))
        remaining -= units
    
    if remaining > 0:
        return None  # Not enough units available
    
    return units_to_take
def import_from_excel(self):
    """Import inventory data from Excel"""
    from tkinter import filedialog
    import pandas as pd
    
    filename = filedialog.askopenfilename(
        title="Select Excel file",
        filetypes=[("Excel files", "*.xlsx")]
    )
    
    if not filename:
        return
        
    try:
        df = pd.read_excel(filename)
        for _, row in df.iterrows():
            # Generate batch number
            batch_no = generate_batch_number(
                row['name'], 
                pd.to_datetime(row['dom']).date(), 
                self.cursor
            )
            
            # Add product with generated batch number
            self.add_product_from_import(row, batch_no)
            
        self.conn.commit()
        self.refresh_product_list()
        messagebox.showinfo("Success", "Data imported successfully")
        
    except Exception as e:
        messagebox.showerror("Error", f"Import failed: {str(e)}")

def export_to_excel(self):
    """Export inventory data to Excel"""
    from tkinter import filedialog
    import pandas as pd
    
    filename = filedialog.asksaveasfilename(
        title="Save Excel file",
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")]
    )
    
    if not filename:
        return
        
    try:
        self.cursor.execute("""
            SELECT p.*, c.name as company_name 
            FROM products p
            LEFT JOIN companies c ON p.company_id = c.id
        """)
        
        columns = [description[0] for description in self.cursor.description]
        data = self.cursor.fetchall()
        
        df = pd.DataFrame(data, columns=columns)
        df.to_excel(filename, index=False)
        messagebox.showinfo("Success", "Data exported successfully")
        
    except Exception as e:
        messagebox.showerror("Error", f"Export failed: {str(e)}")
def init_customer_database(self):
    """Initialize customer database table"""
    self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    self.conn.commit()

def load_customer_names(self):
    """Load customer names for dropdown"""
    self.cursor.execute("SELECT name FROM customers ORDER BY name")
    customers = self.cursor.fetchall()
    customer_names = [customer[0] for customer in customers]
    self.customer_name_combobox['values'] = customer_names

def customer_selected(self, event=None):
    """Handle customer selection"""
    customer_name = self.customer_name_combobox.get()
    if customer_name:
        self.cursor.execute("""
            SELECT mobile, address 
            FROM customers 
            WHERE name = ?
        """, (customer_name,))
        result = self.cursor.fetchone()
        if result:
            self.customer_mobile_entry.delete(0, tk.END)
            self.customer_mobile_entry.insert(0, result[0])
            self.customer_address_entry.delete(0, tk.END)
            self.customer_address_entry.insert(0, result[1])
