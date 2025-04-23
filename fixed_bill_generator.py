"""
Bill Generator Module

This module handles the generation of PDF bills/invoices using ReportLab.
"""
import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

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
    # Determine if we're running as exe or in development
    if getattr(sys, 'frozen', False):
        # If running as executable, use the user's documents folder
        user_data_dir = os.path.join(os.path.expanduser("~"), "BillingApp")
        bills_dir = os.path.join(user_data_dir, "bills")
    else:
        # If running in development, use the local directory
        bills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills")
    
    # Create the bills directory if it doesn't exist
    if not os.path.exists(bills_dir):
        os.makedirs(bills_dir)
    
    # Create filename with timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bill_id = bill_data.get("id", "DRAFT")
    filename = f"Bill_{bill_id}_{timestamp}.pdf"
    pdf_path = os.path.join(bills_dir, filename)
    
    # Create the PDF
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = 1  # Center alignment
    
    subtitle_style = styles["Heading2"]
    subtitle_style.alignment = 1
    
    normal_style = styles["Normal"]
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading3'],
        alignment=0,
        spaceAfter=6
    )
    
    # Create content elements
    elements = []
    
    # Create company header table
    company_name = "Company name"  # Replace with actual company name from database if needed
    company_details = "COMPANY DETAILS:"
    company_address = "123 Anywhere Ave., Any City, ST 12345"
    company_phone = "Phone: 123-456-7890"
    company_email = "Email: hello@reallygreatsite.com"
    company_website = "Website: www.reallygreatsite.com"
    
    company_data = [
        [Paragraph("<img src='generated-icon.png' width='30' height='30'/>", normal_style), Paragraph(company_name, normal_style), Paragraph(company_details, header_style)],
        ["", "", Paragraph(company_address, normal_style)],
        ["", "", Paragraph(company_phone, normal_style)],
        ["", "", Paragraph(company_email, normal_style)],
        ["", "", Paragraph(company_website, normal_style)]
    ]
    
    company_table = Table(company_data, colWidths=[0.5*inch, 2*inch, 4.5*inch])
    company_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
    ]))
    
    elements.append(company_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Customer information
    customer_name = bill_data.get('customer_name', '')
    customer_mobile = bill_data.get('customer_mobile', '')
    customer_address = bill_data.get('customer_address', '')
    
    # Create bill items table with columns matching screenshot
    items_header = [
        ["Date", "Item Description", "Price", "Qty", "Total"],
    ]
    
    items_table = Table(
        items_header,
        colWidths=[1*inch, 3*inch, 1*inch, 0.5*inch, 1*inch]
    )
    
    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, 0), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
    ]))
    
    elements.append(items_table)
    
    # Create empty rows for items
    empty_rows = []
    for i in range(10):  # 10 empty rows
        empty_rows.append(["", "", "", "", ""])
    
    empty_table = Table(
        empty_rows,
        colWidths=[1*inch, 3*inch, 1*inch, 0.5*inch, 1*inch]
    )
    
    empty_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(empty_table)
    
    # Fill actual items if available
    if bill_data['items']:
        # Clear the empty table by overwriting with actual items
        items_rows = []
        total_amount = 0.0
        
        for item in bill_data['items']:
            # Format the date to match the bill template
            date_string = bill_data['date']
            # Add each item row
            items_rows.append([
                date_string,
                item['name'],
                f"₹{item['rate']:.2f}",
                str(item['quantity']),
                f"₹{item['total']:.2f}"
            ])
            total_amount += item['total']
        
        # Create the table with real data
        actual_items_table = Table(
            items_rows,
            colWidths=[1*inch, 3*inch, 1*inch, 0.5*inch, 1*inch]
        )
        
        actual_items_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (4, -1), 'RIGHT'),  # Align price and total to right
        ]))
        
        elements.append(actual_items_table)
    
    # Summary calculations
    subtotal = sum(item['total'] for item in bill_data['items']) if bill_data['items'] else 0.0
    discount = subtotal * 0.10  # Example: 10% discount
    tax = bill_data.get('tax', subtotal * 0.05)  # Use bill data tax or default to 5%
    total = bill_data.get('total', subtotal - discount + tax)
    
    # Summary table with right-aligned values
    summary_data = [
        ["Subtotal", f"₹{subtotal:.2f}"],
        ["Discount (10% Off)", f"(-) ₹{discount:.2f}"],
        ["Sales Tax (5%)", f"₹{tax:.2f}"],
        ["", ""],
        ["Total", f"₹{total:.2f}"]
    ]
    
    # Create summary table
    summary_table = Table(
        summary_data,
        colWidths=[6*inch, 0.5*inch]
    )
    
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment terms and signatures section
    payment_terms_data = [
        [Paragraph("<b>PAYMENT TERMS:</b>", normal_style), "", Paragraph("<b>TRANSPORTER'S NAME:</b>", normal_style)],
        ["123-456-7890", "", ""],
        ["Lorem Beauty & Spa", "", Paragraph("<b>RECEIVER'S STAMP & SIGN:</b>", normal_style)],
        ["Lorem ipsum", "", ""],
        ["", "", ""],
        ["", "", ""],
        [Paragraph("<b>COMPANY NAME:</b>", normal_style), "", ""],
        [Paragraph("<b>AUTHORISED SIGNATORY:</b>", normal_style), "", ""],
        [Paragraph("<b>SIGNATURE</b>", normal_style), "", ""],
    ]
    
    payment_terms_table = Table(
        payment_terms_data,
        colWidths=[2.5*inch, 0.5*inch, 3.5*inch]
    )
    
    payment_terms_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(payment_terms_table)
    
    # Build the PDF
    doc.build(elements)
    
    return pdf_path