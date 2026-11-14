# Solución de despliegue: login en Render

## Por qué no aparecía el login

El servicio original definido en `render.yaml` es un **Static Site**.
No ejecuta el backend Flask y por lo tanto jamás muestra `/login`.
La versión que necesita autenticación se encuentra en
`src/private_server.py` y lee la captura existente `data/live.json`,
sin requerir MySQL.

## Activar la versión privada en Render

1. En Render: **New > Web Service**. Conecta el repositorio
   `BynelsonDa/radar-viral`, rama `main`.
2. Selecciona plan **Free**, si está disponible.
3. Configura:
   - **Build Command:** `pip install -r requirements-private.txt`
   - **Start Command:** `gunicorn --chdir src private_server:app --bind 0.0.0.0:$PORT --workers 1`
   - **Health Check Path:** `/health`
4. Prepara el administrador **localmente**, sin subir credenciales:
   ```bash
   python -m pip install -r requirements-private.txt
   python src/create_admin.py --username neutrinitoo --generate-password
   ```
   Guarda la contraseña que sale en consola en tu gestor de contraseñas.
5. En Render > tu **Web Service** > Environment añade:
   - `AUTH_USERNAME` = `neutrinitoo`
   - `AUTH_PASSWORD_HASH` = valor generado, completo
   - `SESSION_SECRET` = valor generado
   - `AUTH_COOKIE_SECURE` = `1`
6. Haz deploy y abre **la URL del nuevo Web Service** con la ruta `/login`.
   El antiguo Static Site seguirá público y no mostrará el login.

También existe `render-private.yaml` para crear un Blueprint de Web
Service independiente, con la contraseña configurada durante el proceso.

## Prueba local

Crear `.env` con las variables privadas y `AUTH_COOKIE_SECURE=0`
solo para pruebas HTTP locales. Ejecutar:
```bash
python src/private_server.py
```
Visitar `http://localhost:8000/login`.

## Qué está protegido

En el Web Service privado se requiere autenticación para HTML, recursos
JS/CSS, `/data/live.json` y `/api/session`; `/health` queda público.
La captura pertenece a la rama pública del repositorio y al sitio estático
previo: **no contiene ni debe contener datos privados de YouTube**.
Este login no vuelve confidenciales los archivos ya públicos en GitHub.
Si se agregan métricas privadas por OAuth habrá que guardarlas fuera del
repositorio y del Static Site.

El servidor **no se publica automáticamente** solo por añadir estos
archivos: hay que crear el nuevo Web Service y configurar los secretos.

Los web services gratis de Render pueden suspenderse por inactividad.
