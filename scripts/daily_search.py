"""
daily_search.py — Búsqueda diaria de vacantes para Mateo Forrester.

Corre en GCP Cloud Run Job, disparado por Cloud Scheduler todos los días a las 8am Argentina.

Flujo:
1. Lee sent_vacantes.json desde GCS (deduplicación)
2. Busca en LinkedIn Jobs por 12 roles (paralelo)
3. Filtra QA/DevOps/helpdesk y vacantes ya enviadas
4. Llama a Claude API para analizar fit de cada vacante nueva
5. Envía email con los resultados vía Gmail SMTP
6. Actualiza sent_vacantes.json en GCS

Variables de entorno requeridas (desde GCP Secret Manager):
    ANTHROPIC_API_KEY
    GMAIL_APP_PASSWORD
    GCS_BUCKET_NAME   (ej: "jobagent-mateo-dedup")
    GCS_PROJECT_ID    (ej: "tu-proyecto-gcp")
"""

import os
import json
import re
import smtplib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import io
import time
import traceback
import requests
import anthropic
import pypdf
from google import genai as genai_client
from google.cloud import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────────────

TO_EMAIL = "mateoforrester26@gmail.com"
FROM_EMAIL = "mateoforrester26@gmail.com"
GCS_DEDUP_FILE = "sent_vacantes.json"

ROLES = [
    "automation developer",
    "automation engineer",
    "integration developer",
    "integration engineer",
    "process automation",
    "java developer",
    "backend developer",
    "software engineer",
    "software developer",
    "fullstack developer",
    "middleware developer",
    "AI developer",
]

SKIP_KEYWORDS = [
    "qa ", "quality assurance", "tester ", "testing", "devops", "helpdesk",
    "help desk", "soporte", "support engineer", "it support", "network engineer",
    "data engineer", "data scientist",
]

# Ubicaciones aceptadas (CABA + GBA). Todo lo demás se descarta.
# "argentina" sola (sin ciudad) se acepta porque muchos remotos la usan.
ALLOWED_LOCATIONS = [
    "buenos aires",
    "greater buenos aires",
    "gran buenos aires",
    "caba",
    "argentina",   # remotos que no especifican ciudad
]

# Archivos del candidato en GCS
GCS_CV_FILES = ["cv_ingles.pdf", "cv_castellano.pdf", "cv_meli.pdf"]
GCS_PROFILE_FILE = "candidato_perfil.md"

BATCH_SIZE = 10

# ── GCS helpers ────────────────────────────────────────────────────────────────

def load_sent_ids() -> set[str]:
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "")
    if not bucket_name:
        log.warning("GCS_BUCKET_NAME no configurado — dedup deshabilitado")
        return set()
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(GCS_DEDUP_FILE)
        if blob.exists():
            data = json.loads(blob.download_as_text())
            log.info(f"Cargados {len(data)} IDs ya enviados")
            return set(data)
    except Exception as e:
        log.warning(f"No se pudo leer sent_vacantes.json: {e}")
    return set()


def save_sent_ids(ids: set[str]) -> None:
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "")
    if not bucket_name:
        return
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(GCS_DEDUP_FILE)
        blob.upload_from_string(json.dumps(sorted(ids)), content_type="application/json")
        log.info(f"Guardados {len(ids)} IDs en GCS")
    except Exception as e:
        log.error(f"No se pudo guardar sent_vacantes.json: {e}")


