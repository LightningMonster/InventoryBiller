import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
# Removing any potential circular import

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
    
    normal_style = styles["Normal"]
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold'
    )
    small_style = ParagraphStyle(
        'SmallStyle',
        parent=styles['Normal'],
        fontSize=8
    )
    
    # Create content elements
    elements = []
    
    # Company Header - without image to avoid file not found error
    company_data = [
        [
            Paragraph("○", normal_style),  # Simple circle as placeholder for logo
            Paragraph("<b>Company name</b>", normal_style),
            Paragraph("<b>COMPANY DETAILS:</b>", bold_style),
        ],
        [
            "",
            "",
            Paragraph("123 Anywhere Street, Any City, ST 12345", small_style)
        ],
        [
            "",
            "",
            Paragraph("Phone: 123-456-7890", small_style)
        ],
        [
            "",
            "",
            Paragraph("Email: hello@reallygreatsite.com", small_style)
        ],
        [
            "",
            "",
            Paragraph("Website: www.reallygreatsite.com", small_style)
        ]
    ]
    
    # Create company header table
    company_table = Table(company_data, colWidths=[0.7*inch, 2.5*inch, 3.5*inch])
    company_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('SPAN', (0, 0), (0, 4)),
        ('SPAN', (1, 0), (1, 4)),
    ]))
    
    elements.append(company_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Items table - Simplified to match example image
    # Headers for bill items
    items_data = [
        ["Date", "Item Description", "Price", "Qty", "Total"]
    ]
    
    # Create 15 empty rows for the table
    for _ in range(15):
        items_data.append(["", "", "", "", ""])
    
    # Create the table with widths matching the example image
    col_widths = [0.8*inch, 3.2*inch, 0.8*inch, 0.6*inch, 1.0*inch]
    items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
    
    # Apply table styles to match example
    table_style = [
        # Grid borders for all cells
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # Header style - no background color in the example
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Cell alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    
    # Summary table (right-aligned) - Match exact format from screenshot
    subtotal = bill_data.get('subtotal', 100.00)
    discount = bill_data.get('discount', 30.00)
    tax = bill_data.get('tax', 5.00)
    total = bill_data.get('total', 75.00)
    
    # Format values to match screenshot (positive numbers with currency symbol)
    summary_data = [
        ["Subtotal", f"${subtotal:.2f}"],
        [f"Discount ({int(discount)}% Off)", f"(-${discount:.2f})"],
        ["Sales Tax (5%)", f"${tax:.2f}"],
        ["Total", f"${total:.2f}"]
    ]
    
    summary_table = Table(
        summary_data,
        colWidths=[1.5*inch, 0.8*inch]
    )
    
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),
        ('LINEBELOW', (0, -1), (1, -1), 1, colors.black),
    ]))
    
    # Payment terms section (left) and summary (right) - Exactly match screenshot
    payment_data = [
        [Paragraph("<b>PAYMENT TERMS:</b>", bold_style), "", summary_data[0][0], summary_data[0][1]],
        [Paragraph("123-456-7890", small_style), "", summary_data[1][0], summary_data[1][1]],
        [Paragraph("Lorem Beauty & Spa", small_style), "", summary_data[2][0], summary_data[2][1]],
        [Paragraph("Lorem ipsum", small_style), "", summary_data[3][0], summary_data[3][1]]
    ]
    
    payment_table = Table(
        payment_data,
        colWidths=[2*inch, 2.4*inch, 1.5*inch, 0.8*inch]
    )
    
    payment_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (2, -1), (3, -1), 1, colors.black),
        ('LINEBELOW', (2, -1), (3, -1), 1, colors.black),
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (0, 2), (1, 2)),
        ('SPAN', (0, 3), (1, 3)),
    ]))
    
    elements.append(Spacer(1, 0.2*inch))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Signature section - Match exactly with screenshot layout
    signature_data = [
        [Paragraph("<b>COMPANY NAME:</b>", bold_style), "", Paragraph("<b>TRANSPORTER'S NAME:</b>", bold_style), ""],
        [Paragraph("<b>AUTHORISED SIGNATORY:</b>", bold_style), "", "", ""],
        [Paragraph("<b>SIGNATURE</b>", bold_style), "", Paragraph("<b>RECEIVER'S STAMP & SIGN:</b>", bold_style), ""]
    ]
    
    signature_table = Table(
        signature_data,
        colWidths=[1.7*inch, 1.5*inch, 1.7*inch, 1.8*inch]
    )
    
    signature_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (2, 0), (3, 0)),
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (2, 1), (3, 1)),
        ('SPAN', (0, 2), (1, 2)),
        ('SPAN', (2, 2), (3, 2)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(signature_table)
    
    # Build the PDF
    doc.build(elements)
    
    return pdf_path
