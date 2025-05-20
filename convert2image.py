import fitz  # PyMuPDF
import os

# Make sure this path exists and PDF is in the folder
pdf_path = "source_pdf/Imran-Ali-YL14-CVY-Certificate-CaPAyYdoKc.pdf"
output_dir = "static"

# Create output folder if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Open and convert PDF pages to PNG
doc = fitz.open(pdf_path)
for i in range(len(doc)):
    pix = doc[i].get_pixmap(dpi=300)
    pix.save(os.path.join(output_dir, f"cert_bg_page{i+1}.png"))

print("PDF pages converted to images successfully!")