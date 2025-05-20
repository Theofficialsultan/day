import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from flask import Flask, render_template_string

load_dotenv()

app = Flask(__name__)

def send_insurance_email(user_data):
    try:
        required_keys = [
            'name', 'email', 'policy_number', 'policy_start', 'policy_end',
            'insurer', 'duration', 'car_make', 'car_model', 'car_reg',
            'licence', 'address', 'price', 'policy_link'
        ]
        for key in required_keys:
            if key not in user_data:
                raise KeyError(f"Missing key: {key}")

        with open("templates/email_template.html", 'r', encoding='utf-8') as f:
            template_source = f.read()

        with app.app_context():
            html_content = render_template_string(template_source, **user_data)

        message = Mail(
            from_email='officialsaed@outlook.com',
            to_emails=user_data['email'],
            subject=f"RAC Temporary Insurance Policy Confirmation - {user_data["car_reg"]}",
            html_content=html_content
        )

        sg = SendGridAPIClient(os.environ.get("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"))  # Safer key usage
        response = sg.send(message)
        return response.status_code == 202

    except KeyError as ke:
        print(f"Missing data: {ke}")
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False