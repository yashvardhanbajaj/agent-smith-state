// Renders a built dashboard in jsdom with a fake db; prints JSON facts about the proposal cards.
const {JSDOM}=require('jsdom'); const fs=require('fs');
const html=fs.readFileSync(process.argv[2],'utf8'); const errors=[]; const adds=[];
const fakeDb={collection:()=>({get:async()=>({docs:[]}),add:async(p)=>{adds.push(p);return {id:'x'+adds.length};}})};
const dom=new JSDOM(html,{url:'https://desk.local/',runScripts:'dangerously',pretendToBeVisual:true,
  beforeParse(w){ w.onerror=(m)=>errors.push(String(m)); w.scrollTo=()=>{}; w.confirm=()=>true;
    w.claude={use:async(n)=>n==='db'?fakeDb:null}; }});
setTimeout(async()=>{
  const d=dom.window.document;
  const tab=[...d.querySelectorAll('.tab')].find(t=>/command|today|decide/i.test(t.textContent))||d.querySelector('.tab');
  if(tab) tab.click();
  await new Promise(r=>setTimeout(r,400));
  const cards=[...d.querySelectorAll('.pc')];
  const by=(re)=>cards.find(c=>re.test(c.querySelector('.pc-head').textContent));
  const t=by(/Buy AMAT/), l=by(/Buy KLAC/), s=by(/Trim ASML/);
  const keys=(c)=>c?[...c.querySelectorAll('.pc-ticket .k')].map(x=>x.textContent):null;
  const out={cards:cards.length,
    ticketKeys:keys(t), ticketText:t?t.querySelector('.pc-ticket').textContent.replace(/\s+/g,' '):null,
    sellKeys:keys(s), legacy:l?!!l.querySelector('.pc-legacy'):null, legacyHasTiles:l?!!l.querySelector('.pc-ticket'):null,
    hasVerdictTiles:t?!!t.querySelector('.pc-tiles'):false, decide:t?[...t.querySelectorAll('.decide button, .pc-decide button')].map(b=>b.dataset.decision):[],
    retireAll:!!d.querySelector('button.retire-all')};
  const one=l&&l.querySelector('button[data-decision="retire"]'); out.retireButtonOnLegacyCard=!!one; if(one){one.click(); await new Promise(r=>setTimeout(r,200));}
  out.retireWrites=adds.filter(a=>a.decision==='retire'&&a.surface==='proposal').length;
  out.errors=errors.filter(e=>!/scrollTo/.test(e));
  console.log(JSON.stringify(out)); process.exit(0);
},1000);
