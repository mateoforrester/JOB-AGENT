# JobAgent — Documentación del Sistema

Todo lo que hace este proyecto, cómo está armado, y qué hacer si algo falla.

---

## Qué hace esto

Todos los días a las **8am Argentina**, un script corre automáticamente en la nube de Google (GCP) y hace esto:

1. Busca vacantes nuevas en LinkedIn para 12 roles distintos, en paralelo
2. Filtra las que ya te mandó antes (nunca repite)
3. Le pregunta a Claude qué tan buen fit es cada vacante para tu perfil
4. Te manda un email a `mateoforrester26@gmail.com` con los resultados
5. Guarda registro de las vacantes enviadas para no repetirlas mañana

Si no hay vacantes nuevas, no manda nada.

---

## Arquitectura — cómo está conectado todo

```
Google Cloud Scheduler (cron: 8am Argentina todos los días)
    │
    ▼
Cloud Run Job "daily-search"  ←── imagen Docker guardada en Artifact Registry
    │
    ├── Lee credenciales de Secret Manager
    │       ANTHROPIC_API_KEY
    │       GMAIL_APP_PASSWORD
    │
    ├── Lee/escribe sent_vacantes.json en Cloud Storage
    │       gs://job-agent-mateo-dedup/sent_vacantes.json
    │
    ├── Fetches paralelos a LinkedIn Jobs (12 roles, geoId=100446943)
    │
    ├── Llama a Claude API para analizar fit de cada vacante
    │
    └── Envía email via Gmail SMTP → mateoforrester26@gmail.com
```

---

## Proyecto GCP

- **Nombre del proyecto**: `job-agent-mateo`
- **Project Number**: `509799549216`
- **Región**: `us-central1`
- **Cuenta vinculada**: `mateoforrester26@gmail.com`

