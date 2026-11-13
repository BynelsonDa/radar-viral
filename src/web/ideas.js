/* Title-based editorial signals. No private analytics or external AI service. */
(function(root) {
  const norm = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const niches = [
    ['IA y tecnología', /\b(ia|ai|inteligencia artificial|intelligence|chatgpt|gemini|tesla|tecnologia|technology|tech|mit)\b/],
    ['Gaming', /\b(gaming|gamer|games?|juegos?|jogos?|minecraft|fortnite|roblox|gta|skyrim|playstation|ps5|xbox|nintendo|console|rocketleague)\b/],
    ['Animales y naturaleza', /\b(animal\w*|animai\w*|bichos|gato|canguru|gallina|pez|oceano|megalodon|mosquito)\b/],
    ['Deporte y fútbol', /\b(futbol|football|soccer|haaland|neymar|messi|ronaldo|deporte\w*)\b/],
    ['Historias y misterio', /\b(terror|misterio\w*|mystery|historia\w*|prision|guerra\w*|murder\w*|crime|crimen)\b/],
    ['Comida y recetas', /\b(receta\w*|recipe\w*|cocina\w*|comida|cooking|food|fitness|nutricion)\b/],
    ['Creadores y entretenimiento', /\b(mrbeast|mrrelevante|retos?|challenge\w*|prank|comedy|humor|chavo)\b/],
    ['Curiosidades', /\b(curiosidad\w*|curiosidade\w*|datoscuriosos|sabiasque|ciencia|science|incrivel|interessante)\b/]
  ];
  // Specific terms take precedence over broad niche labels.
  const topics = [
    {name:'ChatGPT y Gemini',rx:/\b(chatgpt|gemini)\b/,angle:'Compara dos respuestas a una tarea cotidiana y explica qué revisar antes de usarlas.',hook:'¿Qué cambia cuando le pides la misma tarea a dos asistentes?',steps:['Plantea una tarea concreta.','Muestra dos resultados comparables.','Cierra con una diferencia verificable.']},
    {name:'IA frente a realidad',rx:/\b(real o ia|ia o real|artificial o realidad|realidad|realidade)\b/,angle:'Muestra dos ejemplos propios y explica una pista para distinguir contenido generado.',hook:'¿Cuál de estos ejemplos fue generado con IA?',steps:['Presenta los dos ejemplos.','Da una pista visual.','Revela el proceso usado.']},
    {name:'Inteligencia artificial',rx:/\b(ia|ai|inteligencia artificial|intelligence)\b/,angle:'Prueba una herramienta de IA con una tarea pequeña y enseña el resultado sin exagerarlo.',hook:'Probé una IA para resolver esta tarea: esto fue lo que pasó.',steps:['Muestra el problema.','Graba una prueba breve.','Resume un acierto y una limitación.']},
    {name:'Minecraft',rx:/\b(minecraft)\b/,angle:'Diseña un reto corto de construcción con una regla inesperada.',hook:'¿Puedes completar este reto de Minecraft con una sola regla?',steps:['Explica la regla.','Muestra el intento.','Revela el resultado.']},
    {name:'Fortnite',rx:/\b(fortnite\w*)\b/,angle:'Analiza una decisión de una partida propia y compara dos maneras de resolverla.',hook:'La misma situación en Fortnite, dos decisiones distintas.',steps:['Muestra la situación.','Compara dos jugadas.','Explica la diferencia.']},
    {name:'Consolas y setups',rx:/\b(console|consola\w*|ps5|xbox|nintendo|setup|gaming chair|playstation|play station)\b/,angle:'Compara dos configuraciones de juego con el mismo presupuesto o una misma tarea.',hook:'¿Qué cambia realmente entre estos dos setups?',steps:['Fija el criterio de comparación.','Enseña una diferencia visible.','Da una conclusión limitada a la prueba.']},
    {name:'Videojuegos y retos',rx:/\b(gaming|gamer|games?|juegos?|jogos?|roblox|gta|skyrim|rocketleague)\b/,angle:'Propón un reto de videojuego y explica una mecánica con material de tu partida.',hook:'Intenté resolver este reto de una forma distinta.',steps:['Plantea el reto.','Muestra el intento.','Explica la mecánica clave.']},
    {name:'Animales sorprendentes',rx:/\b(animal\w*|animai\w*|bichos|gato|canguru|gallina|pez|mosquito)\b/,angle:'Explica un comportamiento animal con una fuente comprobable y una ilustración propia.',hook:'¿Por qué este animal se comporta así?',steps:['Presenta el comportamiento.','Explica una causa documentada.','Cierra con una pregunta concreta.']},
    {name:'Océano y descubrimientos',rx:/\b(oceano|megalodon|profundezas)\b/,angle:'Explica un descubrimiento marino y separa lo comprobado de las hipótesis.',hook:'Esto es lo que sí sabemos sobre este misterio del océano.',steps:['Presenta el descubrimiento.','Muestra la evidencia.','Aclara qué sigue sin saberse.']},
    {name:'Fútbol y sus figuras',rx:/\b(haaland|neymar|messi|ronaldo|futbol|football|soccer)\b/,angle:'Compara una habilidad de dos futbolistas usando una métrica y un contexto claros.',hook:'Dos jugadores, una misma habilidad: ¿qué cambia?',steps:['Define la habilidad.','Muestra ejemplos comparables.','Explica el contexto de la comparación.']},
    {name:'MrBeast y grandes retos',rx:/\b(mrbeast)\b/,angle:'Diseña un reto original de bajo presupuesto con una regla simple y un desenlace visible.',hook:'Un reto, una regla y un solo intento.',steps:['Presenta la regla.','Muestra el intento sin anticipar el final.','Revela el desenlace.']},
    {name:'Historias y giros',rx:/\b(historia\w*|prision|terror|guerra\w*|murder\w*|crimen|misterio\w*)\b/,angle:'Cuenta una historia documentada en tres momentos sin presentar suposiciones como hechos.',hook:'Todo parecía normal hasta que apareció este detalle.',steps:['Ubica el contexto.','Introduce un giro documentado.','Resuelve la historia.']},
    {name:'Recetas y comida',rx:/\b(receta\w*|recipe\w*|cocina\w*|comida|food|cooking)\b/,angle:'Prueba una receta corta y muestra el resultado con cantidades reproducibles.',hook:'¿Funciona esta receta con tan pocos pasos?',steps:['Muestra ingredientes.','Graba el paso clave.','Enseña el resultado real.']},
    {name:'Curiosidades y ciencia',rx:/\b(curiosidad\w*|curiosidade\w*|datoscuriosos|sabiasque|ciencia|science|incrivel|interessante)\b/,angle:'Responde una pregunta cotidiana con una demostración o una fuente verificable.',hook:'¿Por qué pasa esto todos los días?',steps:['Formula la pregunta.','Presenta la explicación.','Conecta con un ejemplo cotidiano.']}
  ];
  const hooks = [
    {name:'Pregunta o explicación',rx:/[?¿]|^(como|por que|what|why|how|quem|quien|o que)\b/,sample:'¿Por qué ocurre esto?'},
    {name:'Advertencia o prohibición',rx:/\b(nunca|never|no hagas|nao faca|no debes|no deberias)\b/,sample:'Antes de intentarlo, mira este detalle.'},
    {name:'Comparación o contraste',rx:/\b(vs|versus|frente a|compared|apart|real o ia|ia o real|different|diferentes)\b/,sample:'La misma situación, dos resultados distintos.'},
    {name:'Error, sorpresa o extremo',rx:/\b(error|peor|worst|hated|increible|incrivel|perturbador|sorprend\w*|imortal)\b/,sample:'El detalle que cambia toda la historia.'},
    {name:'Lista numerada',rx:/\btop\s*\d+\b|^\d+\s+[a-z]/,sample:'Tres detalles que puedes comprobar.'},
    {name:'Reto o recompensa',rx:/\b(reto|challenge|first to|keeps? it|you keep|to win|ganar|premio)\b/,sample:'Un reto, una regla y un intento.'}
  ];
  const median = values => {
    const sorted=[...values].sort((a,b)=>a-b),mid=Math.floor(sorted.length/2);
    return sorted.length ? sorted.length%2 ? sorted[mid] : (sorted[mid-1]+sorted[mid])/2 : 0;
  };
  function hookMatches(title) {
    // Hashtags indicate discovery labels, not necessarily an opening phrase.
    const text=norm(title).replace(/#[\p{L}\p{N}_]+/gu,'').replace(/^[^a-z0-9¿]+/,'');
    return hooks.filter(h=>h.rx.test(text));
  }
  function summarize(name, rows, reference, extra={}) {
    const perDay=rows.map(v=>Math.max(0,Number(v.view_count)||0)/Math.max(1,(reference-Date.parse(v.published_at))/86400000));
    const sources=[...rows].sort((a,b)=>{
      const speed=v=>(Number(v.view_count)||0)/Math.max(1,(reference-Date.parse(v.published_at))/86400000);
      return speed(b)-speed(a);
    }).slice(0,3).map(v=>({id:v.video_id,title:v.title,views:Number(v.view_count)||0}));
    return {name,count:rows.length,channels:new Set(rows.map(v=>v.channel_title).filter(Boolean)).size,
      views:rows.reduce((n,v)=>n+(Number(v.view_count)||0),0),medianDaily:median(perDay),
      medianViews:median(rows.map(v=>Number(v.view_count)||0)),sources,...extra};
  }
  function analyze(videos, at) {
    const reference=Date.parse(at)||Date.now();
    const rows=[...new Map(videos.map(v=>[v.video_id,v])).values()].filter(v=>v.video_id && Number.isFinite(Date.parse(v.published_at)) && Date.parse(v.published_at)<=reference);
    const nicheRows=new Map(),topicRows=new Map(),hookRows=new Map();
    let classified=0;
    for(const row of rows) {
      const title=norm(row.title);
      const niche=niches.find(([,rx])=>rx.test(title));
      if(niche) {classified++;if(!nicheRows.has(niche[0]))nicheRows.set(niche[0],[]);nicheRows.get(niche[0]).push(row);}
      const topic=topics.find(t=>t.rx.test(title));
      if(topic) {if(!topicRows.has(topic.name))topicRows.set(topic.name,[]);topicRows.get(topic.name).push(row);}
      for(const hook of hookMatches(row.title)) {
        if(!hookRows.has(hook.name))hookRows.set(hook.name,[]);hookRows.get(hook.name).push(row);
      }
    }
    const rank=groups=>[...groups].map(([name,group])=>summarize(name,group,reference))
      .sort((a,b)=>b.medianDaily-a.medianDaily || b.count-a.count || a.name.localeCompare(b.name));
    const hookRanking=rank(hookRows).map(item=>({...item,share:rows.length ? item.count/rows.length*100 : 0,
      sample:hooks.find(h=>h.name===item.name).sample})).sort((a,b)=>b.count-a.count||b.medianDaily-a.medianDaily);
    const topicRanking=rank(topicRows);
    const ideas=topicRanking.map(group=>{
      const definition=topics.find(t=>t.name===group.name);
      const localHooks=hookRanking.filter(h=>hookRows.get(h.name).some(v=>topicRows.get(group.name).includes(v)));
      const localHook=localHooks.map(h=>({name:h.name,count:hookRows.get(h.name).filter(v=>topicRows.get(group.name).includes(v)).length})).sort((a,b)=>b.count-a.count)[0];
      return {...group,angle:definition.angle,hook:definition.hook,steps:definition.steps,
        observedHook:localHook ? `${localHook.name} · ${localHook.count} videos de este tema` : 'Sin patrón de gancho detectado en este tema',
        confidence:group.count>=3 && group.channels>=2 ? 'Muestra moderada' : 'Muestra pequeña'};
    });
    return {total:rows.length,classified,unclassified:rows.length-classified,niches:rank(nicheRows),topics:topicRanking,hooks:hookRanking,ideas};
  }
  root.RadarIdeas={analyze,nicheFor:title=>niches.find(([,rx])=>rx.test(norm(title)))?.[0] || null};
  if(typeof module!=='undefined' && module.exports)module.exports={analyze};
})(typeof globalThis!=='undefined' ? globalThis : this);
