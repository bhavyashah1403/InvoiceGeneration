import os
import datetime
from fillpdf import fillpdfs
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class InvoiceGenerator:
    def __init__(self, template_file, main_folder_id):
        self.template_file = template_file
        self.main_folder_id = main_folder_id
        self.drive = self.authenticate_drive()

    def authenticate_drive(self):
        try:
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile("credentials.json")

            if gauth.credentials is None:
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                gauth.Refresh()
            else:
                gauth.Authorize()

            gauth.SaveCredentialsFile("credentials.json")
            return GoogleDrive(gauth)

        except Exception as e:
            print(f"Error in Google Drive authentication: {e}")
            return None

    def generate_invoice(self, form_data):
        try:
            # Validate form fields and get PDF form field names
            form_Fields = list(fillpdfs.get_form_fields(self.template_file).keys())
            filled_pdf_name = f"{form_data['customer_name']}_{datetime.datetime.today().strftime('%Y-%m-%d')}.pdf"

            # Fill the PDF with provided data
            fillpdfs.write_fillable_pdf(self.template_file, filled_pdf_name, {
                form_Fields[0]: form_data['number'],
                form_Fields[1]: datetime.datetime.today().strftime('%Y-%m-%d'),
                form_Fields[2]: form_data['customer_name'],
                form_Fields[3]: form_data['amount'],
                form_Fields[4]: form_data['mode_of_payment'],
                form_Fields[5]: form_data['purpose'],
                form_Fields[6]: form_data['bank_name'],
                form_Fields[7]: form_data['amount_in_digit']
            })

            # Upload to Google Drive and send the email
            public_link = self.upload_to_drive(filled_pdf_name, form_data['customer_name'])
            if public_link:
                self.send_email(public_link, form_data['customer_name'],form_data['email'])
            return public_link

        except Exception as e:
            print(f"Error generating invoice: {e}")
            return None

    def upload_to_drive(self, pdf_file, customer_name):
        try:
            folder_list = self.drive.ListFile({
                'q': f"'{self.main_folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder' and title='{customer_name}'"
            }).GetList()

            # Create folder if not exists
            if folder_list:
                folder_id = folder_list[0]['id']
            else:
                folder_metadata = {
                    'title': customer_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [{'id': self.main_folder_id}]
                }
                folder = self.drive.CreateFile(folder_metadata)
                folder.Upload()
                folder_id = folder['id']

            # Upload the PDF to the Drive folder
            file_drive = self.drive.CreateFile({
                'title': os.path.basename(pdf_file),
                'parents': [{'id': folder_id}]
            })
            file_drive.SetContentFile(pdf_file)
            file_drive.Upload()

            # Set permission to be publicly accessible
            permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
            file_drive.InsertPermission(permission)

            return file_drive['alternateLink']

        except Exception as e:
            print(f"Error uploading file to Google Drive: {e}")
            return None

    def send_email(self, link, customer_name, email):
        sender_email = "bhavya.shah1403@gmail.com"
        receiver_email = email
        subject = "Invoice Generated"
        body = f"Hello {customer_name},\n\nHere is your invoice: {link}"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            # Send the email using Gmail's SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, 'chjd lgfd rjql tjlb')  # Replace with your app-specific password
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully")

        except Exception as e:
            print(f"Error sending email: {e}")