Para verlo en el browser: [console.cloud.google.com](https://console.cloud.google.com) → seleccionar proyecto `job-agent-mateo`

---

## Componentes GCP — qué es cada uno

### Cloud Run Job
Es el "trabajador" que corre el script. No está siempre prendido — solo se activa cuando el Scheduler lo llama, corre el script, y se apaga. Por eso es barato (virtualmente gratis a este nivel de uso).

- **Nombre**: `daily-search`
- **Imagen**: `us-central1-docker.pkg.dev/job-agent-mateo/jobagent/daily-search:latest`
- **Timeout**: 5 minutos máximo por ejecución
- **Reintentos**: 1 si falla

Ver en consola: Cloud Run → Jobs → `daily-search`

### Cloud Scheduler
Es el reloj que dispara el job todos los días.

- **Nombre**: `daily-job-search`
- **Schedule**: `0 11 * * *` (11am UTC = 8am Argentina)
- **Timezone**: `America/Argentina/Buenos_Aires`

Ver en consola: Cloud Scheduler → `daily-job-search`

### Cloud Storage (bucket)
Acá se guarda la lista de IDs de vacantes ya enviadas. Es el "memory" del sistema para no repetir.

- **Bucket**: `gs://job-agent-mateo-dedup`
- **Archivo**: `sent_vacantes.json` — array de IDs de LinkedIn (ej: `["4404316648", "4401940970"]`)

Ver en consola: Cloud Storage → `job-agent-mateo-dedup`

### Secret Manager
Guarda las credenciales de forma segura. El script las lee en tiempo de ejecución — nunca están en el código.

- **`GMAIL_APP_PASSWORD`**: contraseña de app de Gmail (16 caracteres)
- **`ANTHROPIC_API_KEY`**: clave de la API de Claude

Ver en consola: Security → Secret Manager

### Artifact Registry
Guarda la imagen Docker del script. Cuando hacemos cambios al código y rebuildeamos, la nueva imagen se sube acá.

- **Repositorio**: `us-central1-docker.pkg.dev/job-agent-mateo/jobagent/`
- **Imagen**: `daily-search:latest`

---

## Archivos del proyecto local

```
JobAgent/
├── CLAUDE.md                    ← Instrucciones del agente de búsqueda manual
├── SISTEMA.md                   ← Este archivo
├── .gitignore                   ← Excluye archivos sensibles
├── .claude/
│   └── commands/
│       ├── search.md            ← Lógica del comando /search (búsqueda manual)
│       ├── adapt-cv.md          ← Lógica del comando /adapt-cv
│       └── analyze-job.md       ← Lógica del comando /analyze-job
├── cv/
│   ├── mateo_forrester.md       ← CV completo de Mateo (base para adaptaciones)
│   └── output/                  ← CVs adaptados generados
├── memory/
│   ├── MEMORY.md                ← Estado de búsqueda, historial, aprendizajes
│   ├── job_hunt_state.md        ← Vacantes guardadas manualmente
│   └── sent_vacantes.json       ← Copia local del dedup (el real está en GCS)
└── scripts/
    ├── daily_search.py          ← Script principal de la automatización
    ├── send_email.py            ← Helper de envío de email (no usado directamente)
    ├── Dockerfile               ← Container del Cloud Run Job
    └── requirements.txt         ← Dependencias Python del script
```

---

## El script: `scripts/daily_search.py`

### Qué hace paso a paso

```
1. Carga IDs ya enviados desde GCS (sent_vacantes.json)
2. Busca en LinkedIn Jobs con 12 roles en paralelo:
   - automation developer, automation engineer
   - integration developer, integration engineer
   - process automation, java developer
   - backend developer, software engineer
   - software developer, fullstack developer
   - middleware developer, AI developer
   URL: linkedin.com/jobs/search/?keywords=ROL&geoId=100446943&f_TPR=r86400&sortBy=DD
   (geoId=100446943 = Argentina, f_TPR=r86400 = últimas 24hs)
3. Filtra: QA, DevOps puro, Helpdesk, Support + IDs ya enviados
4. Llama a Claude API para analizar cada vacante nueva:
   - Por qué es buen fit para Mateo (skills que matchean)
   - Qué le falta para fit perfecto (gaps reales)
   - Fit % (0-100)
   - Recomendación (aplicar ahora / adaptar CV / baja prioridad)
5. Formatea email HTML con las vacantes ordenadas por fit %
6. Envía email via Gmail SMTP (smtp.gmail.com:465)
7. Actualiza sent_vacantes.json en GCS con los nuevos IDs
```

### Variables de entorno que usa
| Variable | De dónde viene | Para qué |
|----------|---------------|----------|
| `ANTHROPIC_API_KEY` | Secret Manager | Llamar a Claude para analizar fit |
| `GMAIL_APP_PASSWORD` | Secret Manager | Autenticarse en Gmail SMTP |
| `GCS_BUCKET_NAME` | Env var del Job | Nombre del bucket de dedup |
| `GCS_PROJECT_ID` | Env var del Job | ID del proyecto GCP |

---

## Comandos útiles para operar el sistema

### Ver si el job corrió bien hoy
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud run jobs executions list --job=daily-search --region=us-central1 --project=job-agent-mateo
```

### Ver los logs de la última ejecución
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=daily-search" \
  --project=job-agent-mateo --limit=50 --format="value(textPayload)"
```

### Correr el job manualmente (sin esperar a las 8am)
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud run jobs execute daily-search --region=us-central1 --project=job-agent-mateo --wait
```

### Ver qué vacantes ya fueron enviadas
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gsutil cat gs://job-agent-mateo-dedup/sent_vacantes.json
```

### Resetear el dedup (para volver a recibir todas las vacantes)
```bash
echo "[]" | CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gsutil cp - gs://job-agent-mateo-dedup/sent_vacantes.json
```

### Actualizar el script después de hacer cambios
```bash
# 1. Editar scripts/daily_search.py con los cambios
# 2. Rebuild y redeploy:
cd scripts
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud builds submit --tag us-central1-docker.pkg.dev/job-agent-mateo/jobagent/daily-search:latest --project=job-agent-mateo

CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud run jobs update daily-search \
  --image=us-central1-docker.pkg.dev/job-agent-mateo/jobagent/daily-search:latest \
  --region=us-central1 --project=job-agent-mateo
```

### Cambiar el App Password de Gmail (si lo regenerás)
```bash
echo -n "NUEVO_APP_PASSWORD" | CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud secrets versions add GMAIL_APP_PASSWORD --data-file=- --project=job-agent-mateo
```

---

## Cómo funciona la búsqueda manual (/search)

Aparte de la automatización, podés hacer búsquedas manuales con Claude Code abriendo este proyecto y escribiendo:

```
/search 3 dias
/search 1 semana
/search hoy
```

El comando está definido en `.claude/commands/search.md` y hace lo mismo que el script automático pero te muestra los resultados acá en el chat, con el análisis de fit incluido.

También podés:
- `/adapt-cv [URL de vacante]` — adaptar tu CV a una vacante específica
- `/analyze-job [URL de vacante]` — análisis profundo de una vacante

---

## Troubleshooting — qué hacer si algo falla

### No llegó el email
1. Revisar logs (comando de logs arriba)
2. Causas comunes:
   - LinkedIn bloqueó los requests (el script intenta de todas formas, puede que haya 0 vacantes)
   - App Password expiró → regenerar en myaccount.google.com y actualizar el secreto
   - La API de Anthropic tuvo un error → el script tiene fallback sin IA

### El job falla (error en la ejecución)
1. Ver logs para identificar el error
2. Causas comunes:
   - Cambio de versión de dependencias → actualizar `requirements.txt` y rebuildelar
   - Credenciales inválidas → verificar en Secret Manager

### Quiero cambiar la hora de envío
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud scheduler jobs update http daily-job-search \
  --schedule="0 12 * * *" \
  --location=us-central1 --project=job-agent-mateo
# 0 12 * * * = 9am Argentina (UTC-3)
```

### Quiero pausar temporalmente la automatización
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud scheduler jobs pause daily-job-search --location=us-central1 --project=job-agent-mateo
```

### Quiero reactivarla
```bash
CLOUDSDK_PYTHON="/c/Users/i7Lenovo/AppData/Local/Programs/Python/Python311/python.exe" \
gcloud scheduler jobs resume daily-job-search --location=us-central1 --project=job-agent-mateo
```

---

## Costo estimado

| Componente | Free tier | Uso estimado | Costo |
|-----------|-----------|-------------|-------|
| Cloud Run Jobs | 240.000 vCPU-seg/mes gratis | ~300 seg/día × 30 = 9.000 | $0 |
| Cloud Scheduler | 3 jobs gratis | 1 job | $0 |
| Cloud Storage | 5 GB gratis | < 1 MB | $0 |
| Secret Manager | 6 versiones gratis | 2 secretos | $0 |
| Cloud Build | 120 min/día gratis | ~1 min por rebuild | $0 |
| **Total** | | | **~$0/mes** |

---

*Última actualización: 24 abril 2026*

---

## Estado actual del sistema (24 abril 2026)

### ✅ Lo que está funcionando
- Cloud Run Job corre todos los días a las 8am Argentina
- Filtra vacantes por ubicación: solo CABA + GBA + Argentina (remoto)
- CVs en PDF (3 versiones: inglés, castellano, MeLi) subidos a GCS y pasados a Claude API como documentos base64
- Email llega correctamente con diseño HTML

### 🐛 Bug pendiente: análisis de fit con IA
**Síntoma**: Las vacantes llegan con datos de fallback en vez del análisis real de Claude:
- "Por qué es buen fit": "Ver descripción completa en LinkedIn"
- "Recomendación": "Revisar manualmente"
- Fit %: 60% para todas

**Causa probable**: La función `analyze_fit()` manda todas las vacantes + 3 PDFs en UNA sola llamada a la API → excede el límite de tokens.

**Fix pendiente**: Procesar las vacantes en batches de ~15 por llamada. Ya se agregó `import traceback` al script. El fix completo (lógica de batching) quedó pendiente.

### Archivos en GCS bucket (`gs://job-agent-mateo-dedup`)
- `sent_vacantes.json` — IDs de vacantes ya enviadas (dedup)
- `cv_ingles.pdf` — CV en inglés
- `cv_castellano.pdf` — CV en castellano
- `cv_meli.pdf` — CV adaptado a MeLi
- `candidato_perfil.md` — Perfil completo del candidato
