"""
generate_pdf.py — Genera el CV de Mateo en PDF.
Uso: python cv/generate_pdf.py <html_file> <output_pdf>
"""
import sys
import os
import subprocess

WKHTMLTOPDF = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

def generate(html_path, pdf_path):
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    abs_html = os.path.abspath(html_path)
    abs_pdf  = os.path.abspath(pdf_path)
    cmd = [
        WKHTMLTOPDF,
        '--enable-local-file-access',
        '--page-size', 'A4',
        '--margin-top', '0mm',
        '--margin-bottom', '0mm',
        '--margin-left', '0mm',
        '--margin-right', '0mm',
        '--encoding', 'UTF-8',
        '--disable-smart-shrinking',
        '--zoom', '1.0',
        '--dpi', '150',
        '--quiet',
        abs_html,
        abs_pdf
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(f"PDF generado: {abs_pdf}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python cv/generate_pdf.py <html_file> <output_pdf>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
