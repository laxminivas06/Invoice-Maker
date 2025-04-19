document.addEventListener('DOMContentLoaded', function() {
    // Set current date
    const today = new Date();
    document.getElementById('invoice_date').valueAsDate = today;
    
    // Generate a simple invoice number (YYYYMMDD-001 format)
    const invoiceNumber = generateInvoiceNumber();
    document.getElementById('invoice_number').value = invoiceNumber;

    // Add item row
    document.getElementById('addItem').addEventListener('click', function() {
        addNewItemRow();
    });

    // Add event listeners to initial row
    const initialRow = document.querySelector('.item-row');
    if (initialRow) {
        addItemRowListeners(initialRow);
    }

    // Calculate totals when values change
    document.getElementById('delivery_charge').addEventListener('input', calculateTotals);
    document.getElementById('subtotal_input').addEventListener('input', calculateTotals);
    document.getElementById('advance').addEventListener('input', calculateTotals);

    // Form submission
    document.getElementById('invoiceForm').addEventListener('submit', function(e) {
        e.preventDefault();
        generateInvoice();
    });

    // Preview button
    document.getElementById('previewBtn').addEventListener('click', previewInvoice);

    // Modal close button
    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('previewModal').style.display = 'none';
    });

    // Print button
    document.getElementById('printBtn').addEventListener('click', function() {
        const printContent = document.getElementById('invoicePreview').innerHTML;
        const originalContent = document.body.innerHTML;
        
        document.body.innerHTML = printContent;
        window.print();
        document.body.innerHTML = originalContent;
    });

    // Download PDF button
    document.getElementById('downloadBtn').addEventListener('click', function() {
        generateInvoice(true); // Pass true to indicate download-only
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target == document.getElementById('previewModal')) {
            document.getElementById('previewModal').style.display = 'none';
        }
    });

    // Helper functions
    function generateInvoiceNumber() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}${month}${day}-001`; // In a real app, you'd increment this
    }

    function addNewItemRow() {
        const tbody = document.querySelector('#itemsTable tbody');
        const newRow = document.createElement('tr');
        newRow.className = 'item-row';
        newRow.innerHTML = `
            <td><input type="text" name="item_description" class="item-description" placeholder="Item description" required></td>
            <td><input type="number" name="quantity" class="quantity" min="1" value="1" required></td>
            <td><input type="number" name="unit_price" class="unit-price" step="0.01" min="0" required></td>
            <td><span class="total">0.00</span></td>
            <td><button type="button" class="remove-item btn btn-danger btn-sm">×</button></td>
        `;
        tbody.appendChild(newRow);
        addItemRowListeners(newRow);
        
        // Focus on the new item description field
        newRow.querySelector('.item-description').focus();
    }

    function addItemRowListeners(row) {
        const quantityInput = row.querySelector('.quantity');
        const unitPriceInput = row.querySelector('.unit-price');
        const removeBtn = row.querySelector('.remove-item');

        quantityInput.addEventListener('input', function() {
            calculateItemTotal(row);
            calculateSubtotal();
        });

        unitPriceInput.addEventListener('input', function() {
            calculateItemTotal(row);
            calculateSubtotal();
        });

        removeBtn.addEventListener('click', function() {
            row.remove();
            calculateSubtotal();
        });
    }

    function calculateItemTotal(row) {
        const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
        const unitPrice = parseFloat(row.querySelector('.unit-price').value) || 0;
        const total = quantity * unitPrice;
        row.querySelector('.total').textContent = total.toFixed(2);
    }

    function calculateSubtotal() {
        let subtotal = 0;
        document.querySelectorAll('.item-row').forEach(row => {
            subtotal += parseFloat(row.querySelector('.total').textContent) || 0;
        });
        
        // Update the subtotal input field
        document.getElementById('subtotal_input').value = subtotal.toFixed(2);
        
        // Trigger totals calculation
        calculateTotals();
    }

    function calculateTotals() {
        // Get manually entered values
        const deliveryCharge = parseFloat(document.getElementById('delivery_charge').value) || 0;
        const subtotal = parseFloat(document.getElementById('subtotal_input').value) || 0;
        const advance = parseFloat(document.getElementById('advance').value) || 0;

        // Calculate totals
        const totalAmount = subtotal + deliveryCharge;
        const due = totalAmount - advance;

        // Update display
        document.getElementById('total_amount').textContent = totalAmount.toFixed(2);
        document.getElementById('due').textContent = due.toFixed(2);
    }

    function collectInvoiceData() {
        return {
            bill_to: document.getElementById('bill_to').value,
            address: document.getElementById('address').value,
            delivery_date_time: document.getElementById('delivery_date_time').value,
            phone: document.getElementById('phone').value,
            invoice_date: document.getElementById('invoice_date').value,
            invoice_number: document.getElementById('invoice_number').value,
            requirement_members: document.getElementById('requirement_members').value,
            items: Array.from(document.querySelectorAll('.item-row')).map(row => ({
                description: row.querySelector('.item-description').value,
                quantity: parseFloat(row.querySelector('.quantity').value) || 0,
                rate: parseFloat(row.querySelector('.unit-price').value) || 0,
                total: parseFloat(row.querySelector('.total').textContent) || 0
            })),
            delivery_charge: parseFloat(document.getElementById('delivery_charge').value) || 0,
            subtotal: parseFloat(document.getElementById('subtotal_input').value) || 0,
            advance: parseFloat(document.getElementById('advance').value) || 0,
            payment_type: document.querySelector('input[name="payment_type"]:checked').value,
            terms_conditions: document.getElementById('terms_conditions').value
        };
    }

    function validateForm() {
        // Validate required fields
        const requiredFields = [
            'bill_to', 'address', 'delivery_date_time', 
            'phone', 'invoice_date', 'invoice_number'
        ];
        
        let isValid = true;
        
        requiredFields.forEach(field => {
            const element = document.getElementById(field);
            if (!element.value.trim()) {
                element.classList.add('is-invalid');
                isValid = false;
            } else {
                element.classList.remove('is-invalid');
            }
        });

        // Validate at least one item with description
        const items = document.querySelectorAll('.item-description');
        if (items.length === 0) {
            alert('Please add at least one item');
            return false;
        }

        let hasItemWithDescription = false;
        items.forEach(item => {
            if (item.value.trim()) {
                hasItemWithDescription = true;
            }
        });

        if (!hasItemWithDescription) {
            alert('Please add description for at least one item');
            return false;
        }

        return isValid;
    }

    function previewInvoice() {
        if (!validateForm()) return;

        const formData = collectInvoiceData();
        const previewHTML = generateInvoiceHTML(formData);
        document.getElementById('invoicePreview').innerHTML = previewHTML;
        document.getElementById('previewModal').style.display = 'block';
    }

    function generateInvoice(downloadOnly = false) {
        if (!validateForm()) return;

        const submitBtn = document.querySelector('#invoiceForm button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = 'Generating...';
        submitBtn.disabled = true;

        const formData = collectInvoiceData();

        fetch('/generate_invoice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (downloadOnly) {
                    // Download the PDF directly
                    const byteCharacters = atob(data.pdf);
                    const byteNumbers = new Array(byteCharacters.length);
                    for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], {type: 'application/pdf'});
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `invoice_${formData.invoice_number}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    // Show success message
                    alert('Invoice generated successfully!');
                }
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error generating invoice: ${error.message}`);
        })
        .finally(() => {
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        });
    }

    function generateInvoiceHTML(data) {
        // Format date for display
        const formattedDate = new Date(data.invoice_date).toLocaleDateString('en-AU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        return `
            <div class="invoice-preview">
                <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div>
                       <img src="https://res.cloudinary.com/djxcl4jcy/image/upload/v1744973510/new_cgqoq1.svg" alt="Company Logo" style="height: 80px; margin-bottom: 10px;">
                        <h1 style="margin: 0; color: #2c3e50;">SRI KARIMALESH CATERERS</h1>
                        <p style="margin: 5px 0 0 0; color: #7f8c8d;">Catering Services</p>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin: 5px 0; color: #2c3e50;">
                            <i class="fas fa-phone"></i> +61 450 056 387
                        </p>
                        <p style="margin: 5px 0; color: #2c3e50;">
                            <i class="fas fa-globe"></i> srikarimaleshcaterers.com.au
                        </p>
                    </div>
                </header>
                
                <hr style="border: 0; height: 2px; background: linear-gradient(to right, #3498db, #2ecc71); margin: 20px 0;">

                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px;">
                    <h2 style="margin: 0 0 15px 0; color: #2c3e50; text-align: center;">INVOICE</h2>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                        <div style="flex: 1; min-width: 250px;">
                            <h3 style="margin: 0 0 10px 0; color: #3498db;">Bill To</h3>
                            <p style="margin: 5px 0;"><strong>${data.bill_to}</strong></p>
                            <p style="margin: 5px 0;">${data.address}</p>
                            <p style="margin: 5px 0;">Phone: ${data.phone}</p>
                        </div>
                        
                        <div style="flex: 1; min-width: 250px;">
                            <h3 style="margin: 0 0 10px 0; color: #3498db;">Invoice Details</h3>
                            <p style="margin: 5px 0;">Invoice #: <strong>${data.invoice_number}</strong></p>
                            <p style="margin: 5px 0;">Date: <strong>${formattedDate}</strong></p>
                            <p style="margin: 5px 0;">Delivery: <strong>${data.delivery_date_time}</strong></p>
                            <p style="margin: 5px 0;">Members: <strong>${data.requirement_members}</strong></p>
                        </div>
                    </div>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                    <thead style="background-color: #3498db; color: white;">
                        <tr>
                    <th style="border: 1px solid black; padding: 12px; text-align: left;"><span style="color:black;">Description</span></th>
                    <th style="border: 1px solid black; padding: 12px; text-align: center;"> <span style="color:black;">Qty </span></th>
                    <th style="border: 1px solid black; padding: 12px; text-align: right;"> <span style="color:black;">Unit Price </span></th>
                    <th style="border: 1px solid black; padding: 12px; text-align: right;"> <span style="color:black;">Total </span></th>
                </tr>
            </thead>
            <tbody>
                ${data.items.map(item => `
                    <tr>
                        <td style="border: 1px solid black; padding: 10px;">${item.description || '-'}</td>
                        <td style="border: 1px solid black; padding: 10px; text-align: center;">${item.quantity}</td>
                        <td style="border: 1px solid black; padding: 10px; text-align: right;">${item.rate > 0 ? '$' + item.rate.toFixed(2) : '-'}</td>
                        <td style="border: 1px solid black; padding: 10px; text-align: right;">${item.total > 0 ? '$' + item.total.toFixed(2) : '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>

                <div style="margin-left: auto; width: 300px; background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>Subtotal:</span>
                        <span>$${data.subtotal.toFixed(2)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>Delivery Charge:</span>
                        <span>$${data.delivery_charge.toFixed(2)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1em; margin-bottom: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
                        <span>Total Amount:</span>
                        <span>$${(parseFloat(data.subtotal) + parseFloat(data.delivery_charge)).toFixed(2)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>Advance Paid:</span>
                        <span>$${data.advance.toFixed(2)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: bold; color: #e74c3c; padding-top: 10px; border-top: 1px solid #ddd;">
                        <span>Balance Due:</span>
                        <span>$${(parseFloat(data.subtotal) + parseFloat(data.delivery_charge) - parseFloat(data.advance)).toFixed(2)}</span>
                    </div>
                </div>

                <div style="display: flex; flex-wrap: wrap; gap: 30px; margin-bottom: 30px;">
                    <div style="flex: 1; min-width: 250px;">
                        <h3 style="margin: 0 0 10px 0; color: #3498db;">Payment Information</h3>
                        <p style="margin: 5px 0;">Payment Method: <strong>${data.payment_type}</strong></p>
                        ${data.payment_type === 'Bank Transfer' ? `
                            <p style="margin: 5px 0;">Account Name: <strong>SRI KARIMALESH CATERERS</strong></p>
                            <p style="margin: 5px 0;">BSB: <strong>123-456</strong></p>
                            <p style="margin: 5px 0;">Account Number: <strong>987654321</strong></p>
                        ` : ''}
                    </div>
                    
                    <div style="flex: 1; min-width: 250px;">
                        <h3 style="margin: 0 0 10px 0; color: #3498db;">Terms & Conditions</h3>
                        <p style="margin: 5px 0; white-space: pre-line;">${data.terms_conditions || 'Payment due upon delivery. Thank you for your business!'}</p>
                    </div>
                </div>

                <div style="text-align: right; margin-top: 50px;">
                    <div style="font-weight: 600;">Rajesh Morishetty</div>
                    <div style="width: 200px; height: 1px; background-color: #333; margin-left: auto; margin-bottom: 5px;"></div>
                    <div style="font-weight: 600;">Authorized Signature</div>
                </div>
            </div>
        `;
    }
});