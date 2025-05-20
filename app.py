from flask import Flask, render_template, request, redirect, url_for, make_response
from email_utils import send_insurance_email
from certificate_generator import generate_certificate
from weasyprint import HTML
import json, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import urllib.parse

load_dotenv()

app = Flask(__name__)
DATA_FILE = 'users.json'

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_users()

    # NEW: support auto-login via email link
    auto_key = request.args.get('auto_login')
    if auto_key:
        key = urllib.parse.unquote(auto_key)
        print(f"[AUTO-LOGIN] Key from URL: {key}")
        if key in users:
            user = users[key]
            user['certificate_url'] = url_for('view_certificate', user_id=key)
            return render_template('index.html', **user)
        else:
            return "No user found", 404

    if request.method == 'POST':
        surname = request.form.get('surname', '').capitalize()
        dob = f"{request.form.get('dob_day', '').zfill(2)}-{request.form.get('dob_month', '').zfill(2)}-{request.form.get('dob_year', '')}"
        postcode = request.form.get('postcode', '').replace(" ", "").upper()
        key = f"{surname}|{dob}|{postcode}"

        print(f"[LOGIN] Generated key: {key}")

        if key in users:
            user = users[key]
            user['certificate_url'] = url_for('view_certificate', user_id=key)
            return render_template('index.html', **user)
        else:
            return "No user found", 404
    return render_template('login.html')

# Remaining routes are unchanged...


# NEW: Route to render certificate_template.html directly using user data
@app.route('/certificate/<path:user_id>')
def view_certificate(user_id):
    user_id = urllib.parse.unquote(user_id)
    users = load_users()
    if user_id in users:
        user = users[user_id]

        # Format policy_start and policy_end as DD/MM/YYYY
        try:
            start = datetime.strptime(user['cover_start_date'], "%d %B %Y").strftime("%d/%m/%Y")
            end = datetime.strptime(user['cover_end_date'], "%d %B %Y").strftime("%d/%m/%Y")
        except Exception as e:
            print("Date formatting error:", e)
            start = user['cover_start_date']
            end = user['cover_end_date']

        # Get first 8 digits of the policy number and add dashes
        short_cert = user['policy_number'][:8] + "--"

        watermark_text = f"{start}-{end} {user['name']} {short_cert}"

        # Render HTML as string
        rendered = render_template("certificate_template.html", watermark_text=watermark_text, **user)

        # Generate PDF from HTML
        pdf = HTML(string=rendered, base_url=request.base_url).write_pdf()

        # Serve PDF inline
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=certificate_{user["car_reg"]}.pdf'
        return response
    else:
        return "User not found", 404

@app.route('/admin')
def admin():
    users = load_users()
    filtered_users = {
        k: v for k, v in users.items()
        if isinstance(v, dict) and 'email' in v and 'name' in v
    }
    return render_template('admin.html', users=filtered_users)

@app.route('/admin/add', methods=['POST'])
def add_user():
    data = request.form.to_dict()

    raw_dob = data['dob'].strip().replace('/', '-')
    try:
        dob_obj = datetime.strptime(raw_dob, "%d-%m-%Y")
        dob_formatted = dob_obj.strftime("%d-%m-%Y")
    except ValueError:
        return "Invalid DOB format. Use DD-MM-YYYY.", 400

    surname_cap = data['surname'].capitalize()
    name_cap = data['name'].capitalize()
    postcode_clean = data['postcode'].replace(" ", "").upper()
    reg_caps = data['reg'].upper()
    key = f"{surname_cap}|{dob_formatted}|{postcode_clean}"

    print(f"[ADMIN ADD] Generated key: {key}")

    users = load_users()

    # Auto-increment certificate number and ref number
    last_cert_number = max(
        [int(u['policy_number'][9:17]) for u in users.values() if 'policy_number' in u] or [60431037]
    )
    last_ref_number = max(
        [int(u['reference_number']) for u in users.values() if 'reference_number' in u] or [43122313]
    )

    new_cert_number = last_cert_number + 1
    new_ref_number = last_ref_number + 1

    policy_number = f"1631H0000{new_cert_number:08d}D"
    reference_number = f"{new_ref_number:08d}"

    duration_days = int(data.get('duration', 2))
    now = datetime.now()
    end = now + timedelta(days=duration_days)

    cert_filename = f"{name_cap.replace(' ', '_')}_{reg_caps}.pdf"

    user_info = {
        "surname": surname_cap,
        "dob": dob_formatted,
        "postcode": data["postcode"],
        "name": name_cap,
        "email": data["email"],
        "car": data["car"],
        "car_make": data["car"].split()[0].capitalize(),
        "car_model": " ".join(data["car"].split()[1:]).capitalize(),
        "car_reg": reg_caps,
        "reg": reg_caps,
        "home_address": data["home_address"],
        "address": data["home_address"],
        "licence": data["licence"],
        "cover_start_date": now.strftime("%d %B %Y"),
        "cover_start_time": now.strftime("%H:%M"),
        "cover_end_date": end.strftime("%d %B %Y"),
        "cover_end_time": end.strftime("%H:%M"),
        "duration": f"{duration_days} Days",
        "policy_start": f"{now.strftime('%d %B %Y')} {now.strftime('%H:%M')}",
        "policy_end": f"{end.strftime('%d %B %Y')} {end.strftime('%H:%M')}",
        "policy_number": policy_number,
        "certificate_number": policy_number,
        "reference_number": reference_number,
        "insurer": "Aviva",
        "price": data.get("price", "£84.19"),
        "contact_number": data.get("contact_number", ""),
        "occupation": data.get("occupation", ""),
        "policy_link": url_for('login', _external=True) + f"?auto_login={urllib.parse.quote_plus(key)}",
        "email_sent": False
    }

    users[key] = user_info
    save_users(users)

    # Generate certificate
    generate_certificate(user_info)

    return redirect(url_for('admin'))

@app.route('/admin/delete/<path:user_id>', methods=['POST'])
def delete_user(user_id):
    user_id = urllib.parse.unquote(user_id)
    users = load_users()
    if user_id in users:
        del users[user_id]
        save_users(users)
    return redirect(url_for('admin'))

@app.route('/admin/email/<user_id>', methods=['POST'])
def issue_email(user_id):
    users = load_users()
    if user_id in users:
        success = send_insurance_email(users[user_id])
        if success:
            users[user_id]['email_sent'] = True
            save_users(users)
        else:
            return "Email failed", 500
    return redirect(url_for('admin'))


# ✅ NEW: Route to generate the PDF dynamically
@app.route('/admin/generate_pdf/<path:user_id>')
def generate_pdf(user_id):
    user_id = urllib.parse.unquote(user_id)
    users = load_users()
    if user_id in users:
        user = users[user_id]

        # Render the certificate template
        rendered = render_template("certificate_template.html",
                                   watermark_text='',
                                   **user)

        # Generate PDF using WeasyPrint
        pdf = HTML(string=rendered).write_pdf()

        # Send the PDF as a response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={user["name"].replace(" ", "_")}_certificate.pdf'
        return response
    else:
        return "User not found", 404


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
