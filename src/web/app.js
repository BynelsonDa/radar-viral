const $ = id => document.getElementById(id);
const number = value => value == null ? '—' : new Intl.NumberFormat('es-CO', {notation: 'compact', maximumFractionDigits: 1}).format(value);
const dateTime = value => value ? new Intl.DateTimeFormat('es-CO', {dateStyle:'medium',timeStyle:'short',timeZone:'America/Bogota'}).format(new Date(value)) : 'Sin capturas';
const date = value => value ? new Intl.DateTimeFormat('es-CO', {dateStyle: 'medium', timeZone: 'America/Bogota'}).format(new Date(value)) : 'Sin fecha';
let page = 1, controller;
function element(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function card(video) {
  const article = element('article', 'video');
  const top = element('div', 'top');
  top.append(element('span', '', date(video.published_at)), element('span', 'duration', `${video.duration_seconds} s`));
  const title = element('h3', '');
  const link = element('a', '', video.title);
  link.href = `https://www.youtube.com/watch?v=${encodeURIComponent(video.video_id)}`;
  link.target = '_blank'; link.rel = 'noopener noreferrer';
  title.append(link);
  const stats = element('div', 'stats');
  for (const [label, value] of [['Vistas', video.view_count], ['Me gusta', video.like_count], ['Comentarios', video.comment_count]]) {
    const item = element('div', '');
    item.append(element('strong', '', number(value)), element('span', '', label));
    stats.append(item);
  }
  article.append(top, title, element('p', 'channel', video.channel_title || 'Canal sin nombre'), stats,
    element('p', 'growth', video.growth_per_hour == null ? 'Crecimiento: pendiente de otra medición' : `${number(video.growth_per_hour)} vistas/h entre las últimas mediciones`));
  return article;
}
const colors = ['#12dbdc','#2c8def','#f6c858','#7c74e9','#32ba9b','#56657e'];
function svgNode(tag, attrs, text) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}
function resetCharts(message) {
  for (const id of ['timeline','ranking','distribution','heatmap']) {
    $(id).replaceChildren(element('p', 'empty-chart', message));
  }
}
function renderCharts(charts, total) {
  resetCharts('Sin datos para estos filtros');
  if (!total || !charts) return;
  const points = charts.timeline.filter(row => row.day && row.day !== 'None');
  if (points.length) {
    const svg = svgNode('svg', {viewBox:'0 0 600 225', role:'img', 'aria-label':'Número de candidatos por fecha de publicación'});
    const max = Math.ceil(Math.max(...points.map(p => p.count), 1)/4)*4;
    for (let i=0; i<=4; i++) {
      const y = 185-i*40;
      svg.append(svgNode('line',{x1:35,x2:580,y1:y,y2:y,stroke:'#293d59','stroke-width':1}));
      svg.append(svgNode('text',{x:26,y:y+4,'text-anchor':'end'},String(Math.round(max*i/4))));
    }
    const start = Date.parse(points[0].day), end = Date.parse(points.at(-1).day);
    const coords = points.map(p => [start===end ? 305 : 40+(Date.parse(p.day)-start)/(end-start)*530,185-p.count/max*160]);
    const path = coords.map(([x,y],i) => `${i?'L':'M'}${x},${y}`).join(' ');
    svg.append(svgNode('path',{d:`${path} L${coords.at(-1)[0]},185 L${coords[0][0]},185 Z`,fill:'#14e3e518'}));
    svg.append(svgNode('path',{d:path,fill:'none',stroke:'#14e3e5','stroke-width':3,'stroke-linejoin':'round'}));
    points.forEach((point,i) => {
      const [cx,cy] = coords[i];
      const dot = svgNode('circle',{cx,cy,r:4,fill:'#14e3e5'});
      dot.append(svgNode('title',{},`${point.day}: ${point.count} candidatos`)); svg.append(dot);
    });
    for (const index of points.length===1 ? [0] : [0,points.length-1]) {
      svg.append(svgNode('text',{x:coords[index][0],y:213,'text-anchor':index===0?'start':'end'},date(points[index].day+'T12:00:00Z')));
    }
    $('timeline').replaceChildren(svg);
  }
  const maxViews = Math.max(...charts.top.map(v => v.view_count), 1);
  $('ranking').replaceChildren(...charts.top.map(video => {
    const row = element('div','rank-row');
    const label = element('span','rank-title',video.title); label.title = video.title;
    const track = element('div','bar-track'); const bar = element('div','bar');
    bar.style.width = `${video.view_count/maxViews*100}%`; track.append(bar);
    row.append(label,track,element('span','rank-value',number(video.view_count))); return row;
  }));
  const groups = [...charts.channels];
  const others = total-groups.reduce((sum,row) => sum+row.count,0);
  if (others>0) groups.push({name:'Otros canales',count:others});
  let offset = 0;
  const stops = groups.map((row,i) => {
    const from = offset; offset += row.count/total*100;
    return `${colors[i]} ${from}% ${offset}%`;
  });
  const donut = element('div','donut'); donut.style.background = `conic-gradient(${stops.join(',')})`;
  donut.setAttribute('role','img'); donut.setAttribute('aria-label','Distribución de candidatos por canal; detalles en la leyenda');
  const center = element('div','donut-center'); center.append(element('strong','',number(total)),element('span','','candidatos')); donut.append(center);
  const legend = element('div','channel-legend');
  groups.forEach((row,i) => {
    const item = element('div','legend-row'); const swatch = element('i',''); swatch.style.background=colors[i];
    item.append(swatch,element('span','',row.name),element('strong','',`${(row.count/total*100).toFixed(0)}%`)); legend.append(item);
  });
  $('distribution').replaceChildren(donut,legend);
  const grid = [];
  grid.push(element('span','axis','UTC'));
  for (const day of ['LUN','MAR','MIÉ','JUE','VIE','SÁB','DOM']) grid.push(element('span','axis',day));
  const maxHeat = Math.max(...charts.heatmap.map(row => row.count),1);
  for (let slot=0;slot<6;slot++) {
    grid.push(element('span','axis',`${String(slot*4).padStart(2,'0')}:00`));
    for (let weekday=0;weekday<7;weekday++) {
      const count = charts.heatmap.find(row => row.weekday===weekday && row.slot===slot)?.count || 0;
      const cell = element('div','cell');
      cell.style.background = count ? `rgba(20,227,229,${0.2+0.8*count/maxHeat})` : '#17263f';
      cell.title = `${['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][weekday]}, ${slot*4}:00–${slot*4+3}:59 UTC: ${count} videos`;
      cell.setAttribute('role','img'); cell.setAttribute('aria-label',cell.title); grid.push(cell);
    }
  }
  $('heatmap').replaceChildren(...grid);
}

