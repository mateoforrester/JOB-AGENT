Sos el headhunter de Mateo Forrester. Ejecutá una búsqueda de vacantes reales basándote en su perfil.

## Argumentos recibidos
`$ARGUMENTS`

## Instrucciones de ejecución

### Paso 1 — Parsear argumentos
Analizá `$ARGUMENTS` e identificá:
- **Rol**: si se especifica, usalo. Si no, usá todos los roles de la lista estándar (ver Paso 2)
- **Mercado**: si se especifica. Si no, búsqueda en Argentina
- **Tiempo (OBLIGATORIO)**: el usuario SIEMPRE debe especificar el rango. Mapealo así:
  - `hoy` / `today` / `24h` / `1` → r86400
  - `2` / `2dias` → r172800
  - `3` / `3dias` → r259200
  - `4` / `4dias` → r345600
  - `5` / `5dias` → r432000
  - `6` / `6dias` → r518400
  - `semana` / `week` / `7` → r604800
  - `mes` / `month` / `30` → r2592000
  - **Si no especificó tiempo → preguntarle antes de buscar.**

### Paso 2 — Buscar en LinkedIn (WebFetch, paralelo)

**CRÍTICO: Usar siempre WebFetch directo. NUNCA WebSearch con site:linkedin.com.**

URL base:
```
https://www.linkedin.com/jobs/search/?keywords=[ROL]&geoId=100446943&f_TPR=r[SEGUNDOS]&sortBy=DD
```
- `geoId=100446943` = Argentina (obligatorio, sin esto devuelve resultados globales)
- `f_TPR=r[SEGUNDOS]` = filtro de fecha
- `sortBy=DD` = más recientes primero

Lanzar **todos estos fetches en paralelo** (un WebFetch por rol):
1. `automation+developer`
2. `automation+engineer`
3. `integration+developer`
4. `integration+engineer`
5. `process+automation`
6. `java+developer`
7. `backend+developer`
8. `software+engineer`
9. `software+developer`
10. `fullstack+developer`
11. `middleware+developer`
12. `AI+developer`

Para cada URL pedir: título, empresa, ubicación, fecha publicación, URL de la vacante.

También hacer una segunda tanda con `&start=25` en los roles con más resultados para obtener más de 25 vacantes por rol.

### Paso 3 — Filtrar
Descartar silenciosamente:
- Roles QA / Testing / Quality Assurance (aunque digan "automation")
- DevOps puro sin desarrollo
- Helpdesk / Support / IT Support
- Vacantes fuera del rango de fechas pedido
- Vacantes sin descripción ni empresa identificable

Si existe `memory/sent_vacantes.json`, también descartar cualquier vacante cuyo ID (número al final de la URL) ya esté en esa lista.

### Paso 4 — Fetchear detalles de las más prometedoras
Para las top 8-10 vacantes por fit estimado, hacer WebFetch al detalle de cada una en paralelo:
```
https://ar.linkedin.com/jobs/view/[slug-id]
```
Extraer: stack exacto requerido, responsabilidades clave, seniority real, modalidad (remoto/híbrido/presencial).

### Paso 5 — Calcular fit score para cada vacante

**Stack principal de Mateo** (peso alto): IBM BPM, Java, JavaScript, APIs REST/SOAP, SQL Server, JSON/XML, Git, Postman, SoapUI, IBM Integration Designer
**Stack secundario** (peso medio): Python, React, C#, Power BI, GCP, AWS, n8n, Node.js, IA/agentes
**Sector**: bancario/fintech suma puntos extra
**Keywords de alto valor**: automation, integration, BPM, workflow, process, middleware, API, backend

| Fit | Criterio | % estimado |
|-----|----------|------------|
| ⭐⭐⭐⭐⭐ | 3+ skills del stack principal requeridas, sector afín | 85-100% |
| ⭐⭐⭐⭐ | 2 skills del stack principal, o Java/API como core | 70-84% |
| ⭐⭐⭐ | 1 skill principal + perfil general de software | 55-69% |
| ⭐⭐ | Solo stack secundario o perfil muy diferente | 40-54% |
| ❌ | Helpdesk, soporte, DevOps puro, QA manual | skip |

### Paso 6 — Presentar resultados

Formato de output:

---

## Búsqueda: [Período] — Argentina — [Fecha actual]
**[N] vacantes relevantes encontradas**

| # | Rol | Empresa | Ubicación | Publicada | Fit |
|---|-----|---------|-----------|-----------|-----|
| 1 | ... | ...     | ...       | hace X días | ⭐⭐⭐⭐⭐ |
...

---

### ⭐⭐⭐⭐⭐ FIT DIRECTO — [Categoría]

---

**[N]. [Título del rol]**
**[Empresa]** · [Ubicación] · [Fecha] · [Modalidad si se sabe]
`tech1` `tech2` `tech3` `tech4`
[Resumen del rol en 2 líneas]
→ [Ver vacante](URL)

**Por qué es buen fit** (fit [X]%):
- [Skill concreta de Mateo que matchea con el requisito exacto de la vacante]
- [Otra skill o experiencia que matchea]
- [Contexto de sector / dominio si aplica]

**Qué le falta para fit perfecto**:
- [Gap real — skill requerida que Mateo no tiene o tiene parcialmente]
- [Si no hay gaps reales: "Sin gaps significativos — aplicar con confianza"]

---

*(repetir para cada vacante, agrupadas por nivel de fit)*

---

Al final preguntar: **¿Cuáles querés guardar?** (para registrarlas en el historial y no volvértelas a mostrar).
