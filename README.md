# Radar Viral

Radar de candidatos a YouTube Shorts con métricas públicas, búsqueda, gráficos
y actualización automática de datos.

## Despliegue gratuito recomendado

El sitio usa **Render Static Sites** y un recolector programado **cada hora en
GitHub Actions**. Conserva los datos en `data/live.json`; no necesita base de datos
ni servidores de pago. Los datos son periódicos, no instantáneos.

Consulta [DEPLOY.md](DEPLOY.md) para activar el secreto de YouTube y el sitio en
Render, y revisar las cuotas gratuitas. El Blueprint `render.yaml` crea únicamente
un sitio estático gratuito. El código de la API key nunca se publica en la web.

```bash
python3 -m pip install -r requirements-static.txt
python3 src/collect_static.py
python3 src/build_static_site.py
```

El build produce la carpeta `public/`. Con una captura existente, solo necesita
Python estándar; la consulta a YouTube se realiza aparte en GitHub Actions.

## Desarrollo opcional con MySQL

La versión Flask/MySQL, el worker y el exportador HTML siguen disponibles para
uso local. Consulta [README-MVP.md](README-MVP.md). No se necesitan para el sitio
gratuito de Render.

## Ideas para próximos Shorts

La sección analiza todos los resultados de los filtros, independientemente de
la página visible. Incluye rankings de nichos y temas por mediana de vistas por
día desde publicación, y patrones de ganchos por frecuencia en títulos. Las
reglas de palabras clave están en `src/web/ideas.js`; no usa servicios de IA de
pago ni métricas privadas. Los títulos en español, inglés y portugués se
clasifican de forma aproximada y los que no coinciden quedan sin clasificar.

Cada brief ofrece un ángulo original, un gancho propuesto, una estructura de
20–40 segundos y referencias a los videos que sustentan el tema. Permite filtrar
por nicho, exigir al menos tres repeticiones, copiar un brief y descargar las
ideas como texto. La muestra se recalcula al cargar nuevas capturas.

La velocidad usada para ordenar es `vistas / max(1, días desde publicación)`,
no crecimiento entre capturas ni predicción de viralidad. Se presenta la
mediana del grupo, el número de videos y de canales. Menos de tres videos o
menos de dos canales se marca como muestra pequeña. Varias categorías de
hook pueden coincidir en un título; sus porcentajes no suman necesariamente
100%. Detectar un patrón en un título no demuestra su eficacia en audio ni su
retención. Los briefs son propuestas editoriales, no datos extraídos del video.

Pruebas del análisis (sin dependencias adicionales):

```bash
node --test tests/ideas.test.cjs
```
