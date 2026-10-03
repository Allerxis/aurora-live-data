export type AuroraWidgetKind =
  | 'status'
  | 'comparison'
  | 'validation'
  | 'migration';

const BASE_WIDGET = String.raw`<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<style>
:root{
  color-scheme:light;
  --aurora-navy:#102a78;
  --aurora-navy-2:#16368f;
  --aurora-paper:#fbfaf7;
  --aurora-white:#ffffff;
  --aurora-ink:#1a2033;
  --aurora-muted:#69728f;
  --aurora-line:#d9dce6;
  --aurora-line-strong:#c8ccda;
  --aurora-cyan:#37c6d4;
  --aurora-purple:#5c2b91;
  --good:#087760;
  --warn:#8a5a00;
  --bad:#a52c3e;
}
*{box-sizing:border-box}
html,body{
  margin:0;padding:0;background:transparent;color:var(--aurora-ink);
  font:14px/1.65 "Avenir Next","Century Gothic",Avenir,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
body{padding:8px}
button{font:inherit}
.shell{
  background:var(--aurora-white);
  border:1px solid var(--aurora-line-strong);
  border-radius:3px;
  box-shadow:none;
  overflow:hidden;
}
.header{
  display:block;
  padding:0;
  color:var(--aurora-ink);
  background:var(--aurora-white);
  border-bottom:1px solid var(--aurora-line);
}
.brandbar{
  display:flex;
  align-items:center;
  min-height:50px;
  padding:10px 18px;
  background:var(--aurora-navy);
}
.brand-lockup{
  display:flex;
  align-items:baseline;
  gap:9px;
  color:#fff;
  white-space:nowrap;
}
.brand-name{
  display:inline-flex;
  align-items:center;
  gap:7px;
  font-size:21px;
  line-height:1;
  font-weight:700;
  letter-spacing:-.04em;
}
.brand-name svg{width:17px;height:17px;display:block;flex:none}
.brand-by{
  font-size:9px;
  line-height:1;
  font-weight:500;
  opacity:.76;
  letter-spacing:.01em;
}
.header-main{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:20px;
  padding:18px 20px 17px;
  background:var(--aurora-paper);
}
.header-copy{min-width:0}
.header-side{display:flex;align-items:center;padding-top:3px;flex:none}
h1{
  margin:0 0 5px;
  color:var(--aurora-navy);
  font-size:22px;
  line-height:1.14;
  letter-spacing:-.035em;
  font-weight:700
}
h2{color:var(--aurora-navy)}
.sub{margin:0;color:var(--aurora-muted);font-size:12px;max-width:620px}
.body{padding:18px 20px 20px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 22px}
.grid.three{grid-template-columns:repeat(3,minmax(0,1fr));gap:0 22px}
.card{
  position:relative;
  min-width:0;
  padding:13px 0 14px;
  border:0;
  border-bottom:1px solid var(--aurora-line);
  background:transparent;
  border-radius:0
}
.card strong{display:block;font-size:13px;margin-bottom:4px;color:var(--aurora-navy)}
.value{
  font-size:23px;
  line-height:1.2;
  font-weight:700;
  letter-spacing:-.035em;
  color:var(--aurora-navy)
}
.muted{color:var(--aurora-muted)}
.small{font-size:12px}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.stack{display:flex;flex-direction:column;gap:14px}
.badge{
  display:inline-flex;
  align-items:center;
  gap:7px;
  border:0;
  border-radius:0;
  padding:0;
  background:transparent;
  font-size:10px;
  font-weight:700;
  letter-spacing:.055em;
  text-transform:uppercase;
  white-space:nowrap
}
.badge.good{color:var(--good)}
.badge.warn{color:var(--warn)}
.badge.bad{color:var(--bad)}
.badge.info{color:var(--aurora-navy)}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor;flex:none}
.btn{
  appearance:none;
  border:1px solid var(--aurora-navy);
  background:transparent;
  color:var(--aurora-navy);
  border-radius:2px;
  padding:8px 12px;
  cursor:pointer;
  font-weight:700;
  transition:background .14s ease,color .14s ease,transform .14s ease
}
.btn:hover{background:#f1f3f8}
.btn.primary{background:var(--aurora-navy);border-color:var(--aurora-navy);color:#fff}
.btn.primary:hover{background:var(--aurora-navy-2)}
.btn.ghost{background:transparent}
.btn:active{transform:translateY(1px)}
.btn:focus-visible{outline:2px solid var(--aurora-cyan);outline-offset:3px}
.metric{
  display:flex;justify-content:space-between;gap:14px;
  padding:8px 0;border-bottom:1px solid var(--aurora-line)
}
.metric:last-child{border-bottom:none}
.metric span:first-child{color:var(--aurora-muted)}
.metric span:last-child{color:var(--aurora-navy);font-weight:650;text-align:right}
.chips{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:9px}
.chip{
  padding:1px 0 1px 8px;
  border-radius:0;
  background:transparent;
  border:0;
  border-left:2px solid var(--aurora-line-strong);
  color:#33405f;
  font-size:10px
}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-top:11px;margin-bottom:2px}
.criteria{display:flex;flex-direction:column;gap:0;border-top:1px solid var(--aurora-line)}
.criterion{
  border:0;border-bottom:1px solid var(--aurora-line);border-radius:0;
  padding:11px 0;background:transparent
}
.criterion .title{font-weight:700;color:var(--aurora-navy)}
.criterion .note{margin-top:5px;color:var(--aurora-muted);font-size:12px}
.model-card{display:flex;flex-direction:column;gap:8px;padding:14px 0 15px}
.model-card h2{font-size:16px;margin:0;word-break:break-word;color:var(--aurora-navy);letter-spacing:-.015em}
.provider{color:var(--aurora-muted);font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:700}
.details{display:none;padding:7px 0 2px}
.details.open{display:block}
.callout{
  border-left:2px solid var(--aurora-cyan);
  padding:10px 12px;
  background:#f4f8f7;
  border-radius:0
}
.callout.warn{border-left-color:#c18a24;background:#fff9ea}
.callout.bad{border-left-color:var(--bad);background:#fff4f5}
.service-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  border-top:1px solid var(--aurora-line);
  border-bottom:1px solid var(--aurora-line);
}
.service{
  padding:10px 10px 10px 0;
  border-right:1px solid var(--aurora-line);
  min-width:0;
}
.service:last-child{border-right:0}
.service-name{display:block;color:var(--aurora-muted);font-size:10px}
.service-state{display:block;color:var(--aurora-navy);font-size:12px;font-weight:700;margin-top:2px}
.empty{padding:24px 4px;text-align:center;color:var(--aurora-muted)}
.footer{
  padding:10px 20px;
  border-top:1px solid var(--aurora-line);
  display:flex;justify-content:space-between;align-items:center;gap:10px;
  color:var(--aurora-muted);font-size:10px;
  background:var(--aurora-paper)
}
@media (max-width:640px){
  body{padding:5px}
  .grid,.grid.three{grid-template-columns:1fr}
  .brandbar{padding:10px 14px}
  .header-main{padding:15px 14px;gap:12px}
  .body{padding:14px}
  .brand-name{font-size:19px}
  .brand-by{display:none}
  h1{font-size:19px}
  .header-side{max-width:40%}
  .service-grid{grid-template-columns:1fr 1fr}
  .service:nth-child(2){border-right:0}
  .service:nth-child(-n+2){border-bottom:1px solid var(--aurora-line)}
  .footer{padding:10px 14px;align-items:flex-start;flex-direction:column}
}
@media (prefers-reduced-motion:reduce){
  *{scroll-behavior:auto!important;transition:none!important}
}
</style>
</head>
<body>
<div id="root" class="shell"><div class="empty">Chargement de l’interface Aurora…</div></div>
<script>
(function(){
  const KIND="__KIND__";
  const root=document.getElementById("root");
  const pending=new Map();
  let nextId=1;
  let latest=null;
  let initialized=false;

  function post(message){ window.parent.postMessage(message,"*"); }
  function request(method,params){
    const id=nextId++;
    post({jsonrpc:"2.0",id:id,method:method,params:params});
    return new Promise(function(resolve,reject){ pending.set(id,{resolve:resolve,reject:reject}); });
  }
  function notify(method,params){ post({jsonrpc:"2.0",method:method,params:params||{}}); }
  function escapeText(v){ return v===null||v===undefined ? "—" : String(v); }
  function num(v){
    if(typeof v!=="number") return "—";
    return new Intl.NumberFormat(document.documentElement.lang||"fr-FR",{notation:v>=1000000?"compact":"standard",maximumFractionDigits:1}).format(v);
  }
  function money(v){
    if(typeof v!=="number") return "—";
    return new Intl.NumberFormat(document.documentElement.lang||"fr-FR",{style:"currency",currency:"USD",maximumFractionDigits:2}).format(v);
  }
  function badge(label,tone){
    const el=document.createElement("span");
    el.className="badge "+(tone||"info");
    const dot=document.createElement("span"); dot.className="dot";
    const txt=document.createElement("span"); txt.textContent=label;
    el.append(dot,txt); return el;
  }
  function brandLockup(){
    const wrap=div("brand-lockup");
    const name=document.createElement("span"); name.className="brand-name";
    const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("viewBox","0 0 24 24");
    svg.setAttribute("aria-hidden","true");
    svg.innerHTML='<path fill="currentColor" d="M12 2 22 22h-4.7l-2-4.2H8.7L6.7 22H2L12 2Zm0 8-1.9 4.1h3.8L12 10Z"/><path fill="#53d8e2" d="M4.8 17.7h14.4l1.1 2.3H3.7l1.1-2.3Z"/>';
    const word=document.createElement("span"); word.textContent="Aurora";
    name.append(svg,word);
    const by=document.createElement("span"); by.className="brand-by"; by.textContent="By Alexis Le Corre";
    wrap.append(name,by);
    return wrap;
  }
  function div(cls){ const el=document.createElement("div"); if(cls)el.className=cls; return el; }
  function p(text,cls){ const el=document.createElement("p"); if(cls)el.className=cls; el.textContent=text; return el; }
  function button(label,cls,fn){
    const b=document.createElement("button"); b.type="button"; b.className="btn "+(cls||""); b.textContent=label; b.addEventListener("click",fn); return b;
  }
  function header(title,subtitle,badgeNode){
    const h=div("header");
    const brandbar=div("brandbar");
    brandbar.append(brandLockup());
    const main=div("header-main");
    const left=div("header-copy");
    const t=document.createElement("h1"); t.textContent=title;
    left.append(t,p(subtitle||"","sub"));
    main.append(left);
    if(badgeNode){ const side=div("header-side"); side.append(badgeNode); main.append(side); }
    h.append(brandbar,main);
    return h;
  }
  function footer(text){
    const f=div("footer");
    const a=document.createElement("span"); a.textContent=text||"Aurora Live Data";
    const b=document.createElement("span"); b.textContent="Aurora · Lecture seule";
    f.append(a,b); return f;
  }
  function parseToolResult(result){
    if(!result) return null;
    if(result.structuredContent) return result.structuredContent;
    const blocks=result.content;
    if(Array.isArray(blocks)){
      const textBlock=blocks.find(function(x){return x&&x.type==="text"&&typeof x.text==="string";});
      if(textBlock){ try{return JSON.parse(textBlock.text);}catch(e){} }
    }
    return result;
  }
  async function sendMessage(text){
    try{
      await request("ui/update-model-context",{structuredContent:{aurora_ui_action:text}});
      await request("ui/message",{role:"user",content:[{type:"text",text:text}]});
    }catch(e){
      if(window.openai&&window.openai.sendFollowUpMessage){
        try{ await window.openai.sendFollowUpMessage({prompt:text}); }catch(_e){}
      }
    }
  }
  function applyContext(ctx){
    if(!ctx) return;
    if(ctx.theme) document.documentElement.dataset.theme=ctx.theme;
    if(ctx.locale) document.documentElement.lang=ctx.locale;
  }

  function renderStatus(data){
    root.replaceChildren();
    const healthy=data&&data.healthy===true;
    root.append(header("Aurora Live Data","État du registre et des contrôles actuellement vérifiés.",badge(healthy?"Opérationnel":"Dégradé",healthy?"good":"bad")));
    const body=div("body stack");
    const grid=div("grid three");
    [
      ["Sources fraîches",escapeText(data.sources_fresh)+" / "+escapeText(data.sources_total)],
      ["Modèles vérifiés",num(data.semantic_models_verified)],
      ["Guidance vérifiée",num(data.guidance_verified)],
      ["Benchmark",String(data.benchmark_suite_gate||"—").toUpperCase()],
      ["Golden Suite",String(data.golden_suite_gate||"—").toUpperCase()],
      ["Runtime",data.runtime_acceptance_ready?"READY":"—"]
    ].forEach(function(item){
      const c=div("card"); c.append(p(item[0],"small muted")); const v=div("value"); v.textContent=item[1]; c.append(v); grid.append(c);
    });
    body.append(grid);
    const services=div("service-grid");
    [
      ["Traçabilité",data.traceability_ready],
      ["Comparaison",data.comparison_ready],
      ["Replay",data.replay_ready],
      ["Migration",data.migration_ready]
    ].forEach(function(x){
      const item=div("service");
      const name=div("service-name"); name.textContent=x[0];
      const state=div("service-state"); state.textContent=x[1]?"Prêt":"À vérifier";
      item.append(name,state); services.append(item);
    });
    body.append(services);
    const actions=div("toolbar");
    actions.append(button("Actualiser","primary",async function(){
      const b=this; b.disabled=true; b.textContent="Actualisation…";
      try{ const next=await request("tools/call",{name:"get_status",arguments:{}}); renderStatus(parseToolResult(next)||data); }
      finally{ b.disabled=false; b.textContent="Actualiser"; }
    }));
    body.append(actions);
    root.append(body,footer(data.generated_at ? "Mis à jour "+new Date(data.generated_at).toLocaleString() : "Aurora Live Data"));
  }

  function capabilityList(model){
    const out=[];
    const f=model.capabilities&&model.capabilities.features||{};
    const t=model.capabilities&&model.capabilities.tools||{};
    if(f.structured_outputs===true) out.push("Structured outputs");
    if(f.function_calling===true) out.push("Function calling");
    if(t.web_search===true) out.push("Web search");
    if(t.file_search===true) out.push("File search");
    if(t.code_interpreter===true) out.push("Code interpreter");
    if(t.computer_use===true) out.push("Computer use");
    if(t.mcp===true) out.push("MCP");
    return out;
  }
  function renderComparison(data){
    root.replaceChildren();
    const models=Array.isArray(data.models)?data.models:[];
    root.append(header("Comparateur de modèles","Comparaison factuelle de modèles vérifiés. Aucun classement global implicite.",badge(models.length+" modèle"+(models.length>1?"s":""),"info")));
    const body=div("body");
    if(!models.length){ body.append(div("empty")).textContent="Aucun modèle à comparer."; root.append(body,footer()); return; }
    const grid=div(models.length>=3?"grid":"grid");
    models.forEach(function(model){
      const c=div("card model-card");
      const top=div("row"); const names=div("");
      const pr=div("provider"); pr.textContent=escapeText(model.provider_slug);
      const h=document.createElement("h2"); h.textContent=escapeText(model.display_name||model.model_key);
      names.append(pr,h);
      const tone=model.default_policy==="include"?"good":model.default_policy==="include_with_warning"?"warn":model.default_policy==="exclude"||model.default_policy==="stale"?"bad":"info";
      top.append(names,badge(escapeText(model.default_policy),tone)); c.append(top);
      [
        ["Contexte",typeof model.context_window_tokens==="number"?num(model.context_window_tokens)+" tokens":"Inconnu"],
        ["Sortie max.",typeof model.max_output_tokens==="number"?num(model.max_output_tokens)+" tokens":"Inconnue"],
        ["Cycle de vie",escapeText(model.lifecycle_status)],
        ["Input / 1M",money(model.pricing&&model.pricing.input)],
        ["Output / 1M",money(model.pricing&&model.pricing.output)]
      ].forEach(function(row){ const m=div("metric"); const a=document.createElement("span");a.textContent=row[0];const b=document.createElement("span");b.textContent=row[1];m.append(a,b);c.append(m); });
      const chips=div("chips"); capabilityList(model).slice(0,7).forEach(function(x){const s=div("chip");s.textContent=x;chips.append(s);}); c.append(chips);
      const details=div("details");
      details.append(p("Vérification : "+escapeText(model.verification_state),"small"),p("Source : "+escapeText(model.semantic_source_url),"small muted"));
      const actions=div("toolbar");
      const toggle=button("Détails","ghost",function(){ details.classList.toggle("open"); toggle.textContent=details.classList.contains("open")?"Masquer":"Détails"; });
      const use=button("Utiliser ce modèle","primary",function(){ sendMessage("Utilise "+model.model_key+" comme modèle cible pour la suite. Préserve les contraintes déjà établies et adapte le prompt avec la guidance vérifiée du fournisseur."); });
      actions.append(toggle,use); c.append(details,actions); grid.append(c);
    });
    body.append(grid);
    if(data.interpretation) body.append(p(data.interpretation,"small muted"));
    root.append(body,footer(data.generated_at?"Données "+new Date(data.generated_at).toLocaleString():"Aurora Model Selector"));
  }

  function outcomeTone(outcome){
    if(outcome==="pass")return"good";
    if(outcome==="fail")return"bad";
    if(outcome==="needs_review")return"warn";
    return"info";
  }
  function renderValidation(data){
    root.replaceChildren();
    const status=String(data.status||data.final_release_gate||"needs_review").toLowerCase();
    root.append(header("Rapport de validation",escapeText(data.summary||"Contrôles Aurora appliqués au prompt."),badge(status.toUpperCase(),outcomeTone(status))));
    const body=div("body stack");
    const gateGrid=div("grid three");
    [
      ["Eval",data.eval_release_gate],
      ["Golden",data.golden_release_gate],
      ["Runtime",data.runtime_gate||data.runtime_release_gate]
    ].forEach(function(x){
      const c=div("card"); c.append(p(x[0],"small muted")); const v=div("value");v.textContent=escapeText(x[1]||"—").toUpperCase();c.append(v);gateGrid.append(c);
    });
    body.append(gateGrid);
    const toolbar=div("toolbar");
    const criteria=Array.isArray(data.criteria)?data.criteria:[];
    const list=div("criteria");
    function paint(filter){
      list.replaceChildren();
      criteria.filter(function(x){return filter==="all"||String(x.outcome)!=="pass";}).forEach(function(item){
        const row=div("criterion");
        const head=div("row"); const title=div("title");title.textContent=escapeText(item.label||item.id);head.append(title,badge(String(item.outcome||"unknown").toUpperCase(),outcomeTone(item.outcome)));row.append(head);
        if(item.note) row.append(p(String(item.note),"note"));
        list.append(row);
      });
      if(!list.children.length){const e=div("empty");e.textContent="Aucun élément pour ce filtre.";list.append(e);}
    }
    toolbar.append(button("Tous","",function(){paint("all");}),button("À revoir","",function(){paint("issues");}));
    body.append(toolbar,list);
    if(Array.isArray(data.unresolved)&&data.unresolved.length){
      const call=div("callout warn"); call.append(p("Points non résolus","small muted"),p(data.unresolved.join(" • "),"small")); body.append(call);
    }
    const actions=div("toolbar");
    if(status!=="pass"){
      actions.append(button("Corriger avec Aurora","primary",function(){sendMessage("Corrige le prompt en traitant les critères en FAIL ou NEEDS_REVIEW du rapport de validation affiché, sans modifier l’intention ni inventer de nouvelles contraintes.");}));
    }else{
      actions.append(button("Voir le manifeste","",function(){sendMessage("Montre-moi le manifeste de validation détaillé de ce prompt.");}));
    }
    body.append(actions);
    root.append(body,footer("Réparations : "+escapeText(data.repair_passes||0)+" / 2"));
  }

  function renderMigration(data){
    root.replaceChildren();
    const status=String(data.status||"needs_review").toLowerCase();
    root.append(header("Plan de migration",escapeText(data.trigger||"Migration de prompt vers une cible actuelle."),badge(status.toUpperCase(),outcomeTone(status==="plan_ready"?"pass":status==="blocked"?"fail":"needs_review"))));
    const body=div("body stack");
    const source=div("card");
    source.append(p("Cible actuelle","small muted"));
    const sv=div("value"); sv.textContent=escapeText(data.source_target&&data.source_target.model_key||data.source_model); source.append(sv);
    if(data.source_target&&data.source_target.lifecycle_status) source.append(p("Cycle de vie : "+data.source_target.lifecycle_status,"small muted"));
    body.append(source);
    if(data.selected_target){
      const sel=div("callout");
      sel.append(p("Cible proposée","small muted"),p(escapeText(data.selected_target.model_key||data.selected_target.display_name),""));
      body.append(sel);
    }
    const candidates=Array.isArray(data.eligible_candidates)?data.eligible_candidates:[];
    if(candidates.length){
      const title=p("Candidats compatibles","small muted"); body.append(title);
      const grid=div("grid");
      candidates.slice(0,6).forEach(function(model){
        const c=div("card model-card");
        const pr=div("provider");pr.textContent=escapeText(model.provider_slug);
        const h=document.createElement("h2");h.textContent=escapeText(model.display_name||model.model_key);
        c.append(pr,h,badge(escapeText(model.default_policy),model.default_policy==="include"?"good":"warn"));
        const m1=div("metric");m1.innerHTML="<span>Contexte</span><span></span>";m1.lastChild.textContent=typeof model.context_window_tokens==="number"?num(model.context_window_tokens):"Inconnu";
        const m2=div("metric");m2.innerHTML="<span>Sortie max.</span><span></span>";m2.lastChild.textContent=typeof model.max_output_tokens==="number"?num(model.max_output_tokens):"Inconnue";
        c.append(m1,m2,button("Choisir cette cible","primary",function(){sendMessage("Choisis "+model.model_key+" comme cible de migration et adapte le prompt en conservant toutes les contraintes établies. Revalide ensuite la version migrée.");}));
        grid.append(c);
      });
      body.append(grid);
    }
    if(Array.isArray(data.warnings)&&data.warnings.length){
      const call=div("callout warn"); call.append(p("Avertissements","small muted")); data.warnings.forEach(function(w){call.append(p("• "+w,"small"));});body.append(call);
    }
    if(Array.isArray(data.required_actions)&&data.required_actions.length){
      const call=div("card");call.append(p("Actions requises","small muted"));data.required_actions.forEach(function(a){call.append(p("• "+a,"small"));});body.append(call);
    }
    root.append(body,footer("Aurora Prompt Migration"));
  }

  function render(data){
    latest=data||{};
    if(KIND==="status")return renderStatus(latest);
    if(KIND==="comparison")return renderComparison(latest);
    if(KIND==="validation")return renderValidation(latest);
    if(KIND==="migration")return renderMigration(latest);
  }

  window.addEventListener("message",function(event){
    if(event.source!==window.parent)return;
    const message=event.data;
    if(!message||message.jsonrpc!=="2.0")return;
    if(message.id!==undefined&&pending.has(message.id)){
      const p=pending.get(message.id);pending.delete(message.id);
      if(message.error)p.reject(message.error);else p.resolve(message.result);
      return;
    }
    if(message.method==="ui/notifications/tool-result"){
      render(message.params&&message.params.structuredContent ? message.params.structuredContent : parseToolResult(message.params));
    }
    if(message.method==="ui/notifications/host-context-changed") applyContext(message.params);
  },{passive:true});

  async function init(){
    try{
      const res=await request("ui/initialize",{
        protocolVersion:"2026-01-26",
        appInfo:{name:"aurora-"+KIND,title:"Aurora",version:"1.0.0",websiteUrl:"https://aurora.le-corre-alexis.fr/"},
        appCapabilities:{}
      });
      applyContext(res&&res.hostContext);
      notify("ui/notifications/initialized",{});
      initialized=true;
    }catch(e){}
    if(window.openai&&window.openai.toolOutput) render(window.openai.toolOutput);
    const ro=new ResizeObserver(function(){
      const h=Math.ceil(document.documentElement.scrollHeight);
      notify("ui/notifications/size-changed",{height:h});
    });
    ro.observe(document.documentElement);
  }
  init();
})();
</script>
</body>
</html>`;

export function createAuroraWidgetHtml(kind: AuroraWidgetKind): string {
  return BASE_WIDGET.replace('__KIND__', kind);
}