def load_candidate_context() -> tuple[str, list[dict]]:
    """Carga el perfil de preferencias y extrae texto de los CVs en PDF desde GCS.
    Devuelve (perfil_texto_completo, []) — sin documentos binarios, todo como texto.
    """
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "")
    profile_text = ""

    if not bucket_name:
        log.warning("GCS_BUCKET_NAME no configurado — usando perfil vacío")
        return profile_text, []

    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Cargar perfil de texto
        blob = bucket.blob(GCS_PROFILE_FILE)
        if blob.exists():
            profile_text = blob.download_as_text(encoding="utf-8")
            log.info("Perfil del candidato cargado desde GCS")

        # Extraer texto de los PDFs y appendear al perfil
        cv_texts = []
        for cv_file in GCS_CV_FILES:
            blob = bucket.blob(cv_file)
            if blob.exists():
                pdf_bytes = blob.download_as_bytes()
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                cv_texts.append(f"\n\n--- CV: {cv_file} ---\n{text}")
                log.info(f"CV extraído: {cv_file} ({len(reader.pages)} páginas)")

        if cv_texts:
            profile_text += "".join(cv_texts)

    except Exception as e:
        log.warning(f"Error cargando contexto del candidato: {e}")

    return profile_text, []


# ── LinkedIn scraping ──────────────────────────────────────────────────────────

LINKEDIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}


def extract_job_id(url: str) -> str | None:
    m = re.search(r"-(\d{8,12})(?:\?|$|/)", url)
    return m.group(1) if m else None


def fetch_role(role: str, seconds: int = 86400) -> list[dict]:
    kw = role.replace(" ", "+")
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={kw}&geoId=100446943&f_TPR=r{seconds}&sortBy=DD"
    )
    try:
        resp = requests.get(url, headers=LINKEDIN_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        log.warning(f"Error fetching {role}: {e}")
        return []

    # Extraer bloques de vacantes del HTML (LinkedIn devuelve data estructurada)
    jobs = []
    # Buscar job cards: título, empresa, ubicación, link
    title_pattern = re.compile(r'class="base-search-card__title"[^>]*>\s*([^<]+)\s*<', re.I)
    company_pattern = re.compile(r'class="base-search-card__subtitle"[^>]*>\s*<[^>]+>\s*([^<]+)\s*<', re.I)
    location_pattern = re.compile(r'class="job-search-card__location"[^>]*>\s*([^<]+)\s*<', re.I)
    link_pattern = re.compile(r'href="(https://[a-z]+\.linkedin\.com/jobs/view/[^"?]+)', re.I)
    date_pattern = re.compile(r'datetime="([^"]+)"', re.I)

    titles = title_pattern.findall(resp.text)
    companies = company_pattern.findall(resp.text)
    locations = location_pattern.findall(resp.text)
    links = link_pattern.findall(resp.text)
    dates = date_pattern.findall(resp.text)

    count = min(len(titles), len(companies), len(links))
    for i in range(count):
        job_url = links[i]
        job_id = extract_job_id(job_url)
        jobs.append({
            "title": titles[i].strip(),
            "company": companies[i].strip() if i < len(companies) else "",
            "location": locations[i].strip() if i < len(locations) else "Argentina",
            "url": job_url,
            "id": job_id or job_url,
            "date": dates[i] if i < len(dates) else "",
        })

    log.info(f"  {role}: {len(jobs)} vacantes")
    return jobs


def should_skip(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in SKIP_KEYWORDS)


def is_allowed_location(location: str) -> bool:
    loc = location.lower()
    return any(allowed in loc for allowed in ALLOWED_LOCATIONS)


def fetch_all_jobs(seconds: int = 86400) -> list[dict]:
    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_role, role, seconds): role for role in ROLES}
        for future in as_completed(futures):
            for job in future.result():
                jid = job["id"]
                if jid not in seen_ids and not should_skip(job["title"]) and is_allowed_location(job["location"]):
                    seen_ids.add(jid)
                    all_jobs.append(job)

    log.info(f"Total vacantes únicas tras filtrar: {len(all_jobs)}")
    return all_jobs


# ── Descripción completa de vacantes ──────────────────────────────────────────

