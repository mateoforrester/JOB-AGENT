Sos el headhunter de Mateo Forrester. Adaptá su CV a la vacante específica que te pasaron.

## Input recibido
`$ARGUMENTS`

## Instrucciones de ejecución

### Paso 1 — Obtener el job description completo
- Si `$ARGUMENTS` es una **URL**: usá `WebFetch` para obtener el contenido completo de la página
- Si `$ARGUMENTS` es **texto directo**: usarlo tal cual

Si no se recibió nada, pedirle a Mateo que pegue la descripción del puesto o la URL.

### Paso 2 — Analizar el job description

Identificá y listá internamente:

**Keywords técnicas** (tecnologías, herramientas, lenguajes mencionados)
**Keywords de negocio** (sector, tipo de empresa, metodología)
**Skills obligatorias** (must-have del rol)
**Skills deseables** (nice-to-have)
**Tone de la empresa** (formal/startup, español/inglés, etc.)
**Idioma requerido** para la postulación

### Paso 3 — Comparar con el perfil de Mateo

Abrí y leé `cv/mateo_forrester.md` para tener el CV base.

Mapeá:
- ✅ **Match fuerte**: skills requeridas que Mateo tiene bien desarrolladas
- ⚡ **Match parcial**: skills que Mateo tiene pero con menor profundidad
- ❌ **Gap**: skills que Mateo no tiene (no inventar ni exagerar)

### Paso 4 — Generar el CV adaptado (HTML + PDF)

**Reglas de diseño — OBLIGATORIAS:**
- El CV tiene **una sola sección de resumen/perfil**: el "Sobre Mi" del sidebar. NO agregar sección "Resumen" en el main.
- El "Sobre Mi" del sidebar debe estar reescrito con las keywords del JD incorporadas naturalmente (3-4 líneas).
- Foto de perfil: `filter: brightness(1.12) contrast(1.05)` y `border: 3px solid rgba(255,255,255,0.65)`.
- El `.body` debe tener `min-height: 257mm` para que el CV ocupe la página completa.
- Subtítulo del header: reflejar el título exacto del rol (ej: "Software Engineer · Node.js · APIs · Cloud").

**Reglas ATS — OBLIGATORIAS:**
- Usar nombres de sección estándar: "Experiencia Laboral", "Educación", "Habilidades", "Certificaciones"
- Incluir las keywords exactas del JD en bullets y en habilidades (sin inventar)
- Los bullets comienzan con verbos de acción: Diseñé, Desarrollé, Implementé, Construí, Colaboré, Automaticé, etc.
- Las habilidades se organizan por categoría relevante para este rol (primero lo que pide el JD)
- El título del rol target debe aparecer en el subtítulo del header

**No inventés experiencia que Mateo no tiene.** Solo reorganizá, reencuadrá y resaltá lo relevante.

Generá el HTML del CV adaptado usando la misma estructura de `cv/cv_base_test.html` (tabla dos columnas, header oscuro, sidebar gris), guardalo en `cv/output/cv_[empresa_slug].html`, y luego ejecutá:
```
python cv/generate_pdf.py cv/output/cv_[empresa_slug].html cv/output/mateo_forrester_[empresa_slug].pdf
```

Informá la ruta del PDF generado al final.

---

## Output en pantalla

### Análisis de fit — [Rol] @ [Empresa]

| Categoría | Skill requerida | Mateo tiene | Match |
|---|---|---|---|
| Must-have | [skill] | ✅/⚡/❌ | Alto/Medio/Bajo |
| Must-have | [skill] | ✅/⚡/❌ | Alto/Medio/Bajo |
| Nice-to-have | [skill] | ✅/⚡/❌ | Alto/Medio/Bajo |

**Fit general estimado**: [⭐⭐⭐⭐⭐ / porcentaje]
**Recomendación**: [Una línea honesta sobre si vale la pena aplicar y con qué mensaje]

---

## Cover Letter — [idioma según la empresa]

*Corta, directa, 3 párrafos. Sin clichés. Que suene humana y estratégica.*

**Asunto sugerido**: [línea de asunto si es por email]

[Párrafo 1 — Por qué este rol y esta empresa específicamente. Mostrar que conocés la empresa.]

[Párrafo 2 — La experiencia más relevante de Mateo para lo que buscan. 1-2 logros concretos.]

[Párrafo 3 — Cierre. Disponible para conversar. Directo.]

---
Mateo Forrester
mateoforrester26@gmail.com | linkedin.com/in/mateoforrester
