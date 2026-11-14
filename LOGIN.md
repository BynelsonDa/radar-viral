# Radar Viral — inicio de sesión privado

Se añadió un **login de administrador** al servidor **Flask** con usuario
configurable, contraseña protegida con `scrypt`, sesión firmada y cookie
`HttpOnly`, `SameSite=Lax`; CSRF en inicio/cierre de sesión y un límite
básico de intentos fallidos. Sesión máxima de 12 horas.

## 1. Preparar el usuario Neutrinitoo

```bash
pip install -r requirements.txt
python src/create_admin.py --username neutrinitoo --generate-password
```

El comando muestra una contraseña aleatoria y estas variables para configurar
**únicamente en el entorno privado del servidor**:

- `AUTH_USERNAME=neutrinitoo`
- `AUTH_PASSWORD_HASH=...`
- `SESSION_SECRET=...`

Guarda la contraseña en un gestor de contraseñas. **Ninguna contraseña ni su hash
se comitea al repositorio.** Alternativamente, sin `--generate-password`,
el comando solicita una contraseña por consola dos veces. La cuenta queda
**preparada en código, pero NO se activa en el despliegue** hasta configurar
las variables de entorno.

Para entorno local, usa `.env` (ignorado por Git), configura las variables
generadas y ejecuta el servidor:

```bash
python src/dashboard.py --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000/login`.

## 2. Despliegue privado necesario

**ATENCIÓN: el servicio actual descrito en `render.yaml` es estático**,
y continúa siendo público. Poner un formulario HTML sobre un hosting estático
NO restringe las descargas ni `data/live.json`. El login se aplica **solo
al servidor Flask**, no al sitio estático ni a exportaciones HTML.

Para tener un dashboard privado en Internet, despliega el contenedor Flask
como un servicio web con una base MySQL disponible. Configura las tres
variables anteriores como secretos en el hosting, habilita HTTPS y
`AUTH_COOKIE_SECURE=1`. Asegura que los datos privados no estén publicados
en `public/` ni en repositorios públicos.

El dashboard Flask exige sesión para `/`, archivos JS/CSS y
`/api/videos`, `/api/status` y `/api/session`.
Solo `/login` y `/health` quedan públicos. Sin las tres variables,
el dashboard devuelve un error 503 **en vez de exponer datos**.

## 3. Pruebas

```bash
python -m unittest discover -s tests -p test_auth.py -v
```

El límite de intentos es local al proceso: para despliegues de alta
concurrencia usar Redis o un WAF con límites globales. Se recomienda
añadir recuperación de cuentas, auditoría de acceso y usuarios en una base
de datos si se requieren múltiples administradores.