DESCRIPTION_PATTERNS = [
    re.compile(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>', re.S | re.I),
    re.compile(r'class="description__text[^"]*"[^>]*>(.*?)</section>', re.S | re.I),
    re.compile(r'"description"\s*:\s*\{"text"\s*:\s*"([^"]{100,})"', re.I),
]


def fetch_description(job: dict) -> None:
    """Descarga la descripción completa de la vacante y la guarda en job['description']."""
    try:
        time.sleep(0.5)
        resp = requests.get(job["url"], headers=LINKEDIN_HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
        for pattern in DESCRIPTION_PATTERNS:
            m = pattern.search(html)
            if m:
                # Limpiar tags HTML básicos
                text = re.sub(r"<[^>]+>", " ", m.group(1))
                text = re.sub(r"\s+", " ", text).strip()
                if len(text) > 100:
                    job["description"] = text[:3000]  # limitar para no explotar tokens
                    return
        job["description"] = ""
    except Exception as e:
        log.warning(f"No se pudo bajar descripción de {job['url']}: {e}")
        job["description"] = ""


def pre_filter_titles(jobs: list[dict], profile_text: str) -> list[dict]:
    """Descarta con solo los títulos las vacantes que claramente no aplican al perfil."""
    if not jobs:
        return []

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    titles_text = "\n".join(
        f"{i+1}. {j['title']} @ {j['company']}"
        for i, j in enumerate(jobs)
    )

    prompt = f"""Sos un headhunter senior filtrando vacantes para este candidato:

{profile_text[:2000]}

Dado este listado de vacantes (solo títulos y empresa), devolvé un JSON array con los números (1-based) de las vacantes que tienen POTENCIAL REAL para este candidato (fit estimado > 40%).
Descartá solo las que claramente no aplican: roles de soporte, QA manual, DevOps puro, tecnologías completamente distintas al stack del candidato.
En caso de duda, INCLUIR — es mejor analizar de más que perder una oportunidad.

Vacantes:
{titles_text}

Respondé SOLO con el JSON array de números, ejemplo: [1, 3, 5, 7]. Sin texto adicional."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.M).strip()
        indices = json.loads(raw)
        selected = [jobs[i - 1] for i in indices if 1 <= i <= len(jobs)]
        log.info(f"Pre-filtro: {len(jobs)} → {len(selected)} vacantes con potencial")
        return selected
    except Exception as e:
        log.warning(f"Error en pre-filtro, usando todas las vacantes: {e}")
        return jobs


# ── Análisis de fit — Claude con fallback a Gemini ────────────────────────────

def _build_prompt(profile_section: str, jobs_text: str) -> str:
    return f"""Sos un headhunter senior evaluando vacantes para un candidato.

{profile_section}Analizá estas vacantes comparándolas con el perfil real del candidato y devolvé un JSON array con objetos:
{{
  "index": <número de 1 a N>,
  "fit_stars": <1-5>,
  "fit_pct": <número 0-100>,
  "why_fit": ["razón concreta basada en la descripción real", "razón 2", "razón 3"],
  "gaps": ["gap real que pide la vacante y no tiene el candidato"],
  "recommendation": "una línea — aplicar ahora / adaptar CV primero / baja prioridad",
  "stack_tags": ["tech1", "tech2"]
}}

Reglas de scoring:
- 5 estrellas (85-100%): automation/integration/BPM/Java con fintech — match directo
- 4 estrellas (70-84%): Java o APIs como core del rol
- 3 estrellas (55-69%): software engineer general con algo del stack
- 2 estrellas (40-54%): solo stack secundario o perfil diferente

Vacantes:
{jobs_text}
Respondé SOLO con el JSON array, sin texto adicional."""


def _call_claude(prompt: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.M).strip()
    return json.loads(raw)


def _call_gemini(prompt: str) -> list[dict]:
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY no configurada")
    client = genai_client.Client(api_key=gemini_key)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.M).strip()
    return json.loads(raw)


def analyze_fit(jobs: list[dict], profile_text: str, pdf_documents: list[dict] = None) -> list[dict]:
    if not jobs:
        return []

    profile_section = f"Perfil del candidato:\n{profile_text}\n\n" if profile_text else ""

    for batch_start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[batch_start:batch_start + BATCH_SIZE]

        jobs_text = ""
        for i, j in enumerate(batch):
            desc = j.get("description", "")
            desc_section = f"\n   Descripción: {desc}" if desc else ""
            jobs_text += f"{i+1}. {j['title']} @ {j['company']} — {j['location']}{desc_section}\n\n"

        prompt = _build_prompt(profile_section, jobs_text)
        batch_num = batch_start // BATCH_SIZE + 1
        analyses = None

        # Intentar con Claude primero
        try:
            analyses = _call_claude(prompt)
            log.info(f"Batch {batch_num}: analizado con Claude OK")
        except Exception as e:
            log.warning(f"Claude falló (batch {batch_num}): {e} — intentando con Gemini...")
            try:
                analyses = _call_gemini(prompt)
                log.info(f"Batch {batch_num}: analizado con Gemini OK")
            except Exception as e2:
                log.error(f"Gemini también falló (batch {batch_num}): {e2}")
                log.error(traceback.format_exc())

        if analyses:
            for a in analyses:
                idx = a["index"] - 1 + batch_start
                if 0 <= idx < len(jobs):
                    jobs[idx].update(a)
        else:
            for job in batch:
                job.setdefault("fit_stars", 3)
                job.setdefault("fit_pct", 60)
                job.setdefault("why_fit", ["Ver descripción completa en LinkedIn"])
                job.setdefault("gaps", [])
                job.setdefault("recommendation", "Revisar manualmente")
                job.setdefault("stack_tags", [])

        # Pausa entre batches para respetar rate limits del free tier de Gemini
        if batch_start + BATCH_SIZE < len(jobs):
            time.sleep(15)

    return jobs


# ── Formateo HTML del email ────────────────────────────────────────────────────

STAR_MAP = {5: "⭐⭐⭐⭐⭐", 4: "⭐⭐⭐⭐", 3: "⭐⭐⭐", 2: "⭐⭐", 1: "⭐"}


def format_email_html(jobs: list[dict], date_str: str) -> str:
    if not jobs:
        return ""

    # Ordenar por fit desc
    jobs_sorted = sorted(jobs, key=lambda j: j.get("fit_pct", 0), reverse=True)

    cards = ""
    for j in jobs_sorted:
        stars = STAR_MAP.get(j.get("fit_stars", 3), "⭐⭐⭐")
        pct = j.get("fit_pct", "—")
        why = "".join(f"<li>{r}</li>" for r in j.get("why_fit", []))
        gaps_list = j.get("gaps", [])
        gaps_html = (
            "".join(f"<li>{g}</li>" for g in gaps_list)
            if gaps_list
            else "<li>Sin gaps significativos — aplicar con confianza ✅</li>"
        )
        tags = " ".join(f'<span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:4px">{t}</span>' for t in j.get("stack_tags", []))
        rec = j.get("recommendation", "")

        cards += f"""
        <div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin-bottom:16px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <h3 style="margin:0 0 4px;font-size:16px;color:#202124">
                <a href="{j['url']}" style="color:#1a73e8;text-decoration:none">{j['title']}</a>
              </h3>
              <p style="margin:0;color:#5f6368;font-size:14px">{j['company']} · {j['location']}</p>
            </div>
            <div style="text-align:right;flex-shrink:0;margin-left:16px">
              <div style="font-size:16px">{stars}</div>
              <div style="font-size:13px;color:#5f6368;font-weight:600">{pct}% fit</div>
            </div>
          </div>
          <div style="margin-top:12px">{tags}</div>
          <table style="margin-top:14px;width:100%;border-collapse:collapse">
            <tr>
              <td style="vertical-align:top;padding-right:16px;width:50%">
                <p style="margin:0 0 6px;font-weight:600;font-size:13px;color:#188038">✅ Por qué es buen fit</p>
                <ul style="margin:0;padding-left:16px;font-size:13px;color:#3c4043;line-height:1.6">{why}</ul>
              </td>
              <td style="vertical-align:top;width:50%">
                <p style="margin:0 0 6px;font-weight:600;font-size:13px;color:#c5221f">⚠️ Qué le falta para fit perfecto</p>
                <ul style="margin:0;padding-left:16px;font-size:13px;color:#3c4043;line-height:1.6">{gaps_html}</ul>
              </td>
            </tr>
          </table>
          <p style="margin:12px 0 0;font-size:13px;color:#5f6368;border-top:1px solid #f1f3f4;padding-top:10px">
            <strong>Recomendación:</strong> {rec}
          </p>
        </div>"""

    total = len(jobs_sorted)
    top5 = sum(1 for j in jobs_sorted if j.get("fit_stars", 0) >= 4)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8f9fa;margin:0;padding:20px">
  <div style="max-width:700px;margin:0 auto">
    <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:24px;border-radius:10px 10px 0 0;color:#fff">
      <h1 style="margin:0 0 4px;font-size:22px">🔍 Vacantes del día</h1>
      <p style="margin:0;opacity:0.85;font-size:14px">{date_str} · {total} nuevas · {top5} con fit alto</p>
    </div>
    <div style="background:#fff;padding:16px;border-radius:0 0 10px 10px;border:1px solid #e0e0e0;border-top:none">
      {cards}
    </div>
    <p style="text-align:center;font-size:12px;color:#9aa0a6;margin-top:16px">
      JobAgent · mateoforrester26@gmail.com
    </p>
  </div>
</body>
</html>"""


# ── Envío de email ─────────────────────────────────────────────────────────────

def send_email(subject: str, html_body: str) -> None:
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, app_password)
        server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

    log.info(f"Email enviado: {subject}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("=== JobAgent Daily Search ===")
    today = datetime.now().strftime("%d/%m/%Y")

    # 1. Cargar contexto del candidato (CVs + perfil) y IDs ya enviados
    profile_text, _ = load_candidate_context()
    sent_ids = load_sent_ids()

    # 2. Buscar vacantes nuevas en LinkedIn
    all_jobs = fetch_all_jobs(seconds=3600)  # TEST: última hora para probar con pocas vacantes

    # 3. Filtrar ya enviadas
    new_jobs = [j for j in all_jobs if j["id"] not in sent_ids]
    log.info(f"Vacantes nuevas (no enviadas antes): {len(new_jobs)}")

    if not new_jobs:
        log.info("No hay vacantes nuevas hoy. No se envía email.")
        return

    # 4. Pre-filtrar por títulos (descarta las que claramente no aplican)
    log.info("Pre-filtrando vacantes por título...")
    pre_filtered = pre_filter_titles(new_jobs, profile_text)

    if not pre_filtered:
        log.info("Ninguna vacante pasó el pre-filtro. No se envía email.")
        return

    # 5. Bajar descripción completa de cada vacante que pasó el filtro
    log.info(f"Bajando descripciones de {len(pre_filtered)} vacantes...")
    for job in pre_filtered:
        fetch_description(job)

    # 6. Analizar fit con Claude API usando descripción real + CV completo
    log.info("Analizando fit con Claude API (descripción completa)...")
    analyzed = analyze_fit(pre_filtered, profile_text)

    # Solo mostrar vacantes con fit >= 2 estrellas
    filtered = [j for j in analyzed if j.get("fit_stars", 0) >= 2]
    if not filtered:
        log.info("No hay vacantes con fit suficiente. No se envía email.")
        return

    # 7. Formatear y enviar email
    html = format_email_html(filtered, today)
    if not html:
        return

    top = sum(1 for j in filtered if j.get("fit_stars", 0) >= 4)
    subject = f"💼 {len(filtered)} vacantes nuevas hoy — {top} con fit alto ({today})"
    send_email(subject, html)

    # 6. Actualizar dedup
    new_ids = {j["id"] for j in new_jobs}
    save_sent_ids(sent_ids | new_ids)
    log.info(f"Done. {len(filtered)} vacantes enviadas.")


if __name__ == "__main__":
    main()
