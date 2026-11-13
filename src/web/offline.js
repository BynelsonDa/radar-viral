// Read-only filtering for a standalone export. No API key or network is needed.
function snapshotData(params) {
  const source = window.RADAR_SNAPSHOT;
  const query = (params.get('q') || '').trim().toLocaleLowerCase('es');
  const days = Number(params.get('days') || 0);
  const cutoff = Date.parse(source.exported_at) - days * 86400000;
  const rows = source.videos.filter(v =>
    (!query || `${v.title} ${v.channel_title || ''}`.toLocaleLowerCase('es').includes(query)) &&
    (!days || Date.parse(v.published_at) >= cutoff));
  const byDay = new Map(), byChannel = new Map(), bySlot = new Map();
  for (const row of rows) {
    const day = row.published_at?.slice(0,10);
    if (day) {
      byDay.set(day,(byDay.get(day)||0)+1);
      const date = new Date(row.published_at);
      const weekday = (date.getUTCDay()+6)%7, slot = Math.floor(date.getUTCHours()/4);
      const key = `${weekday}-${slot}`;
      const item = bySlot.get(key)||{weekday,slot,count:0}; item.count++; bySlot.set(key,item);
    }
    const channel = row.channel_title ?? 'Sin canal';
    byChannel.set(channel,(byChannel.get(channel)||0)+1);
  }
  const sort = params.get('sort');
  rows.sort((a,b) => {
    if (sort==='growth') return (b.growth_per_hour ?? -Infinity)-(a.growth_per_hour ?? -Infinity) || a.video_id.localeCompare(b.video_id);
    if (sort==='recent') return (Date.parse(b.published_at)||0)-(Date.parse(a.published_at)||0) || a.video_id.localeCompare(b.video_id);
    return b.view_count-a.view_count || a.video_id.localeCompare(b.video_id);
  });
  const page = Number(params.get('page')||1);
  return {
    summary:{total:rows.length,views:rows.reduce((n,v)=>n+v.view_count,0),channels:new Set(rows.map(v=>v.channel_title).filter(v=>v!=null)).size,updated:rows.map(v=>v.last_seen_at).filter(Boolean).sort().at(-1)||null},
    videos:rows.slice((page-1)*24,page*24),page,page_size:24,
    charts:{timeline:[...byDay].sort(([a],[b])=>a.localeCompare(b)).map(([day,count])=>({day,count})),
      top:[...rows].sort((a,b)=>b.view_count-a.view_count).slice(0,5),
      channels:[...byChannel].map(([name,count])=>({name,count})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name)).slice(0,5),
      heatmap:[...bySlot.values()]}
  };
}