let ideaRows=[], ideaAt=null, visibleIdeas=[];
function evidenceLink(source) {
  const link=element('a','evidence-link',source.title);
  link.href=`https://www.youtube.com/watch?v=${encodeURIComponent(source.id)}`;
  link.target='_blank';link.rel='noopener noreferrer';return link;
}
function briefText(idea) {
  return `${idea.name} — ${idea.confidence}\nIdea: ${idea.angle}\nGancho propuesto: ${idea.hook}\nGuion de 20–40 s (propuesto):\n${idea.steps.map((step,i)=>`${i+1}. ${step}`).join('\n')}\nEvidencia: ${idea.count} videos, ${idea.channels} canales, ${number(idea.medianDaily)} vistas/día (mediana histórica).\nPatrón observado: ${idea.observedHook}\nReferencias:\n${idea.sources.map(source=>`https://www.youtube.com/watch?v=${encodeURIComponent(source.id)}`).join('\n')}`;
}
function signalList(id,groups,isHook=false) {
  const nodes=groups.slice(0,5).map((group,index)=>{
    const item=element('article','signal');
    const head=element('div','signal-title');head.append(element('span','signal-index',String(index+1).padStart(2,'0')),element('strong','',group.name));
    item.append(head,element('p','signal-metric',isHook ? `${group.count} videos · ${group.share.toFixed(0)}% de la muestra` : `${number(group.medianDaily)} vistas/día · mediana`),
      element('p','caption',`${group.count} videos · ${group.channels} canales · ${number(group.views)} vistas acumuladas`));
    if(group.count<3)item.append(element('span','sample-tag','Muestra pequeña'));
    if(isHook)item.append(element('p','caption',`Ejemplo de estructura: «${group.sample}»`));
    const details=element('details','sources');details.append(element('summary','','Ver videos de referencia'));
    group.sources.forEach(source=>details.append(evidenceLink(source)));item.append(details);return item;
  });
  $(id).replaceChildren(...(nodes.length ? nodes : [element('p','empty-chart','No hay patrones suficientes con estos filtros.')]));
}
function renderIdeas(rows,at) {
  ideaRows=rows;ideaAt=at;
  const selected=$('ideas-niche').value;
  const analysis=RadarIdeas.analyze(rows,at);
  $('ideas-niche').replaceChildren(element('option','','Todos los nichos'));
  $('ideas-niche').firstChild.value='';
  for(const niche of analysis.niches) {
    const option=element('option','',niche.name);option.value=niche.name;$('ideas-niche').append(option);
  }
  if(analysis.niches.some(n=>n.name===selected))$('ideas-niche').value=selected;
  updateIdeaPanel();
}
function updateIdeaPanel() {
  const niche=$('ideas-niche').value;
  const rows=niche ? ideaRows.filter(v=>RadarIdeas.nicheFor(v.title)===niche) : ideaRows;
  const data=RadarIdeas.analyze(rows,ideaAt);
  const minimum=Number($('ideas-min').value);
  const keep=group=>group.count>=minimum;
  $('ideas-coverage').textContent=`${data.total} videos analizados · ${data.classified} clasificados por título · ${data.unclassified} sin clasificar. Se usan todos los resultados de tus filtros, no solo la página visible. Los nichos y temas son etiquetas aproximadas.`;
  signalList('niche-ranking',data.niches.filter(keep));
  signalList('hook-ranking',data.hooks.filter(keep),true);
  signalList('topic-ranking',data.topics.filter(keep));
  visibleIdeas=data.ideas.filter(keep).slice(0,6);
  $('download-ideas').disabled=!visibleIdeas.length;
  const cards=visibleIdeas.map((idea,index)=>{
    const article=element('article','idea-card');
    const head=element('div','section-title');head.append(element('span','eyebrow',`IDEA ${String(index+1).padStart(2,'0')}`),element('span','sample-tag',idea.confidence));
    article.append(head,element('h4','',idea.name),element('p','idea-angle',idea.angle));
    const hook=element('blockquote','',idea.hook);article.append(element('span','idea-label','GANCHO PROPUESTO'),hook,
      element('p','caption',`Patrón observado: ${idea.observedHook}`));
    const script=element('ol','idea-script');idea.steps.forEach(step=>script.append(element('li','',step)));
    article.append(element('span','idea-label','GUION PROPUESTO · 20–40 S'),script,
      element('p','idea-evidence',`${idea.count} videos · ${idea.channels} canales · ${number(idea.medianDaily)} vistas/día (mediana)`));
    const details=element('details','sources');details.append(element('summary','','Consultar evidencia'));
    idea.sources.forEach(source=>details.append(evidenceLink(source)));article.append(details);
    const copy=element('button','copy-idea','Copiar brief');
    copy.addEventListener('click',async()=>{
      try {await navigator.clipboard.writeText(briefText(idea));$('ideas-copy-status').textContent=`Brief de «${idea.name}» copiado.`;}
      catch {$('ideas-copy-status').textContent='No se pudo copiar. Usa Descargar ideas para guardar los briefs.';}
    });article.append(copy);return article;
  });
  $('idea-cards').replaceChildren(...(cards.length ? cards : [element('p','empty-chart','No hay ideas con suficiente evidencia para estos filtros. Amplía las fechas o reduce el mínimo de repeticiones.')]));
}
$('ideas-niche').addEventListener('change',updateIdeaPanel);
$('ideas-min').addEventListener('change',updateIdeaPanel);
$('download-ideas').addEventListener('click',()=>{
  const text=`Radar Viral · Ideas para próximos Shorts\nBasadas en títulos y métricas de la muestra; no garantizan viralidad.\n\n${visibleIdeas.map(briefText).join('\n\n---\n\n')}`;
  const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));
  const link=element('a','');link.href=url;link.download='ideas-para-proximos-shorts.txt';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});

