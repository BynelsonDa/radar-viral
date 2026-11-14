/* Neutrinitoo-specific audit from an actual YouTube Data API snapshot. */
(function () {
  const el = id => document.getElementById(id);
  const fmt = n => n == null ? '—' : new Intl.NumberFormat('es-CO').format(n);
  const safe = (tag, cls, value) => {
    const node = document.createElement(tag);
    node.className = cls || '';
    if (value != null) node.textContent = String(value);
    return node;
  };
  async function render() {
    const target = el('channel-content');
    if (!target) return;
    try {
      const response = await fetch('/data/channel.json', {cache: 'no-store'});
      if (!response.ok) throw new Error('No se pudo obtener la captura del canal.');
      const data = await response.json();
      if (!data.channel) {
        target.textContent = 'La primera auditoría está pendiente. Ejecuta «Actualizar datos de YouTube» en GitHub Actions con YOUTUBE_API_KEY configurada.';
        return;
      }
      const stats = safe('div', 'channel-stats');
      for (const [label, value] of [
        ['Suscriptores', data.channel.subscribers],
        ['Visualizaciones del canal', data.channel.views],
        ['Videos públicos', data.channel.video_count]
      ]) {
        const metric = safe('article', 'channel-stat');
        metric.append(safe('span', 'caption', label), safe('strong', '', fmt(value)));
        stats.append(metric);
      }
      const heading = safe('p', 'caption', 'Última captura: '+new Date(data.exported_at).toLocaleString('es-CO')+' · API oficial de YouTube');
      const videos = safe('div', 'channel-list');
      const ordered = [...data.videos].sort((a,b) => b.views - a.views);
      ordered.slice(0,12).forEach((video,i) => {
        const row = safe('article', 'channel-video');
        const title = safe('a', '', (i+1)+'. '+video.title);
        title.href = 'https://www.youtube.com/watch?v='+encodeURIComponent(video.id);
        title.target = '_blank'; title.rel='noopener noreferrer';
        row.append(title, safe('span', 'caption', fmt(video.views)+' vistas · '+fmt(video.likes)+' me gusta'));
        videos.append(row);
      });
      target.replaceChildren(stats,heading,videos,
        safe('p','caption','La duración ≤180 segundos indica candidatos a Shorts, no confirma su clasificación. Retención y fuentes de tráfico requieren YouTube Analytics.'));
    } catch (error) { target.textContent = error.message; }
  }
  function init() {
    const refresh = el('channel-reload');
    if (refresh) refresh.addEventListener('click',render);
    render();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();
