"""
Test script to verify bill_generator imports correctly
"""
print("Starting import test...")
from bill_generator import generate_bill_pdf
print("Import successful!")

# Test a simple bill generation with minimal data
def test_bill_generation():
    bill_data = {
        "id": "TEST001",
        "date": "2023-04-23",
        "customer_name": "Test Customer",
        "customer_mobile": "1234567890",
        "customer_address": "Test Address",
        "items": [
            {
                "name": "Test Product",
                "hsn_code": "1234",
                "quantity": 2,
                "rate": 100.00,
                "total": 200.00
            }
        ],
        "subtotal": 200.00,
        "tax": 36.00,
        "total": 236.00
    }
    
    try:
        path = generate_bill_pdf(bill_data)
        print(f"Bill generated successfully at: {path}")
        return True
    except Exception as e:
        print(f"Error generating bill: {str(e)}")
        return False

# Only run the test if this file is executed directly
if __name__ == "__main__":
    test_bill_generation()