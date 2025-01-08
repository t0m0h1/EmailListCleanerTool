from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def validate_email_syntax(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def check_mx_record(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            return redirect(url_for('process_file', filename=file.filename))
    return render_template('index.html')

@app.route('/process/<filename>')
def process_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)  # Assuming CSV file format
    cleaned_data = []

    for email in df['email']:
        result = {
            'email': email,
            'valid_syntax': validate_email_syntax(email),
            'valid_domain': False,
            'valid_mx': False
        }
        if result['valid_syntax']:
            domain = email.split('@')[1]
            result['valid_domain'] = check_mx_record(domain)
            result['valid_mx'] = result['valid_domain']
        cleaned_data.append(result)

    # Generate report as DataFrame
    report_df = pd.DataFrame(cleaned_data)
    report_filename = filename.rsplit('.', 1)[0] + '_cleaned.csv'
    report_df.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], report_filename), index=False)

    return render_template('process.html', report_filename=report_filename)

if __name__ == '__main__':
    app.run(debug=True)
