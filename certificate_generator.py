import os
import time
from flask import Flask, render_template_string
from weasyprint import HTML
from datetime import datetime
import fitz  # PyMuPDF
from jinja2 import Template

app = Flask(__name__)

def generate_certificate(user_data, output_dir="static/certificates"):
    start_time = time.time()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    print("[CERTIFICATE] Output directory ready.")

    # Fix watermark spacing regardless of name length
    if 'cover_start_date' in user_data and 'cover_end_date' in user_data and 'name' in user_data and 'policy_number' in user_data:
        try:
            start = datetime.strptime(user_data['cover_start_date'], "%d %B %Y").strftime("%d/%m/%Y")
            end = datetime.strptime(user_data['cover_end_date'], "%d %B %Y").strftime("%d/%m/%Y")
            short_cert = user_data['policy_number'][:8] + "--"

            # Trim long names to prevent overflow
            max_name_length = 20
            trimmed_name = user_data['name'][:max_name_length]

            base_text = f"{start}-{end} {trimmed_name} {short_cert}"
            fixed_text = base_text[:45].ljust(45)
            user_data['watermark_text'] = "   ".join([fixed_text] * 30)
            print("[CERTIFICATE] Watermark generated.")
        except Exception as e:
            print("Watermark formatting error:", e)

    # Load the certificate template
    with open("templates/certificate_template.html", "r", encoding="utf-8") as f:
        template = f.read()
    print("[CERTIFICATE] Template loaded.")

    # Render with Jinja inside Flask app context
    with app.app_context():
        rendered_html = render_template_string(template, **user_data)
    print("[CERTIFICATE] HTML rendered.")

    # Build PDF filename
    filename = f"{user_data['name'].replace(' ', '_')}_{user_data['car_reg'].replace(' ', '')}.pdf"
    output_path = os.path.join(output_dir, filename)

    # Generate PDF from HTML
    print("[CERTIFICATE] Generating PDF...")
    HTML(string=rendered_html).write_pdf(output_path)
    print(f"[CERTIFICATE] PDF generated: {output_path}")

    print(f"[CERTIFICATE] Total time: {round(time.time() - start_time, 2)} seconds")

    # Return relative URL to be used in frontend
    return f"/{output_path}"


# NEW: Build a placeholder-based certificate template from real PDF
def create_placeholder_certificate_template(input_pdf_path="original/certificate_original.pdf",
                                            output_template_path="templates/certificate_template_preview.pdf"):
    doc = fitz.open(input_pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Optional: remove previous text/images if needed
        page.clean_contents()

        # Inject placeholder text
        page.insert_text((100, 150), "{{ name }}", fontsize=12)
        page.insert_text((100, 170), "{{ car_reg }}", fontsize=12)
        page.insert_text((100, 190), "{{ policy_start }}", fontsize=12)
        page.insert_text((100, 210), "{{ policy_end }}", fontsize=12)
        page.insert_text((100, 230), "{{ licence }}", fontsize=12)

        # Optional watermark placeholder
        page.insert_textbox(
            fitz.Rect(0, 0, page.rect.width, page.rect.height),
            "{{ watermark_text }}",
            fontsize=40,
            rotate=45,
            color=(0.8, 0.8, 0.8),
            align=1
        )

    doc.save(output_template_path)
    print(f"Placeholder preview saved to: {output_template_path}")