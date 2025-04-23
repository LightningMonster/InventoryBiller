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
    # Create directory for bills if it doesn't exist
    bills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills")
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
    
    # Add company header
    elements.append(Paragraph("COMPANY INVOICE", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Invoice information
    bill_id_text = f"Invoice #: {bill_data['id']}"
    date_text = f"Date: {bill_data['date']}"
    
    # Customer information
    customer_text = f"Customer Name: {bill_data['customer_name']}"
    customer_info = [customer_text]
    
    if bill_data.get('customer_mobile'):
        customer_info.append(f"Phone: {bill_data['customer_mobile']}")
    
    if bill_data.get('customer_address'):
        customer_info.append(f"Address: {bill_data['customer_address']}")
    
    # Create invoice header table
    invoice_data = [
        ["", ""],
        [Paragraph(bill_id_text, normal_style), ""],
        [Paragraph(date_text, normal_style), ""],
        ["", ""],
        [Paragraph(customer_info[0], normal_style), ""]
    ]
    
    # Add additional customer info if available
    for i, info in enumerate(customer_info[1:], 5):
        invoice_data.append([Paragraph(info, normal_style), ""])
    
    invoice_table = Table(invoice_data, colWidths=[4*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Items table header
    elements.append(Paragraph("Items:", header_style))
    
    items_data = [
        ["#", "Item", "HSN Code", "Qty", "Rate", "Amount"]
    ]
    
    # Add item rows
    for i, item in enumerate(bill_data['items'], 1):
        items_data.append([
            str(i),
            item['name'],
            item['hsn_code'],
            str(item['quantity']),
            f"₹{item['rate']:.2f}",
            f"₹{item['total']:.2f}"
        ])
    
    # Create items table
    items_table = Table(
        items_data, 
        colWidths=[0.3*inch, 3*inch, 1*inch, 0.5*inch, 1*inch, 1*inch]
    )
    
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (5, -1), 'RIGHT'),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Summary table
    summary_data = [
        ["Subtotal:", f"₹{bill_data['subtotal']:.2f}"],
        ["Tax (18%):", f"₹{bill_data['tax']:.2f}"],
        ["Total:", f"₹{bill_data['total']:.2f}"]
    ]
    
    summary_table = Table(
        summary_data,
        colWidths=[5.8*inch, 1*inch]
    )
    
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),
        ('LINEBELOW', (0, -1), (1, -1), 1, colors.black),
    ]))
    
    elements.append(summary_table)
    
    # Footer note
    elements.append(Spacer(1, 0.3*inch))
    footer_text = "Thank you for your business!"
    elements.append(Paragraph(footer_text, styles["Italic"]))
    
    # Terms and conditions
    elements.append(Spacer(1, 0.2*inch))
    terms_text = """
    Terms & Conditions:
    1. Goods once sold cannot be returned.
    2. Payment due within 30 days.
    3. All disputes are subject to local jurisdiction.
    """
    elements.append(Paragraph(terms_text, styles["Normal"]))
    
    # Build the PDF
    doc.build(elements)
    
    return pdf_path