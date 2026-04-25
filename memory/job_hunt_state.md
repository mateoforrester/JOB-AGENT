# Job Hunt State — Mateo Forrester

*Este archivo es el historial vivo de la búsqueda. El agente lo lee al inicio de cada sesión y lo actualiza cuando aprende algo nuevo o cuando Mateo lo corrige.*

---

## Estado actual

**Fecha de inicio**: 2026-04-09
**Estado**: Búsqueda activa iniciada

### Última búsqueda
- Fecha: —
- Roles buscados: —
- Mercados: —
- Vacantes encontradas: —
- Vacantes de interés: —

### Postulaciones en curso
*(vacío — sin postulaciones aún)*

### Vacantes guardadas para revisar
*(vacío)*

---

## Aprendizajes y correcciones

*Cada vez que Mateo corrija algo o el agente aprenda una preferencia nueva, se registra aquí.*

### Formato
```
## [YYYY-MM-DD] — [categoría: búsqueda / formato / preferencia / postulación]
**Aprendido**: [qué se aprendió]
**Por qué importa**: [contexto]
```

## 2026-04-11 — flujo de búsqueda
**Aprendido**: Después de cada búsqueda, preguntar a Mateo cuáles vacantes quiere guardar. Las que confirme se agregan a "Vacantes guardadas". En búsquedas futuras, no volver a traer vacantes que ya estén en esa lista (deduplicar por URL o nombre+empresa).
**Por qué importa**: Evita mostrar resultados repetidos y permite llevar un historial real de lo que ya se vio.

## 2026-04-15 — método de búsqueda
**Aprendido**: Usar siempre WebFetch directo a URLs de LinkedIn Jobs con filtros `f_TPR` y `sortBy=DD`, NO WebSearch con `site:linkedin.com`. Hacer múltiples fetches en paralelo por rol (backend developer, software engineer, java developer, automation developer, automation engineer, integration developer, integration engineer, AI developer, process automation, RPA developer, middleware developer, API developer, fullstack developer) + páginas adicionales con `&start=25`. Luego fetchear detalles de las más prometedoras en paralelo.
**Por qué importa**: WebSearch devuelve perfiles de personas y resultados limitados. WebFetch directo a LinkedIn Jobs trae las vacantes reales con fecha, empresa y URL — igual a lo que ve el usuario en el sitio.

---

*Archivo inicializado el 2026-04-09. Primer uso del agente.*
