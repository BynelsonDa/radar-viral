# Radar Viral — YouTube MVP

Recolector Python de candidatos a YouTube Shorts de hasta 180 segundos. **La duración por sí sola no garantiza que sean Shorts.** La API pública tampoco proporciona métricas de retención de videos de terceros.

## Ejecución con Docker

Requisitos: Docker Engine + Docker Compose v2, una clave de YouTube Data API v3.

1. Copia la configuración: `cp .env.example .env`.
2. Edita `.env`: escribe `YOUTUBE_API_KEY`, `DB_PASSWORD` y `MYSQL_ROOT_PASSWORD` (contraseñas diferentes y seguras).
3. Arranca MySQL: `docker compose up -d db`.
4. Ejecuta la recolección: `docker compose --profile collect run --rm collector`.
5. Para repetir la medición más tarde, ejecuta de nuevo el comando del paso 4. Los snapshots permiten comparar crecimiento entre momentos de recolección.
6. Para ejecutar las pruebas en un contenedor: `docker compose run --rm --no-deps collector python -m unittest discover -s tests -v` **no funciona con la imagen de producción**, porque los tests se excluyen del build. Ejecuta las pruebas en tu equipo o mediante GitHub Actions (siguiente sección).

Si solo quieres trabajar localmente sin Docker, crea MySQL con `mysql -u root -p < sql/schema.sql`, instala `pip install -r requirements.txt`, ajusta `DB_HOST=127.0.0.1` y ejecuta `python -m src.collector`.

## Tests

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

GitHub Actions ejecuta estas pruebas en cada PR hacia `main`.

## Seguridad y límites

- No subas `.env`; está en `.gitignore`.
- La base de datos usa un volumen persistente y **no expone puertos** al host.
- El esquema de MySQL se inicializa automáticamente solo la **primera vez** que se crea el volumen. Los cambios de esquema posteriores necesitan migraciones.
- Cada consulta `search.list` consume cuota. El buscador no cubre todo YouTube.
- El servicio `collector` se ejecuta manualmente por ahora; **no** existe una programación automática ni un despliegue cloud permanente.
- El dashboard, el análisis semántico y las pruebas de integración con YouTube y MySQL están pendientes.
