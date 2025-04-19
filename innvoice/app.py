from flask import Flask, render_template, request, send_file, jsonify
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import traceback
import base64
import requests
from datetime import datetime

app = Flask(__name__)

# Your logo URL
LOGO_URL = "https://res.cloudinary.com/djxcl4jcy/image/upload/v1744973510/new_cgqoq1.svg"

def get_logo():
    try:
        response = requests.get(LOGO_URL)
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error fetching logo: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    try:
        # Get JSON data from frontend
        data = request.get_json()
        app.logger.info(f"Received data: {data}")  # Log the incoming data
        
        # Validate incoming data
        required_fields = ['bill_to', 'address', 'phone', 'delivery_date_time', 'invoice_date', 'invoice_number', 'requirement_members', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        # Calculate totals
        subtotal = sum(float(item.get('total', 0)) for item in data['items'])
        delivery_charge = float(data.get('delivery_charge', 0))
        advance = float(data.get('advance', 0))
        
        invoice_data = {
            'bill_to': data['bill_to'],
            'address': data['address'],
            'phone': data['phone'],
            'delivery_date_time': data['delivery_date_time'],
            'invoice_date': data['invoice_date'],
            'invoice_number': data['invoice_number'],
            'requirement_members': data['requirement_members'],
            'items': data['items'],
            'delivery_charge': delivery_charge,
            'subtotal': subtotal,
            'advance': advance,
            'payment_type': data.get('payment_type', 'Cash'),
            'terms_conditions': data.get('terms_conditions', 'Payment due upon delivery. Thank you for your business!')
        }

        # Calculate derived values
        invoice_data['total_amount'] = invoice_data['subtotal'] + invoice_data['delivery_charge']
        invoice_data['due'] = invoice_data['total_amount'] - invoice_data['advance']

        # Generate PDF
        pdf_bytes = generate_pdf(invoice_data)
        
        # Return both JSON response and PDF as base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        response = {
            'success': True,
            'invoice_number': invoice_data['invoice_number'],
            'pdf': pdf_base64
        }
        return jsonify(response)

    except Exception as e:
        app.logger.error(f"Error generating invoice: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_pdf(invoice_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=36, leftMargin=36,
                          topMargin=36, bottomMargin=36)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    company_style = ParagraphStyle(
        'Company',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.HexColor('#3498db'),
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=14
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    
    elements = []
    
    # Header with logo and company info
    logo = get_logo()
    header_table_data = []
    
    # Left column - Logo and company name
    left_col = []
    if logo:
        try:
            logo_img = Image(logo, width=2*inch, height=0.8*inch)
            left_col.append(logo_img)
        except Exception as e:
            app.logger.error(f"Error processing logo: {str(e)}")
            left_col.append(Paragraph("SRI KARIMALESH CATERERS", header_style))
    else:
        left_col.append(Paragraph("SRI KARIMALESH CATERERS", header_style))
    
    left_col.append(Paragraph("Catering Services", company_style))
    
    # Right column - Contact info with Font Awesome-like icons using Unicode
    right_col = [
    Paragraph(f"""<font color="#3498db"></font> <font color="#2c3e50">+61 450 056 387</font>""", body_style),
    Paragraph(f"""<font color="#2ecc71"></font> <font color="#2c3e50">srikarimaleshcaterers.com.au</font>""", body_style)
    ]
   
    header_table_data.append([left_col, right_col])
    
    header_table = Table(header_table_data, colWidths=[doc.width/2]*2)
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('RIGHTPADDING', (1,0), (1,0), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    
    # Colorful divider
    elements.append(Spacer(1, 15))
    divider = Table([[""]], colWidths=[doc.width])
    divider.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#3498db')),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#2ecc71')),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 15))
    
    # Invoice title with background
    invoice_title = Paragraph("INVOICE", ParagraphStyle(
        'InvoiceTitle',
        parent=header_style,
        fontSize=16,
        backColor=colors.HexColor('#f8f9fa'),
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1
    ))
    elements.append(invoice_title)
    
    # Invoice info in two columns with light gray background
    info_data = [
        [
            Paragraph("<b>Bill To</b>", section_header_style),
            "",
            Paragraph("<b>Invoice Details</b>", section_header_style),
            ""
        ],
        [
            Paragraph("<b>" + invoice_data['bill_to'] + "</b>", bold_style),
            "",
            Paragraph("Invoice #: <b>" + invoice_data['invoice_number'] + "</b>", body_style),
            ""
        ],
        [
            Paragraph(invoice_data['address'], body_style),
            "",
            Paragraph("Date: <b>" + invoice_data['invoice_date'] + "</b>", body_style),
            ""
        ],
        [
            Paragraph("Phone: " + invoice_data['phone'], body_style),
            "",
            Paragraph("Delivery: <b>" + invoice_data['delivery_date_time'] + "</b>", body_style),
            ""
        ],
        [
            "",
            "",
            Paragraph("Members: <b>" + invoice_data['requirement_members'] + "</b>", body_style),
            ""
        ]
    ]
    
    info_table = Table(info_data, colWidths=[2.5*inch, 0.5*inch, 2.5*inch, 0.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('SPAN', (0,0), (1,0)),
        ('SPAN', (2,0), (3,0)),
        ('SPAN', (0,1), (1,1)),
        ('SPAN', (2,1), (3,1)),
        ('SPAN', (0,2), (1,2)),
        ('SPAN', (2,2), (3,2)),
        ('SPAN', (0,3), (1,3)),
        ('SPAN', (2,3), (3,3)),
        ('SPAN', (0,4), (1,4)),
        ('SPAN', (2,4), (3,4)),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    # Items table with black border header
    items_header = [
        Paragraph("<font color='black'>Description</font>", bold_style),
        Paragraph("<font color='black'>Qty</font>", bold_style),
        Paragraph("<font color='black'>Unit Price</font>", bold_style),
        Paragraph("<font color='black'>Total</font>", bold_style)
    ]
    items_data = [items_header]
    
    for item in invoice_data['items']:
        items_data.append([
            Paragraph(item['description'], body_style),
            Paragraph(str(item['quantity']), body_style), 
            Paragraph(f"${float(item.get('rate', 0)):.2f}" if item.get('rate') else "-", body_style),
            Paragraph(f"${float(item.get('total', 0)):.2f}" if item.get('total') else "-", body_style)
        ])
    
    items_table = Table(items_data, colWidths=[3.2*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # Totals section with highlighted important amounts
    totals_data = [
        ["Subtotal:", f"${invoice_data['subtotal']:.2f}"],
        ["Delivery Charge:", f"${invoice_data['delivery_charge']:.2f}"],
        ["Total Amount:", f"${invoice_data['total_amount']:.2f}"],
        ["Advance Paid:", f"${invoice_data['advance']:.2f}"],
        ["Balance Due:", f"${invoice_data['due']:.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[3*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LINEABOVE', (0,2), (-1,2), 0.5, colors.HexColor('#dddddd')),
        ('LINEBELOW', (0,2), (-1,2), 0.5, colors.HexColor('#dddddd')),
        ('FONTNAME', (0,2), (1,2), 'Helvetica-Bold'),
        ('FONTSIZE', (0,2), (1,2), 11),
        ('FONTNAME', (0,4), (1,4), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,4), (1,4), colors.HexColor('#e74c3c')),
        ('FONTSIZE', (0,4), (1,4), 11),
        ('BOTTOMPADDING', (0,4), (1,4), 15),
    ]))
    elements.append(totals_table)
    
    # Payment and Terms section in two columns
    elements.append(Spacer(1, 20))
    
    payment_terms_data = [
        [
            Paragraph("Payment Information", section_header_style),
            Paragraph("Terms & Conditions", section_header_style)
        ],
        [
            Paragraph(f"Payment Method: <b>{invoice_data['payment_type']}</b>", body_style),
            Paragraph(invoice_data['terms_conditions'], body_style)
        ]
    ]
    
    if invoice_data['payment_type'] == 'Bank Transfer':
        payment_terms_data.insert(1, [
            Paragraph("Account Name: <b>SRI KARIMALESH CATERERS</b>", body_style),
            ""
        ])
        payment_terms_data.insert(2, [
            Paragraph("BSB: <b>123-456</b>", body_style),
            ""
        ])
        payment_terms_data.insert(3, [
            Paragraph("Account Number: <b>987654321</b>", body_style),
            ""
        ])
    
    payment_terms_table = Table(payment_terms_data, colWidths=[doc.width/2]*2)
    payment_terms_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(payment_terms_table)
    
    # Signature line
    elements.append(Spacer(1, 30))
    signature_table = Table([
        ["", Paragraph("Rajesh Morishetty", bold_style)],
        ["", Table([[""]], colWidths=[2*inch])],
        ["", Paragraph("Authorized Signature", ParagraphStyle(
            'Signature',
            parent=body_style,
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d')
        ))]
    ], colWidths=[4*inch, 2*inch])
    
    signature_table.setStyle(TableStyle([
        ('LINEABOVE', (1,1), (1,1), 1, colors.black),
    ]))
    elements.append(signature_table)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

@app.route('/download_invoice', methods=['POST'])
def download_invoice():
    try:
        data = request.get_json()
        
        # Calculate totals
        subtotal = sum(float(item.get('total', 0)) for item in data['items'])
        delivery_charge = float(data.get('delivery_charge', 0))
        advance = float(data.get('advance', 0))
        
        invoice_data = {
            'bill_to': data['bill_to'],
            'address': data['address'],
            'phone': data['phone'],
            'delivery_date_time': data['delivery_date_time'],
            'invoice_date': data['invoice_date'],
            'invoice_number': data['invoice_number'],
            'requirement_members': data['requirement_members'],
            'items': data['items'],
            'delivery_charge': delivery_charge,
            'subtotal': subtotal,
            'advance': advance,
            'payment_type': data.get('payment_type', 'Cash'),
            'terms_conditions': data.get('terms_conditions', 'Payment due upon delivery. Thank you for your business!')
        }

        # Calculate derived values
        invoice_data['total_amount'] = invoice_data['subtotal'] + invoice_data['delivery_charge']
        invoice_data['due'] = invoice_data['total_amount'] - invoice_data['advance']

        pdf_bytes = generate_pdf(invoice_data)
        buffer = BytesIO(pdf_bytes)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"invoice_{invoice_data['invoice_number']}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        app.logger.error(f"Error downloading invoice: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)