import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import Flask, render_template_string

app = Flask(__name__)

def send_insurance_email(user_data):
    try:
        with open("templates/email_template.html", 'r', encoding='utf-8') as f:
            template_source = f.read()

        with app.app_context():
            html_content = render_template_string(template_source, **user_data)

        message = Mail(
            from_email="officialsaed@outlook.com",
            to_emails=user_data['email'],
            subject=f"RAC Temporary Insurance Policy Confirmation - {user_data['car_reg']}",
            html_content=html_content
        )

        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        return response.status_code == 202

    except Exception as e:
        print("Error sending email:", e)
        return False