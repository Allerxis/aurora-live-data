export type AuroraWidgetKind =
  | 'status'
  | 'comparison'
  | 'validation'
  | 'migration';

const BASE_WIDGET = String.raw\`<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<style>
:root{
  color-scheme:light dark;
  --bg:#ffffff;
  --panel:#f7f8fb;
  --panel-2:#eef2f8;
  --text:#111827;
  --muted:#667085;
  --line:#dbe2ea;
  --accent:#2855d9;
  --accent-2:#0f766e;
  --good:#047857;
  --warn:#b45309;
  --bad:#b42318;
  --shadow:0 8px 30px rgba(15,23,42,.08);
}
:root[data-theme="dark"]{
  --bg:#0b0f17;
  --panel:#111827;
  --panel-2:#182132;
  --text:#f4f7fb;
  --muted:#9aa7ba;
  --line:#273449;
  --accent:#7aa2ff;
  --accent-2:#5eead4;
  --good:#5ee2aa;
  --warn:#f6c45e;
  --bad:#ff8f8f;
  --shadow:0 10px 34px rgba(0,0,0,.3);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:var(--text);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
body{padding:10px}
button{font:inherit}
.shell{border:1px solid var(--line);border-radius:16px;background:var(--bg);box-shadow:var(--shadow);overflow:hidden}
.header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:16px 16px 12px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
h1{font-size:18px;line-height:1.2;margin:3px 0 4px}
.sub{margin:0;color:var(--muted);font-size:12px}
.body{padding:14px 16px 16px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}
.card{border:1px solid var(--line);background:var(--panel);border-radius:12px;padding:12px;min-width:0}
.card strong{display:block;font-size:13px;margin-bottom:4px}
.value{font-size:20px;font-weight:750;letter-spacing:-.02em}
.muted{color:var(--muted)}
.small{font-size:12px}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px}
.stack{display:flex;flex-direction:column;gap:10px}
.badge{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:4px 8px;font-size:11px;font-weight:700;background:var(--panel)}
.badge.good{color:var(--good)}
.badge.warn{color:var(--warn)}
.badge.bad{color:var(--bad)}
.badge.info{color:var(--accent)}
.dot{width:7px;height:7px;border-radius:50%;background:currentColor}
.btn{border:1px solid var(--line);background:var(--panel);color:var(--text);border-radius:9px;padding:7px 10px;cursor:pointer;font-weight:650}
.btn:hover{border-color:var(--accent)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:white}
.btn.ghost{background:transparent}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.metric{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid var(--line)}
.metric:last-child{border-bottom:none}
.metric span:first-child{color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{padding:3px 7px;border-radius:999px;background:var(--panel-2);border:1px solid var(--line);font-size:11px}
.toolbar{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}
.criteria{display:flex;flex-direction:column;gap:7px}
.criterion{border:1px solid var(--line);border-radius:10px;padding:9px 10px;background:var(--panel)}
.criterion .title{font-weight:700}
.criterion .note{margin-top:4px;color:var(--muted);font-size:12px}
.model-card{display:flex;flex-direction:column;gap:9px}
.model-card h2{font-size:15px;margin:0;word-break:break-word}
.provider{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.details{display:none;padding-top:6px}
.details.open{display:block}
.callout{border-left:3px solid var(--accent);padding:9px 10px;background:var(--panel);border-radius:0 10px 10px 0}
.callout.warn{border-left-color:var(--warn)}
.callout.bad{border-left-color:var(--bad)}
.arrow{font-size:18px;color:var(--muted);text-align:center}
.empty{padding:18px;text-align:center;color:var(--muted)}
.footer{padding:10px 16px;border-top:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:10px;color:var(--muted);font-size:11px}
@media (max-width:640px){
  body{padding:6px}
  .grid,.grid.three{grid-template-columns:1fr}
  .header{padding:14px}
  .body{padding:12px 14px 14px}
}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
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
  function div(cls){ const el=document.createElement("div"); if(cls)el.className=cls; return el; }
  function p(text,cls){ const el=document.createElement("p"); if(cls)el.className=cls; el.textContent=text; return el; }
  function button(label,cls,fn){
    const b=document.createElement("button"); b.type="button"; b.className="btn "+(cls||""); b.textContent=label; b.addEventListener("click",fn); return b;
  }
  function header(title,subtitle,badgeNode){
    const h=div("header"); const left=div("");
    const eyebrow=div("eyebrow"); eyebrow.textContent="Aurora";
    const t=document.createElement("h1"); t.textContent=title;
    left.append(eyebrow,t,p(subtitle||"","sub")); h.append(left); if(badgeNode)h.append(badgeNode); return h;
  }
  function footer(text){
    const f=div("footer"); const a=document.createElement("span"); a.textContent=text||"Aurora Live Data";
    const b=document.createElement("span"); b.textContent="Lecture seule";
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
</html>\`;

export function createAuroraWidgetHtml(kind: AuroraWidgetKind): string {
  return BASE_WIDGET.replace('__KIND__', kind);
}
