"""
Test script to generate a bill with the fixed bill generator template
"""
from fixed_bill_generator import generate_bill_pdf

# Create test data for bill generation
bill_data = {
    "id": "TEST002",
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
        },
        {
            "name": "Product 2",
            "hsn_code": "5678",
            "quantity": 1,
            "rate": 25.00,
            "total": 25.00
        }
    ],
    "subtotal": 125.00,
    "tax": 5.00,
    "total": 130.00
}

# Generate the bill
pdf_path = generate_bill_pdf(bill_data)
print(f"Bill generated at: {pdf_path}")