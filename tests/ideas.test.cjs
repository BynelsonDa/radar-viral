const test=require('node:test');
const assert=require('node:assert/strict');
const {analyze}=require('../src/web/ideas.js');
const at='2026-11-13T12:00:00Z';
const video=(id,title,views=1000,channel='Channel',published='2026-11-03T12:00:00Z')=>({video_id:id,title,view_count:views,channel_title:channel,published_at:published});

test('niche and topic rankings use median daily views rather than total views',()=>{
 const rows=[video('a','ChatGPT',1000),video('b','Gemini',2000),video('c','IA',100000),video('d','Minecraft',10000)];
 const result=analyze(rows,at);
 assert.equal(result.niches[0].name,'Gaming');
 assert.equal(result.niches.find(n=>n.name==='IA y tecnología').medianDaily,200);
 assert.equal(result.classified,4);
});
test('hook frequency comes from titles and excludes hashtag-only patterns',()=>{
 const result=analyze([video('a','¿Cómo funciona la IA?'),video('b','What is Minecraft?'),video('c','Mira este video #never #top5'),video('d','Nunca hagas esto en Minecraft')],at);
 assert.equal(result.hooks[0].name,'Pregunta o explicación');
 assert.equal(result.hooks[0].count,2);
 assert.equal(result.hooks[0].share,50);
 assert.equal(result.hooks.find(h=>h.name==='Advertencia o prohibición').count,1);
 assert.ok(!result.hooks.some(h=>h.name==='Lista numerada'));
});
test('one video can have several hook patterns without double counting the sample',()=>{
 const result=analyze([video('a','¿Cuál es el PEOR error en Minecraft?')],at);
 assert.equal(result.total,1);
 assert.equal(result.hooks.length,2);
 assert.equal(result.ideas[0].confidence,'Muestra pequeña');
});
test('unclassified titles do not get invented niches or topics',()=>{
 const result=analyze([video('a','Un momento tranquilo')],at);
 assert.equal(result.unclassified,1);
 assert.deepEqual(result.niches,[]);assert.deepEqual(result.ideas,[]);
});
test('briefs keep matching evidence and flag stronger sample support',()=>{
 const rows=[video('a','Minecraft',100,'A'),video('b','Minecraft reto',200,'B'),video('c','Minecraft game',300,'A'),video('d','IA',999999,'C')];
 const idea=analyze(rows,at).ideas.find(i=>i.name==='Minecraft');
 assert.equal(idea.count,3);assert.equal(idea.channels,2);assert.equal(idea.confidence,'Muestra moderada');
 assert.ok(idea.sources.every(s=>s.id!=='d'));assert.equal(idea.steps.length,3);assert.ok(idea.hook);
});
test('future dates, duplicate ids and zero-age spikes do not inflate the sample',()=>{
 const row=video('a','Minecraft',1000,'A',at);
 const result=analyze([row,row,video('future','IA',99999,'B','2026-12-01T00:00:00Z')],at);
 assert.equal(result.total,1);assert.equal(result.niches[0].medianDaily,1000);
});
test('empty samples return no recommendations',()=>{
 const result=analyze([],at);assert.equal(result.total,0);assert.deepEqual(result.ideas,[]);
});
