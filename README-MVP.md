# Radar Viral — MVP YouTube

Recolector de candidatos a Shorts de hasta 180 segundos. **La duración no garantiza que un video sea un Short.** No se extraen métricas privadas de retención.

## Requisitos
Python 3.10+, MySQL 8+ y una clave de YouTube Data API v3.

## Instalación

1. Crea las tablas con `mysql -u root -p < sql/schema.sql`.
2. Crea un entorno virtual: `python -m venv .venv`.
3. Actívalo e instala `pip install -r requirements.txt`.
4. Copia `.env.example` a `.env` y configura API key y MySQL.
5. Ejecuta `python src/collector.py`.

## Próximos pasos
Añadir Docker Compose, pruebas, actualización eficiente de videos históricos, clasificación de nichos y dashboard. No publiques `.env` ni la clave de API. Las búsquedas consumen cuota y no cubren exhaustivamente todos los nichos.
