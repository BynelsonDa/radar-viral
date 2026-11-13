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
