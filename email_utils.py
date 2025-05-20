import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template_string
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def send_insurance_email(user_data):
    try:
        with open("templates/email_template.html", 'r', encoding='utf-8') as f:
            template_source = f.read()

        with app.app_context():
            html_content = render_template_string(template_source, **user_data)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"RAC Temporary Insurance Policy Confirmation - {user_data['car_reg']}"
        msg["From"] = f"RAC Insurance <{os.getenv('EMAIL_FROM')}>"
        msg["To"] = user_data["email"]
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.sendmail(msg["From"], msg["To"], msg.as_string())
        server.quit()

        return True

    except Exception as e:
        import traceback
        print("Email sending failed:", e)
        traceback.print_exc()
        return False
    