async function load() {
  controller?.abort(); controller = new AbortController();
  $('status').className = ''; $('status').textContent = 'Consultando datos…';
  resetCharts('Consultando datos…');
  $('videos').replaceChildren(); $('prev').disabled = true; $('next').disabled = true;
  for (const id of ['total','views','channels']) $(id).textContent = '—';
  $('updated').textContent = 'Datos públicos de YouTube';
  $('ideas-coverage').textContent='Consultando ideas…';
  $('download-ideas').disabled=true;
  $('idea-cards').replaceChildren();
  for(const id of ['niche-ranking','hook-ranking','topic-ranking'])$(id).replaceChildren();
  const params = new URLSearchParams(new FormData($('filters'))); params.set('page', page);
  try {
    if (window.RADAR_LIVE_FILE) {
      const capture = await fetch(window.RADAR_LIVE_FILE, {signal: controller.signal, cache:'no-store'});
      if (!capture.ok) throw new Error('No se pudo cargar la captura de datos. Reintenta en unos momentos.');
      window.RADAR_SNAPSHOT = await capture.json();
    }
    const response = window.RADAR_SNAPSHOT
      ? {ok: true, json: async () => snapshotData(params)}
      : await fetch(`/api/videos?${params}`, {signal: controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudieron cargar los videos.');
    for (const id of ['total', 'views', 'channels']) $(id).textContent = number(data.summary[id]);
    $('videos').replaceChildren(...data.videos.map(card));
    renderCharts(data.charts, data.summary.total);
    renderIdeas(data.idea_videos || [],window.RADAR_SNAPSHOT?.exported_at || new Date().toISOString());
    if (window.RADAR_LIVE_FILE) liveStatus();
    $('status').textContent = data.videos.length ? `${data.summary.total} candidatos coinciden con tus filtros.` : 'No hay videos para estos filtros. Prueba otra búsqueda o ejecuta el recolector para incorporar datos.';
    $('page').textContent = `Página ${page}`;
    $('prev').disabled = page <= 1; $('next').disabled = page * data.page_size >= data.summary.total;
    $('updated').textContent = data.summary.updated ? `Última captura: ${dateTime(data.summary.updated)}` : 'Todavía no hay capturas';
  } catch (error) {
    if (error.name === 'AbortError') return;
    resetCharts('Datos no disponibles');
    ideaRows=[];visibleIdeas=[];
    $('ideas-coverage').textContent='No se pudieron calcular ideas. Reintenta cuando se recuperen los datos.';
    $('status').className = 'error'; $('status').textContent = error.message;
  }
}
$('filters').addEventListener('submit', event => {event.preventDefault(); page = 1; load();});
$('refresh').addEventListener('click', () => load());
$('prev').addEventListener('click', () => {page--; load();});
$('next').addEventListener('click', () => {page++; load();});
load();

async function liveStatus() {
  if (window.RADAR_LIVE_FILE) {
    const stamp=window.RADAR_SNAPSHOT?.exported_at;
    const stale=!stamp || Date.now()-Date.parse(stamp)>3*3600000;
    $('live-status').textContent = `${stale ? 'Captura pendiente de actualización' : 'Datos públicos actualizados periódicamente'} · programación cada hora · última captura: ${dateTime(stamp)}. GitHub y YouTube pueden demorar las actualizaciones.`;
    return;
  }
  if (window.RADAR_SNAPSHOT) {
    $('live-status').textContent = 'Copia portátil: sin actualización automática.';
    return;
  }
  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw new Error();
    const data = await response.json();
    const job = data.jobs.find(row => row.job==='refresh');
    if (!job) {
      $('live-status').textContent = 'Esperando el primer ciclo de actualización del recolector.';
    } else if (job.last_error) {
      $('live-status').textContent = `Actualización pausada: ${job.last_error} Última captura: ${dateTime(job.last_success_at)}.`;
    } else {
      const stale = !job.last_success_at || Date.now()-Date.parse(job.last_success_at)>job.interval_seconds*2000;
      $('live-status').textContent = `${stale ? 'Datos pendientes de actualización' : 'Actualización automática activa'} · cada ${Math.round(job.interval_seconds/60)} min · última captura: ${dateTime(job.last_success_at)}. YouTube puede demorar la publicación de sus métricas.`;
    }
  } catch {
    $('live-status').textContent = 'No se pudo comprobar la actualización automática.';
  }
}
liveStatus();
if (window.RADAR_LIVE_FILE || !window.RADAR_SNAPSHOT) {
  setInterval(() => {
    if (!document.hidden) { load(); liveStatus(); }
  },60000);
}
