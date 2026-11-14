# Neutrinitoo — auditoría y respuestas sugeridas

Primera integración de **Radar Viral** para el canal `@Neutrinitoo`. Funciona
junto al recolector existente, sin cambiar su esquema MySQL ni su dashboard.

## Qué hace ahora

- Descubre el ID real del canal con `channels.list(forHandle=...)`.
- Extrae estadísticas públicas y hasta 500 videos recientes de la lista de subidas.
- Calcula vistas y likes por 1.000 vistas, identifica *candidatos* a Shorts
  por duración de hasta 180 segundos y extrae palabras frecuentes de títulos.
- Recupera comentarios públicos de un video y genera **borradores locales**
  de respuestas con reglas transparentes.
- Permite publicar **una respuesta individual** solo tras autorización OAuth
  y un comando explícito de confirmación.

**Límites:** la Data API pública no entrega retención, fuentes de tráfico,
visualizaciones por hora ni el porcentaje que decidió quedarse. Las palabras
frecuentes de los títulos **no son tendencias verificadas ni volúmenes de
búsqueda**. Para detectar tendencias en el tiempo, hay que comparar capturas
persistidas y añadir un módulo de investigación de temas. La duración por sí sola
no permite confirmar que un video sea un Short.

## Configuración

Desde la raíz del repositorio:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Añade `YOUTUBE_API_KEY` a un archivo `.env` local (nunca a Git).
El proyecto ya utiliza esta variable.

```bash
python src/channel_lab.py audit --handle @Neutrinitoo --limit 100 > neutrinitoo.json
python src/channel_lab.py comments --video-id oi8RO1rG11s --limit 30 > comentarios.json
python -m unittest discover -s tests -p test_channel_lab.py -v
```

Los comentarios y las respuestas sugeridas se devuelven como JSON. **No se
publica absolutamente nada** al ejecutar `audit` o `comments`.

## Publicar una respuesta previamente aprobada

1. En Google Cloud, habilita YouTube Data API v3 y crea un cliente OAuth de
   tipo **aplicación de escritorio**.
2. Descarga el JSON OAuth a `client_secret.json` en el proyecto.
3. Instala dependencias adicionales: `pip install -r requirements-channel.txt`.
4. Autoriza la cuenta propietaria cuando el navegador lo solicite.
5. Ejecuta **solo cuando hayas revisado y aprobado el texto**:

```bash
python src/channel_lab.py publish --comment-id ID_DEL_COMENTARIO --text "Tu respuesta revisada" --confirm-publish
```

El token se guarda en `.youtube-token.json` local y **jamás debe subirse al
repositorio**. También se puede configurar `YOUTUBE_OAUTH_TOKEN_FILE` y
`YOUTUBE_OAUTH_CLIENT_FILE`. La cuenta OAuth debe controlar el canal configurado.

La automatización de publicación masiva, respuestas sin revisar y generación de
afirmaciones científicas sin fuentes queda fuera del alcance de esta fase.

## Siguiente iteración

Integrar panel de revisión de borradores; OAuth para YouTube Analytics
(retención y fuentes de tráfico); capturas históricas por Short; señales de
tendencia por crecimiento y por demanda externa, separando estimaciones de
mediciones reales. 
