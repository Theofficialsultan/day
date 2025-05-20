import os
import requests
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

        if os.getenv("USE_MAILGUN", "false").lower() == "true":
            MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
            MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
            if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
                raise Exception("Mailgun credentials not found.")

            # DEBUG: Print Mailgun details before sending
            print("Preparing to send email via Mailgun...")
            print("Using API key:", MAILGUN_API_KEY[:10] + "..." if MAILGUN_API_KEY else "Missing")
            print("Domain:", MAILGUN_DOMAIN or "Missing")
            print("Recipient email:", user_data.get("email", "Missing"))
            print("Endpoint:", f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages" if MAILGUN_DOMAIN else "Missing domain")

            response = requests.post(
                f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                auth=("api", MAILGUN_API_KEY),
                data={
                    "from": f"RAC Insurance <no-reply@{MAILGUN_DOMAIN}>",
                    "to": [user_data["email"]],
                    "subject": f"RAC Temporary Insurance Policy Confirmation - {user_data['car_reg']}",
                    "html": html_content
                }
            )
            return response.status_code == 200

        else:
            message = Mail(
                from_email='officialsaed@outlook.com',
                to_emails=user_data['email'],
                subject=f"RAC Temporary Insurance Policy Confirmation - {user_data['car_reg']}",
                html_content=html_content
            )

            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            response = sg.send(message)
            return response.status_code == 202

    except KeyError as ke:
        print(f"Missing data: {ke}")
        return False
    except Exception as e:
        import traceback
        print("Error sending email:", e)
        traceback.print_exc()
        return False