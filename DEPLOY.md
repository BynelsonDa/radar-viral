# Radar Viral en Render

La aplicación usa tres servicios en la misma región: una web pública, un recolector
privado y MySQL privado con disco persistente. `render.yaml` describe los tres.
El HTML portátil no se utiliza en este despliegue.

## Antes de crear recursos

La configuración selecciona **Standard** para MySQL (memoria suficiente para el
motor), **Starter** para la web y el worker, y un disco de 10 GB. Son recursos
**de pago**. Revisa el presupuesto que muestre Render antes de confirmar. No se
han creado recursos de Render automáticamente por guardar este archivo.

El repositorio debe estar accesible para la cuenta de Render y contener la rama
`codex/radar-live`. El proyecto usa Docker; no configures un sitio estático.

## Despliegue desde el dashboard

1. En Render abre **New → Blueprint** y conecta `BynelsonDa/radar-viral`.
2. Selecciona la rama `codex/radar-live` y el archivo `render.yaml`.
3. Revisa los servicios y el coste. Introduce `YOUTUBE_API_KEY` en el campo seguro
   del recolector al que Render solicitará valor. No subas la clave a Git.
4. Confirma el Blueprint. MySQL generará sus contraseñas y las compartirá solo con
   la web y el worker mediante referencias internas.
5. Espera a que los tres servicios estén activos. Abre la URL HTTPS que Render
   asigne a `radar-viral-web`. `/health` debe devolver `{"status":"ok"}`.
6. Verifica que `/api/status` muestre `last_success_at` para `refresh` y
   `discovery`, sin `last_error`, y que el panel muestre videos reales.

No copies valores de autenticación proxy de Codex en Render. La clave configurada
para las solicitudes de este entorno no se convierte automáticamente en una
credencial de la cuenta de alojamiento. Introduce la clave real exclusivamente
mediante la configuración segura de Render.

Para que un agente administre Render se necesita una API key de Render, guardada
en el secreto `RENDER_API_KEY` de los ajustes del entorno, con destino
`api.render.com`. No la pegues en el chat. Debe conocerse también el workspace
correcto y aprobarse el presupuesto antes de crear servicios facturables.

## Actualización y límites

- El worker actualiza hasta 500 videos guardados cada 15 minutos. Prioriza los
  que llevan más tiempo sin actualizarse; con más de 500, hacen falta varios
  ciclos para cubrirlos todos.
- Descubre candidatos nuevos cada 6 horas con hasta siete búsquedas. Configura
  `SEARCH_TERMS` en el worker, separados por punto y coma.
- El navegador consulta la base cada minuto mientras la pestaña esté visible.
  Abrir el panel o pulsar actualizar no dispara búsquedas de YouTube.
- Son datos periódicos, no un flujo instantáneo. YouTube puede retrasar métricas.
  CTR, ingresos y retención privada no están disponibles.
- Los intervalos mínimos son 5 minutos para métricas y 1 hora para búsquedas;
  acortarlos aumenta consumo de cuota. La configuración por defecto supone
  aproximadamente 2800 unidades/día para 7 búsquedas cada 6 h, más hasta unas
  960 consultas de estadísticas/día para 500 videos cada 15 min. El coste real
  depende de la cuota y las tarifas vigentes de YouTube y del volumen recopilado.
- Un bloqueo de MySQL evita ejecuciones simultáneas. Los tiempos de los trabajos
  se guardan en MySQL para no repetir búsquedas al reiniciar el worker.
- Ante errores se conserva la última captura y se muestra un aviso. El worker
  reintenta en el siguiente intervalo; no imprime URLs con la API key.

Las claves de API de Google restringidas a IP deben permitir la salida de Render.
La web no necesita una clave de YouTube. Solo el worker realiza consultas externas.

## Persistencia y operación

No elimines el disco de MySQL para redesplegar. Mantén copias con herramientas de
MySQL (por ejemplo `mysqldump`) fuera del disco; un snapshot del disco no reemplaza
un backup consistente de la base. Las métricas recopiladas en el entorno Codex
no se migran solas; el worker llena la base nueva con datos de YouTube.

`autoDeployTrigger` está desactivado: los commits no publican versiones sin una
acción de despliegue. Render termina HTTPS; Waitress sirve la app Flask interna.
La web es de solo lectura y muestra métricas públicas. No expongas MySQL a internet.

## Validación local

Con MySQL y `DB_*` configurados, ejecuta:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/database.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python src/worker.py --once
.venv/bin/python src/dashboard.py
```

Para ejecutar la actualización periódica de forma continua, usa otro proceso:

```bash
.venv/bin/python src/worker.py
```

Construye la imagen con `docker build -t radar-viral .`. En Codex, si el build
necesita la CA del proxy, añade
`--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt`. No se desactiva TLS.
