"""
Bill Generator Module

This module handles the generation of PDF bills/invoices using ReportLab.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_bill_pdf(bill_data):
    """
    Generate a PDF bill from the provided bill data
    
    Args:
        bill_data (dict): Dictionary containing bill information
            Required keys:
            - id: Bill ID
            - date: Bill date 
            - customer_name: Customer name
            - customer_mobile: Customer mobile (optional)
            - customer_address: Customer address (optional)
            - items: List of dictionaries with item details
            - subtotal: Subtotal amount
            - tax: Tax amount
            - total: Total amount
    
    Returns:
        str: Path to the generated PDF file
    """
    # Use the BILLS_DIR from config
    bills_dir = BILLS_DIR
    if not os.path.exists(bills_dir):
        os.makedirs(bills_dir)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bill_{timestamp}.pdf"
    filepath = os.path.join(bills_dir, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=20,
        alignment=1  # Center alignment
    )
    
    # Company Header
    company_data = [
        ['', 'COMPANY DETAILS:', ''],
        ['Company name', '123 Anywhere St., Any City, ST 12345', ''],
        ['', 'Phone: 123-456-7890', ''],
        ['', 'Email: hello@reallygreatsite.com', ''],
        ['', 'Website: www.reallygreatsite.com', ''],
    ]
    company_table = Table(company_data, colWidths=[100, 300, 100])
    company_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 20))
    
    # Bill Details
    bill_header = [
        ['Bill No:', str(bill_data['id']), 'Date:', bill_data['date']],
        ['Customer Name:', bill_data['customer_name'], 'Mobile:', bill_data['customer_mobile']],
        ['Address:', bill_data['customer_address'], '', ''],
    ]
    bill_table = Table(bill_header, colWidths=[80, 170, 80, 170])
    bill_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 20))
    
    # Items Table
    items_header = ['Sr.No', 'Item Description', 'HSN Code', 'Qty', 'Rate', 'Amount']
    items_data = [items_header]
    
    for idx, item in enumerate(bill_data['items'], 1):
        items_data.append([
            str(idx),
            item['name'],
            item['hsn_code'],
            str(item['quantity']),
            f"₹{item['rate']:.2f}",
            f"₹{item['total']:.2f}"
        ])
    
    # Add empty rows to ensure minimum 10 rows
    while len(items_data) < 11:  # Header + 10 rows
        items_data.append(['', '', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[40, 200, 70, 50, 70, 70])
    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),  # Right align numbers
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row bold
        ('FONT', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Totals Section
    totals_data = [
        ['', 'Subtotal:', f"₹{bill_data['subtotal']:.2f}"],
        ['', 'Discount (10% Off):', f"₹{bill_data['subtotal'] * 0.10:.2f}"],
        ['', 'Sales Tax (5%):', f"₹{bill_data['tax']:.2f}"],
        ['', 'Total:', f"₹{bill_data['total']:.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[300, 100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONT', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 40))
    
    # Payment Terms and Signatures
    footer_data = [
        ['PAYMENT TERMS:', '', '', 'TRANSPORTER\'S NAME:'],
        ['COMPANY NAME:', '', '', 'RECEIVER\'S STAMP & SIGN:'],
        ['AUTHORISED SIGNATORY:', '', '', ''],
        ['SIGNATURE', '', '', ''],
    ]
    footer_table = Table(footer_data, colWidths=[150, 100, 100, 150])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(footer_table)
    
    # Build the PDF
    doc.build(elements)
    return filepath