import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

        # Set up Brevo SMTP email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"RAC Temporary Insurance Policy Confirmation - {user_data['car_reg']}"
        msg["From"] = os.getenv("SMTP_USER")
        msg["To"] = user_data["email"]
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.sendmail(msg["From"], msg["To"], msg.as_string())
        server.quit()

        return True

    except KeyError as ke:
        print(f"Missing data: {ke}")
        return False
    except Exception as e:
        import traceback
        print("Error sending email:", e)
        traceback.print_exc()
        return False