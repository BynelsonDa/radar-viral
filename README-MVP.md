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
Añadir Docker Compose, actualización eficiente de videos históricos y clasificación de nichos. No publiques `.env` ni la clave de API. Las búsquedas consumen cuota y no cubren exhaustivamente todos los nichos.

## Dashboard local

Con MySQL iniciado y el esquema importado, ejecuta desde la raíz del proyecto:

```bash
.venv/bin/python src/dashboard.py
```

El servidor escucha en la interfaz local y el puerto 8000. Puedes cambiarlo con
`--port`. Usa las mismas variables `DB_*` del recolector y carga el `.env` de la
raíz. No requiere nuevas dependencias. En el entorno de desarrollo configurado,
`bash /workspace/radar-viral-setup/start-db.sh` inicia MySQL.

La pantalla permite buscar títulos o canales, filtrar por fecha de publicación,
ordenar por vistas, fecha o crecimiento y recorrer páginas de 24 videos. Las
métricas del resumen corresponden a los filtros activos. «Actualizar datos» vuelve
a consultar MySQL; no llama a YouTube ni consume cuota. Para incorporar videos,
ejecuta el recolector por separado:

```bash
MAX_SEARCHES_PER_RUN=1 MAX_RESULTS_PER_SEARCH=5 .venv/bin/python src/collector.py
```

El crecimiento por hora se calcula con las dos últimas capturas de cada video.
Sin dos capturas separadas en el tiempo aparece como pendiente. Representa el
promedio entre esas mediciones, no una predicción ni una clasificación de nichos.
Las métricas que YouTube no proporciona se muestran con «—».

La web usa Flask con Waitress y es de solo lectura. La clave de YouTube permanece
en el recolector; el dashboard solo lee MySQL. Para desplegar la web, el worker
y la base persistente consulta [DEPLOY.md](DEPLOY.md).

El panel de analítica incluye publicaciones por fecha, los cinco videos con más
vistas, distribución de candidatos por canal y frecuencia de publicación por
bloques de cuatro horas en UTC. Los gráficos usan todos los resultados de los
filtros, independientemente de la página visible. La distribución muestra los
cinco canales principales y agrupa el resto en «Otros canales». Estos datos no
miden interés de búsqueda ni recomiendan horarios; CTR e ingresos requieren
acceso privado al canal y no se incluyen.

### Versión portátil sin servidor

Para generar un HTML autónomo con una copia de los datos públicos actuales:

```bash
.venv/bin/python src/export_site.py /tmp/radar-viral.html
```

Descarga ese archivo y ábrelo con un navegador. Incluye estilos, gráficos y filtros
sin dependencias de red ni claves de API. Los filtros de fecha usan como referencia
la fecha de exportación. No incorpora nuevas capturas; vuelve a exportarlo para
actualizar su contenido. La versión conectada a MySQL continúa disponible con
`src/dashboard.py`.

### Pruebas de integración

Con la base de datos configurada y el esquema importado:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas de integración crean registros temporales con identificadores únicos
y los eliminan al terminar. Comprueban filtros, resumen, paginación, crecimiento
y búsqueda literal. Usa una base de desarrollo.

## Datos actualizados automáticamente

El proceso `python src/worker.py` actualiza métricas cada 15 minutos y descubre
candidatos cada 6 horas. El dashboard consulta MySQL cada minuto y muestra la
última actualización y los errores del recolector. Los intervalos, la cuota y
el despliegue completo en Render se describen en [DEPLOY.md](DEPLOY.md).
