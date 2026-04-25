"""
send_email.py — Envía el reporte diario de vacantes por Gmail SMTP.

Uso:
    python scripts/send_email.py --subject "Asunto" --body-file path/to/body.html
    python scripts/send_email.py --subject "Asunto" --body "contenido HTML"

Credenciales: scripts/gmail_credentials.json
    {
        "email": "mateoforrester26@gmail.com",
        "app_password": "xxxx xxxx xxxx xxxx"
    }
"""

import smtplib
import json
import argparse
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

CREDENTIALS_FILE = Path(__file__).parent / "gmail_credentials.json"
TO_EMAIL = "mateoforrester26@gmail.com"


def load_credentials():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: No se encontró {CREDENTIALS_FILE}")
        print("Creá el archivo con este formato:")
        print('  {"email": "mateoforrester26@gmail.com", "app_password": "xxxx xxxx xxxx xxxx"}')
        sys.exit(1)

    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        creds = json.load(f)

    if creds.get("app_password") in ("", "xxxx xxxx xxxx xxxx", None):
        print("ERROR: Configurá tu App Password en scripts/gmail_credentials.json")
        print("Instrucciones: myaccount.google.com → Security → App Passwords")
        sys.exit(1)

    return creds


def send_email(subject: str, body_html: str):
    creds = load_credentials()
    from_email = creds["email"]
    app_password = creds["app_password"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = TO_EMAIL

    # Versión texto plano como fallback
    text_body = body_html.replace("<br>", "\n").replace("<br/>", "\n")
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, app_password)
        server.sendmail(from_email, TO_EMAIL, msg.as_string())

    print(f"Email enviado a {TO_EMAIL}: {subject}")


def main():
    parser = argparse.ArgumentParser(description="Envía reporte de vacantes por email")
    parser.add_argument("--subject", required=True, help="Asunto del email")
    parser.add_argument("--body", help="Contenido HTML del email (inline)")
    parser.add_argument("--body-file", help="Path a archivo HTML con el cuerpo del email")
    args = parser.parse_args()

    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    elif args.body:
        body = args.body
    else:
        # Leer de stdin
        body = sys.stdin.read()

    if not body.strip():
        print("ERROR: El cuerpo del email está vacío.")
        sys.exit(1)

    send_email(args.subject, body)


if __name__ == "__main__":
    main()
