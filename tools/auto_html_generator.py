import fitz  # PyMuPDF
import os

# Set paths
PDF_PATH = "source_pdf/Imran-Ali-YL14-CVY-Certificate-CaPAyYdoKc.pdf"
OUTPUT_HTML = "templates/certificate_template.html"

# Jinja placeholder map (manual mapping of important text values)
jinja_map = {
    "Imran Ali": "{{ name }}",
    "YL14 CVY": "{{ car_reg }}",
    "16 April 2025 at 13:00": "{{ policy_start }}",
    "23 April 2025 at 13:00": "{{ policy_end }}",
    "1631H00006043103713D": "{{ policy_number }}",
    "4 Cheviot Road Leicester   LE2 6RG": "{{ address }}",
    "£123.31": "{{ price }}",
    "08/11/2002": "{{ dob }}",
    "ALI99011082IH9AL": "{{ licence }}",
    "BMW": "{{ car_make }}",
    "4 SERIES": "{{ car_model }}"
}

def extract_pdf_to_html(pdf_path, output_html_path):
    doc = fitz.open(pdf_path)
    html_output = ["<html><head><meta charset='utf-8'><style>body { font-family: Arial; font-size: 12px; }</style></head><body>"]

    for page_num, page in enumerate(doc, 1):
        text_blocks = page.get_text("dict")["blocks"]
        html_output.append(f'<div style="page-break-after: always;"><h3>Page {page_num}</h3>')

        for block in text_blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    txt = span["text"].strip()

                    # Replace known values with Jinja placeholders
                    for original, jinja_var in jinja_map.items():
                        if original in txt:
                            txt = txt.replace(original, jinja_var)

                    if txt:
                        style = f"position:absolute; left:{span['bbox'][0]}px; top:{span['bbox'][1]}px;"
                        line_text += f"<span style='{style}'>{txt}</span> "
                if line_text:
                    html_output.append(f"<div style='margin:5px 0;'>{line_text}</div>")

        html_output.append("</div>")  # End of page

    html_output.append("</body></html>")

    # Save HTML to file
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_output))

    print(f"[+] Generated HTML with placeholders: {output_html_path}")

if __name__ == "__main__":
    extract_pdf_to_html(PDF_PATH, OUTPUT_HTML)