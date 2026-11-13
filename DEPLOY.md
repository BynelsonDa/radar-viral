# Despliegue gratuito: Render Static Site + GitHub Actions

La configuración activa `render.yaml` crea **un solo sitio estático gratuito**.
No usa los servicios MySQL, web ni worker de pago de la propuesta anterior.
No se ha creado ningún recurso de pago durante la preparación.

## Activación

1. En GitHub abre el repositorio `BynelsonDa/radar-viral` → **Settings → Secrets
   and variables → Actions → New repository secret**. Guarda la clave real de
   Google con el nombre **YOUTUBE_API_KEY**. No la pegues en el chat ni la subas
   al repositorio. El secreto proxy de Codex no se copia automáticamente allí.
2. Los cambios deben estar en `main`: las tareas programadas de GitHub solo
   ejecutan workflows que existen en la rama principal. En **Actions → Actualizar
   datos de YouTube → Run workflow** puedes comprobar la primera recolección.
3. En Render elige **New → Blueprint**, conecta este repositorio y selecciona
   `main`. El archivo `render.yaml` define únicamente un servicio de runtime
   `static`, sin base de datos, disco ni plan de pago. Revisa el resumen antes
   de crear. Render debe tener permiso para leer el repositorio privado.
4. Render genera una URL HTTPS para `radar-viral`. Al terminar el primer build,
   abre esa URL. No necesitas una terminal ni instalar nada en tu computador.

También puedes crear **New → Static Site** con estos valores:

| Campo | Valor |
| --- | --- |
| Repository | BynelsonDa/radar-viral |
| Branch | main |
| Build command | python3 src/build_static_site.py |
| Publish directory | public |
| Auto deploy | On commit |

El nombre del dominio final lo asigna Render; no existe una URL de aplicación
hasta crear ese servicio. Para permitir que un agente lo cree mediante la API,
configura `RENDER_API_KEY` de forma segura en los ajustes de este entorno. No es
necesaria esa API key si lo creas desde el dashboard de Render.

## Cómo llegan los datos

Cada hora, aproximadamente al minuto 17, GitHub Actions ejecuta el recolector.
Consulta métricas de los videos guardados y, cada seis horas, descubre candidatos
nuevos. Guarda solo métricas públicas en `data/live.json` y hace un commit en
`main`. El despliegue automático de Render reconstruye el sitio al recibir ese
commit. La clave de API permanece en GitHub Actions y nunca llega al navegador.

El sitio comprueba los datos publicados cada minuto mientras esté visible. La
hora de captura se muestra en la pantalla. Si pasan más de tres horas sin una
captura nueva, se avisa de que está pendiente de actualización. Ante un error de
YouTube se conserva la captura anterior y falla la tarea, sin publicar datos
parciales. «Actualizar datos» recarga la captura disponible; no gasta cuota.

Esta opción tiene **datos periódicos, no instantáneos**. Las colas de GitHub,
el build de Render y los retrasos de YouTube pueden aumentar la demora. En
repositorios sin actividad, GitHub puede desactivar cron; revisa Actions si las
capturas dejan de actualizarse. No se promete disponibilidad continua ni un SLA.

## Cuotas gratuitas

El repositorio es privado: GitHub Actions usa la cuota de minutos incluida en el
plan de la cuenta, compartida con otros workflows. Una ejecución por hora supone
unas 720–744 ejecuciones al mes. Cada ejecución tiene un timeout de cinco minutos,
pero normalmente termina mucho antes. El consumo exacto debe verificarse en
**GitHub → Settings → Billing and licensing → Usage**. Mantén desactivado el
consumo de pago si necesitas un coste estrictamente cero; al agotar la cuota,
las actualizaciones se detendrán hasta recuperarla.

Render Static Sites no requiere un proceso de pago. Su almacenamiento, builds
y transferencia están sujetos a las cuotas gratuitas vigentes de la cuenta.
No cambies el servicio a Web Service ni añadas discos o workers de pago.

YouTube también aplica su propia cuota. Se limita el conjunto a 500 videos de
los últimos 60 días. La búsqueda usa hasta siete términos, cada seis horas;
los videos conocidos se consultan en lotes de 50 cada hora. Ajusta términos en
`.github/workflows/refresh-data.yml` si cambia el objetivo del radar.

Los datos publicados son estadísticas públicas de YouTube. No se publican el
repositorio, claves, credenciales de Render ni información privada del canal.

## Validación y build local

```bash
python3 -m pip install -r requirements-static.txt
python3 src/collect_static.py
python3 src/build_static_site.py
```

El build solo necesita la biblioteca estándar de Python y una captura existente.
No requiere MySQL ni la clave de YouTube. La web completa está en `public/`, que
se excluye de Git porque Render la genera. La captura `data/live.json` sí se
versiona para conservarla entre ejecuciones del recolector.

Las implementaciones opcionales de Flask/MySQL y de HTML portátil permanecen
para desarrollo; no forman parte de la configuración gratuita activa.
