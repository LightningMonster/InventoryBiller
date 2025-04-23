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
    """
    # Determine if we're running as exe or in development
    if getattr(sys, 'frozen', False):
        user_data_dir = os.path.join(os.path.expanduser("~"), "BillingApp")
        bills_dir = os.path.join(user_data_dir, "bills")
    else:
        bills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bills")

    if not os.path.exists(bills_dir):
        os.makedirs(bills_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bill_id = bill_data.get("id", "DRAFT")
    filename = f"Bill_{bill_id}_{timestamp}.pdf"
    pdf_path = os.path.join(bills_dir, filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    elements = []

    # Company Header
    company_data = [
        [
            Paragraph("", normal_style),
            Paragraph("<b>Company name</b>", normal_style),
            Paragraph("<b>COMPANY DETAILS:</b>", normal_style)
        ],
        [
            "",
            "",
            "123 Anywhere St., Any City, ST 12345"
        ],
        [
            "",
            "",
            "Phone: 123-456-7890"
        ],
        [
            "",
            "",
            "Email: hello@reallygreatsite.com"
        ],
        [
            "",
            "",
            "Website: www.reallygreatsite.com"
        ]
    ]

    header_table = Table(company_data, colWidths=[0.7*inch, 2.3*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (2, 0), (2, -1), 20),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))

    # Bill Items Table
    items_header = [["Date", "Item Description", "Price", "Qty", "Total"]]
    items_data = items_header + [["", "", "", "", ""] for _ in range(15)]  # 15 empty rows

    items_table = Table(items_data, colWidths=[0.8*inch, 3.2*inch, 0.8*inch, 0.6*inch, 1.1*inch])

    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))

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
            colWidths=[0.8*inch, 3.2*inch, 0.8*inch, 0.6*inch, 1.1*inch]
        )

        actual_items_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (4, -1), 'RIGHT'),  # Align price and total to right
        ]))

        elements.append(actual_items_table)


    # Payment Terms and Summary
    payment_data = [
        ["PAYMENT TERMS:", "", "Subtotal", f"₹{bill_data.get('subtotal',0):.2f}"],
        ["123-456-7890", "", "Discount (30% Off)", f"(-) ₹{bill_data.get('subtotal',0)*0.3:.2f}"],
        ["Lorem Beauty & Spa", "", "Sales Tax (5%)", f"₹{bill_data.get('tax',0):.2f}"],
        ["Lorem ipsum", "", "Total", f"₹{bill_data.get('total',0):.2f}"]
    ]

    payment_table = Table(payment_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.0*inch])
    payment_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (2, -1), (3, -1), 1, colors.black),
        ('LINEBELOW', (2, -1), (3, -1), 1, colors.black),
    ]))

    elements.append(payment_table)
    elements.append(Spacer(1, 0.3*inch))

    # Signature Section
    signature_data = [
        ["COMPANY NAME:", "", "TRANSPORTER'S NAME:", ""],
        ["AUTHORISED SIGNATORY:", "", "", ""],
        ["SIGNATURE", "", "RECEIVER'S STAMP & SIGN:", ""]
    ]

    signature_table = Table(signature_data, colWidths=[1.7*inch, 1.5*inch, 1.7*inch, 1.6*inch])
    signature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(signature_table)

    # Build the PDF
    doc.build(elements)
    return pdf_path