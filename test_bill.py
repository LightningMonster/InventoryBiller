"""
Test script to generate a bill with the new template
"""
from bill_generator import generate_bill_pdf

# Create test data for bill generation
bill_data = {
    "id": "TEST001",
    "date": "2023-04-23",
    "customer_name": "Test Customer",
    "customer_mobile": "1234567890",
    "customer_address": "Test Address",
    "items": [
        {
            "name": "Product 1",
            "hsn_code": "1234",
            "quantity": 2,
            "rate": 50.00,
            "total": 100.00
        }
    ],
    "subtotal": 100.00,
    "tax": 5.00,
    "total": 75.00  # After discount
}

# Generate the bill
pdf_path = generate_bill_pdf(bill_data)
print(f"Bill generated at: {pdf_path}")