import tkinter as tk
from tkinter import ttk, messagebox
from ui_components import BillingTab, InventoryTab, ReportsTab, ManagementTab
from db_operations import DatabaseManager
from business_logic import ProductManager, BillingManager

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing & Inventory Management System")
        self.root.geometry("1200x700")

        # Initialize managers
        self.db_manager = DatabaseManager()
        self.product_manager = ProductManager(self.db_manager)
        self.billing_manager = BillingManager(self.db_manager)

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.billing_tab = BillingTab(self.notebook, self)
        self.inventory_tab = InventoryTab(self.notebook, self)
        self.reports_tab = ReportsTab(self.notebook, self)
        self.management_tab = ManagementTab(self.notebook, self)

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

def main():
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()