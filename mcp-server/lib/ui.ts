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
  --aurora-navy:#0c1f66;
  --aurora-paper:#fdfcf9;
  --aurora-white:#ffffff;
  --aurora-ink:#171d31;
  --aurora-muted:#66719d;
  --aurora-line:#dcdee8;
  --aurora-mint:#eff8f5;
  --aurora-cyan:#1d8d9c;
  --aurora-purple:#5c1d91;
  --aurora-violet:#6e52d9;
  --good:#0b7a63;
  --warn:#9a5b00;
  --bad:#a62e3f;
  --shadow:0 14px 40px rgba(12,31,102,.08);
}
*{box-sizing:border-box}
html,body{
  margin:0;padding:0;background:transparent;color:var(--aurora-ink);
  font:14px/1.6 "Avenir Next","Century Gothic",Avenir,Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}
body{padding:10px}
button{font:inherit}
.shell{
  position:relative;
  overflow:hidden;
  background:var(--aurora-paper);
  border:1px solid rgba(12,31,102,.14);
  border-radius:14px;
  box-shadow:var(--shadow);
}
.shell:before{
  content:"";
  display:block;
  height:3px;
  background:linear-gradient(90deg,var(--aurora-purple),var(--aurora-violet) 42%,#00c7e8 78%,var(--aurora-cyan));
}
.header{
  position:relative;
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:18px;
  padding:16px 18px 15px;
  color:#fff;
  background:
    radial-gradient(circle at 92% 10%,rgba(0,199,232,.16),transparent 26%),
    radial-gradient(circle at 82% 110%,rgba(110,82,217,.2),transparent 35%),
    var(--aurora-navy);
  border-bottom:0;
}
.header:after{
  content:"";
  position:absolute;
  right:-12px;top:-28px;
  width:145px;height:145px;border-radius:50%;
  border:1px solid rgba(255,255,255,.08);
  box-shadow:
    inset 0 0 0 11px rgba(29,141,156,.02),
    inset 0 0 0 29px rgba(110,82,217,.025);
  pointer-events:none;
}
.brand-row{display:flex;align-items:center;gap:12px;margin-bottom:12px;min-height:30px}
.brand-logo{display:block;width:168px;max-width:54vw;height:auto;object-fit:contain}
.header-copy{position:relative;z-index:1;min-width:0}
.header-side{position:relative;z-index:1;display:flex;align-items:flex-start;padding-top:2px}
.eyebrow{
  font-size:10px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:#9ee9f0;margin:0 0 4px
}
h1{
  margin:0 0 5px;
  color:#fff;
  font-size:22px;
  line-height:1.12;
  letter-spacing:-.025em;
  font-weight:700
}
h2{color:var(--aurora-navy)}
.sub{margin:0;color:rgba(255,255,255,.75);font-size:12px;max-width:620px}
.body{padding:17px 18px 18px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 18px}
.grid.three{grid-template-columns:repeat(3,minmax(0,1fr));gap:0 18px}
.card{
  position:relative;
  min-width:0;
  padding:13px 0 14px;
  border:0;
  border-bottom:1px solid var(--aurora-line);
  background:transparent;
  border-radius:0
}
.grid>.card:nth-last-child(-n+3){ }
.card strong{display:block;font-size:13px;margin-bottom:4px;color:var(--aurora-navy)}
.value{font-size:22px;font-weight:750;letter-spacing:-.025em;color:var(--aurora-navy)}
.muted{color:var(--aurora-muted)}
.small{font-size:12px}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px}
.stack{display:flex;flex-direction:column;gap:13px}
.badge{
  display:inline-flex;align-items:center;gap:7px;
  border:1px solid currentColor;border-radius:999px;
  padding:4px 8px;font-size:10px;font-weight:750;
  background:rgba(255,255,255,.04);
  letter-spacing:.035em
}
.header .badge{background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.22)}
.badge.good{color:#6ff0c7}
.badge.warn{color:#ffd98a}
.badge.bad{color:#ff9aa8}
.badge.info{color:#9ee9f0}
.body .badge.good{color:var(--good);background:#eaf7f2;border-color:#b8e0d3}
.body .badge.warn{color:var(--warn);background:#fff6df;border-color:#ead7a5}
.body .badge.bad{color:var(--bad);background:#fff0f2;border-color:#edc2c8}
.body .badge.info{color:var(--aurora-navy);background:#eef2ff;border-color:#cfd7f5}
.dot{width:7px;height:7px;border-radius:50%;background:currentColor}
.btn{
  appearance:none;
  border:1px solid var(--aurora-navy);
  background:transparent;
  color:var(--aurora-navy);
  border-radius:4px;
  padding:8px 11px;
  cursor:pointer;
  font-weight:700;
  transition:background .16s ease,color .16s ease,transform .16s ease
}
.btn:hover{background:rgba(12,31,102,.055)}
.btn.primary{background:var(--aurora-navy);border-color:var(--aurora-navy);color:#fff}
.btn.primary:hover{background:#142d7f}
.btn.ghost{background:transparent}
.btn:active{transform:translateY(1px)}
.btn:focus-visible{outline:2px solid var(--aurora-cyan);outline-offset:3px}
.metric{
  display:flex;justify-content:space-between;gap:12px;
  padding:8px 0;border-bottom:1px solid var(--aurora-line)
}
.metric:last-child{border-bottom:none}
.metric span:first-child{color:var(--aurora-muted)}
.metric span:last-child{color:var(--aurora-navy);font-weight:650;text-align:right}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.chip{
  padding:4px 7px;border-radius:3px;
  background:var(--aurora-mint);
  border:1px solid #d7ebe4;
  color:#234b56;
  font-size:10px
}
.toolbar{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px;margin-bottom:2px}
.criteria{display:flex;flex-direction:column;gap:0;border-top:1px solid var(--aurora-line)}
.criterion{
  border:0;border-bottom:1px solid var(--aurora-line);border-radius:0;
  padding:11px 0;background:transparent
}
.criterion .title{font-weight:700;color:var(--aurora-navy)}
.criterion .note{margin-top:5px;color:var(--aurora-muted);font-size:12px}
.model-card{display:flex;flex-direction:column;gap:8px;padding:14px 0 15px}
.model-card h2{font-size:16px;margin:0;word-break:break-word;color:var(--aurora-navy);letter-spacing:-.015em}
.provider{color:var(--aurora-cyan);font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:750}
.details{display:none;padding:7px 0 2px}
.details.open{display:block}
.callout{
  border-left:3px solid var(--aurora-cyan);
  padding:11px 12px;
  background:var(--aurora-mint);
  border-radius:0
}
.callout.warn{border-left-color:#d19a2b;background:#fff8e8}
.callout.bad{border-left-color:var(--bad);background:#fff2f3}
.arrow{font-size:18px;color:var(--aurora-muted);text-align:center}
.empty{padding:22px 4px;text-align:center;color:var(--aurora-muted)}
.footer{
  position:relative;
  padding:11px 18px;
  border-top:1px solid var(--aurora-line);
  display:flex;justify-content:space-between;align-items:center;gap:10px;
  color:var(--aurora-muted);font-size:10px;
  background:#fbfaf7
}
.footer:before{
  content:"";
  position:absolute;left:18px;top:-1px;width:56px;height:2px;
  background:linear-gradient(90deg,var(--aurora-purple),var(--aurora-cyan))
}
@media (max-width:640px){
  body{padding:6px}
  .grid,.grid.three{grid-template-columns:1fr}
  .header{padding:14px}
  .body{padding:14px}
  .brand-logo{width:150px}
  h1{font-size:19px}
  .header-side{max-width:42%}
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
  const BRAND_LOGO="data:image/png;base64,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";
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
  function div(cls){ const el=document.createElement("div"); if(cls)el.className=cls; return el; }
  function p(text,cls){ const el=document.createElement("p"); if(cls)el.className=cls; el.textContent=text; return el; }
  function button(label,cls,fn){
    const b=document.createElement("button"); b.type="button"; b.className="btn "+(cls||""); b.textContent=label; b.addEventListener("click",fn); return b;
  }
  function header(title,subtitle,badgeNode){
    const h=div("header");
    const left=div("header-copy");
    const brand=div("brand-row");
    const logo=document.createElement("img");
    logo.src=BRAND_LOGO;
    logo.alt="Aurora — by Alexis Le Corre";
    logo.className="brand-logo";
    brand.append(logo);
    const eyebrow=div("eyebrow"); eyebrow.textContent="Interface Aurora";
    const t=document.createElement("h1"); t.textContent=title;
    left.append(brand,eyebrow,t,p(subtitle||"","sub"));
    h.append(left);
    if(badgeNode){ const side=div("header-side"); side.append(badgeNode); h.append(side); }
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
    root.append(header("Aurora Live Data","État actuel du registre et des couches de validation.",badge(healthy?"Sain":"Dégradé",healthy?"good":"bad")));
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
    const gates=div("card");
    gates.append(p("Services avancés","small muted"));
    const chips=div("chips");
    [
      ["Traceability",data.traceability_ready],
      ["Comparison",data.comparison_ready],
      ["Replay",data.replay_ready],
      ["Migration",data.migration_ready]
    ].forEach(function(x){ chips.append(badge(x[0]+": "+(x[1]?"ready":"unknown"),x[1]?"good":"warn")); });
    gates.append(chips); body.append(gates);
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
