from flask import Flask, render_template, request, redirect, url_for, flash
from invoice_generator import InvoiceGenerator
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the invoice generator with the PDF template and folder ID
invoice_generator = InvoiceGenerator('Newinvoice.pdf', '1rnW6soFsG_ERrm5OhI1zayw1UgU2ZcDd')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'number': request.form['number'],
                'customer_name': request.form['customer_name'],
                'amount': request.form['amount'],
                'mode_of_payment': request.form['mode_of_payment'],
                'purpose': request.form['purpose'],
                'bank_name': request.form['bank_name'],
                'amount_in_digit': request.form['amount_in_digit'],
                'email':request.form['email']
            }

            # Generate the invoice and get the public link
            public_link = invoice_generator.generate_invoice(form_data)
            
            if public_link:
                flash('Invoice generated successfully!', 'success')
                flash(f'Public Link: {public_link}', 'info')
            else:
                flash('Failed to generate the invoice.', 'danger')

        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')

        return redirect(url_for('home'))

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
