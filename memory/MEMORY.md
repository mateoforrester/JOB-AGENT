# MEMORY — Mateo Forrester Job Hunt

*Este archivo es el historial vivo de la búsqueda. El agente lo lee al inicio de cada sesión y lo actualiza cuando aprende algo nuevo o cuando Mateo lo corrige.*

---

## Estado actual

**Fecha de inicio**: 2026-04-09
**Estado**: Búsqueda activa

### Última búsqueda
- Fecha: 2026-04-10
- Roles buscados: automation developer/engineer, BPM, integration, software developer/engineer, AI developer/engineer, java developer, backend developer
- Mercados: Argentina + LATAM + USA remoto
- Filtro de días: 4 días
- Vacantes encontradas: 9

### Postulaciones en curso
*(vacío — sin postulaciones aún)*

### Vacantes guardadas para revisar
*(vacío)*

---

## Aprendizajes y correcciones

### 2026-04-10 — búsqueda: fuente y roles
**Aprendido**: La búsqueda debe ser únicamente en LinkedIn.com. No usar otras fuentes (Indeed, Bumeran, Getro, etc.).
**Por qué importa**: Mateo quiere resultados concentrados en LinkedIn, que es donde postula.

### 2026-04-10 — búsqueda: filtro de tiempo
**Aprendido**: El filtro de días es OBLIGATORIO y lo especifica Mateo al llamar /search. No asumir ningún default. Si no lo especifica, preguntar antes de buscar.
**Por qué importa**: En la primera búsqueda se mostraron vacantes de hace meses sin respetar el filtro.

### 2026-04-10 — búsqueda: respetar fecha estrictamente
**Aprendido**: Solo mostrar vacantes publicadas dentro del rango de días pedido. Si dice "hace 1 mes" o "hace 3 semanas" y el filtro era 4 días → descartar. Si no se puede confirmar la fecha → descartar.
**Por qué importa**: Se mostraron vacantes viejas (Oowlish 3 años, Despegar 1 año, Huzzle 3 semanas) cuando el filtro era 4 días.

### 2026-04-10 — búsqueda: no mostrar posiciones QA
**Aprendido**: Mateo es desarrollador de software, no QA. No mostrar roles de QA / Testing / Quality Assurance / Automation QA aunque tengan la palabra "automation".
**Por qué importa**: Se incluyeron 4 posiciones QA en los resultados cuando el perfil de Mateo es desarrollo.

### 2026-04-10 — búsqueda: formato ideal confirmado ✓
**Aprendido**: La búsqueda que le gustó a Mateo tuvo estas características — replicar siempre:
- 20+ vacantes en el resultado final
- Empresas target (MeLi, PedidosYa, Ualá, Despegar) buscadas vía listings de backend-java/software-engineer, no con WebSearch genérico
- Múltiples listings fetcheados en paralelo: `backend-java-empleos`, `software-engineer-empleos`, `software-developer-empleos-provincia-de-buenos-aires`, `automation-developer-empleos`
- Filtro de fecha aplicado estrictamente — descartar sin mostrar lo que está fuera del rango
- QA/Testing excluido siempre
- Detalle completo para las top 14, tabla resumen para el resto
- Plan de acción al final separado en "hoy" vs "esta semana"
- Links de LinkedIn con `f_TPR` y `sortBy=DD` con los segundos exactos del filtro pedido
**Por qué importa**: Mateo lo confirmó explícitamente — "esa búsqueda me encantó, quiero resultados siempre así".

### 2026-04-10 — búsqueda: volumen de resultados
**Aprendido**: Devolver MUCHAS vacantes, no pocas. Hay que fetchear múltiples páginas de listings (java developer, backend developer, software engineer, automation engineer, software developer, integration engineer) y también las páginas de jobs de las empresas target directamente. No conformarse con 6-8 resultados.
**Por qué importa**: En la primera búsqueda de 5 días se devolvieron solo 6 vacantes cuando había docenas disponibles. Mateo quiere volumen.

### 2026-04-10 — búsqueda: empresas target — cómo buscarlas
**Aprendido**: Para Mercado Libre, Despegar y PedidosYa NO usar WebSearch genérico (devuelve perfiles). Buscarlas directamente en los listings de LinkedIn: `ar.linkedin.com/jobs/backend-java-empleos` y similares ya las muestran. También fetchear `linkedin.com/jobs/pedidosya-jobs-worldwide` y `linkedin.com/jobs/despegar-jobs-worldwide`.
**Por qué importa**: En la primera búsqueda las empresas target no aparecieron porque se buscó mal. Aparecieron recién cuando se fetcheó el listing de `backend-java-empleos`.

### 2026-04-10 — búsqueda: empresas target prioritarias
**Aprendido**: Siempre buscar primero en Mercado Libre, Despegar y PedidosYa antes de la búsqueda general. Si hay vacantes → mostrarlas al tope marcadas con 🏆.
**Por qué importa**: Son empresas tech argentinas de primer nivel, buen salario y cultura remota.

### 2026-04-10 — búsqueda: ubicación y orden
**Aprendido**: Siempre buscar con ubicación Buenos Aires, Argentina. Los links de LinkedIn deben usar `location=Buenos+Aires%2C+Argentina`, `f_TPR=r[segundos]` según los días pedidos, y `sortBy=DD` para ordenar por más recientes primero.
**Por qué importa**: LinkedIn tiene esos filtros nativos y son más precisos que buscar sin ubicación. Mateo los señaló explícitamente desde la UI.

### 2026-04-10 — formato: archivo de memoria
**Aprendido**: El archivo de estado/memoria del proyecto se llama MEMORY.md (antes job_hunt_state.md).
**Por qué importa**: Mateo prefiere ese nombre. Actualizar referencias en CLAUDE.md.
