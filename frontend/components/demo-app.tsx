"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { CitationViewer, type CitationView } from "./citation-viewer";

type Quote = { section_id:string; page_id:string; quote:string; occurrence:number };
type Card = { plan_id:string; index_version:string; card_version?:string; insurer:string; name:string; variant:string; plan_type:string; status:string; field_coverage?:Record<string,boolean>; rule_coverage?:Record<string,boolean> };
type Reason = { field:string; status:string; explanation:string; citations:Quote[]; strength?:string; coverage_status?:string };
type Fit = { plan_id:string; status:string; hard_limits:Reason[]; other_needs:Reason[] };
type Anchor = { quote:string; page:number; document_id:string; boxes:[number,number,number,number][]; pdf_url:string };
type PlanAnswer = { id:string; plan_id:string; name:string; variant:string; insurer:string; state:string; model:string; result?:{message?:string; answer?:{statements:{text:string; coverage_scope?:"base"|"optional, extra premium"|"optional premium adjustment"; scope_product?:string; scope_variant?:string; heading?:string; excerpts?:string[]; conditions:{text:string}[]; restrictions:{text:string}[]}[]}; validation?:{anchors:Anchor[]} } };
type Question = { id:string; state:string; plans:PlanAnswer[] };
type State = { revision:number; stage:string; message:string; understanding:string[]; pending:{text:string;field:string}|null; fit_groups:Record<string,Fit[]>; selected_plans:string[]; restored_plans:string[]; insurer_filter:string|null; question_id:string|null; question_count:number; stop_reason:string|null; price_plan:string|null; price:{status:string;amount_printed:string|null;label?:string;caveat?:string;budget_comparison?:{status:string;note:string};citations:Quote[];axis_options?:Record<string,string[]>}|null; transcript:Message[]; turns:{elapsed_ms:number}[] };
type Chat = { id:string; release_id:string; cards:Card[]; state:State };
type Message = { role:"customer"|"assistant";text:string;understanding?:string[] };
const groups = [["fits","Fits"],["unresolved","Can’t tell"],["doesnt_fit","Doesn’t fit"]] as const;
const label = (c:Card) => `${c.insurer} — ${c.name} (${c.variant})`;

export function DemoApp({onSignedOut}:{onSignedOut:()=>Promise<void>}) {
  const [chat,setChat]=useState<Chat|null>(null);
  const [messages,setMessages]=useState<Message[]>([]);
  const [text,setText]=useState("");
  const [screen,setScreen]=useState("chat");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [question,setQuestion]=useState<Question|null>(null);
  const [citation,setCitation]=useState<CitationView|null>(null);
  const [erase,setErase]=useState(false);
  const events=useRef<EventSource|null>(null);
  const delayedReply=useRef<Message|null>(null);
  const receipt=useRef<{text:string;revision:number;request_id:string}|null>(null);
  useEffect(()=>{
    const id=new URLSearchParams(window.location.search).get("conversation");
    if(id)void api<Chat>(`/api/v2/demo/conversations/${id}/`).then(data=>{setChat(data);if(data.state.question_id){const history=[...data.state.transcript];const reply=history.at(-1);if(reply?.role==="assistant"){delayedReply.current=history.pop()!;}setMessages(history);stream(data.state.question_id);}else{setMessages(data.state.transcript);}}).catch(e=>setError(e instanceof Error?e.message:"Conversation unavailable"));
    return ()=>events.current?.close();
  },[]);

  async function begin() {
    setBusy(true);setError("");
    try {const data=await api<Chat>("/api/v2/demo/conversations/",{method:"POST"});setChat(data);window.history.replaceState(null,"",`?conversation=${data.id}`);setMessages([{role:"assistant",text:data.state.message,understanding:data.state.understanding}]);setQuestion(null);events.current?.close();}
    catch(e){setError(e instanceof Error?e.message:"Could not start chat");}finally{setBusy(false);}
  }
  function acceptQuestion(data:Question) {
    setQuestion(data);
    if(["completed","cancelled"].includes(data.state)){events.current?.close();if(delayedReply.current){const reply=delayedReply.current;delayedReply.current=null;setMessages(old=>[...old,reply]);}}
  }
  async function refreshComparison(id:string) {
    try {const data=await api<Question>(`/api/v2/demo/questions/${id}/`);acceptQuestion(data);setError("");}
    catch(e){setError(e instanceof Error?e.message:"Could not refresh comparison");}
  }
  function stream(id:string) {
    events.current?.close();const source=new EventSource(`/api/v2/demo/questions/${id}/events/`);events.current=source;
    source.onmessage=event=>acceptQuestion(JSON.parse(event.data) as Question);
    source.onerror=()=>{source.close();setError("Live updates paused. Refresh the comparison to check progress.");};
  }
  async function send(message:string) {
    if(!chat||busy||!message.trim()||chat.state.stage==="stopped")return;
    setBusy(true);setError("");
    const request=receipt.current?.text===message&&receipt.current.revision===chat.state.revision?receipt.current:{text:message,revision:chat.state.revision,request_id:crypto.randomUUID()};receipt.current=request;
    try {const data=await api<Chat>(`/api/v2/demo/conversations/${chat.id}/`,{method:"POST",body:JSON.stringify(request)});
      setChat(data);setText("");receipt.current=null;const reply:Message={role:"assistant",text:data.state.message,understanding:data.state.understanding};
      if(data.state.question_id){delayedReply.current=reply;setMessages(old=>[...old,{role:"customer",text:message}]);setQuestion(null);stream(data.state.question_id);}
      else {delayedReply.current=null;setMessages(old=>[...old,{role:"customer",text:message},reply]);if(data.state.stage==="stopped")events.current?.close();}setScreen("chat");
    }catch(e){setError(e instanceof Error?e.message:"Message unavailable");}finally{setBusy(false);}
  }
  async function showCitation(card:Card,q:Quote,kind="cards") {
    setError("");try {const a=await api<Anchor>(`/api/v2/demo/${card.card_version?(kind==="cards"?"fact-cards":"fact-prices"):kind}/${card.card_version||card.index_version}/citation/`,{method:"POST",body:JSON.stringify({citation:q})});setCitation({documentVersionId:a.document_id,page:a.page,quote:a.quote,label:`${label(card)} · physical page ${a.page}`,bbox:null,boxes:a.boxes,pdfUrl:a.pdf_url});}
    catch(e){setError(e instanceof Error?e.message:"Source unavailable");}
  }
  async function answerCitation(p:PlanAnswer,n:number){try{const a=await api<Anchor>(`/api/v2/demo/citations/${p.id}/${n}/`);setCitation({documentVersionId:a.document_id,page:a.page,quote:a.quote,label:`${p.name} · physical page ${a.page}`,bbox:null,boxes:a.boxes,pdfUrl:a.pdf_url});}catch(e){setError(e instanceof Error?e.message:"Source unavailable");}}
  const answering=Boolean(chat?.state.question_id&&(!question||!["completed","cancelled"].includes(question.state)));
  const cards=chat?.cards||[];
  const selected=cards.filter(c=>chat?.state.selected_plans.includes(c.plan_id));
  function reasons(card:Card,fit:Fit){return <details open={chat?.state.stop_reason==="none_remain"}><summary>Quoted reasons and unresolved checks</summary>{[...fit.hard_limits,...fit.other_needs].map((r,n)=><div className="demo-reason" key={n}><p>{r.strength&&<strong>{r.strength.replaceAll("_"," ")} · {r.coverage_status} · </strong>}{r.explanation}</p>{r.citations.map((q,i)=><button className="demo-citation" key={i} onClick={()=>void showCitation(card,q)}><q>{q.quote}</q><span>Open source ↗</span></button>)}</div>)}</details>;}
  return <div className="demo-shell">
    <header className="demo-header"><a className="demo-brand" href="/demo">CoverGuide<span>Document-led comparison</span></a><span className="demo-local">LOCAL DEMO</span></header>
    <nav className="demo-nav" aria-label="Comparison screens">{[["chat","Guided chat"],["catalogue","All plans"],["comparison","Comparison"],["prices","Prices"],["coverage","Source coverage"]].map(([key,title])=><button key={key} aria-current={screen===key?"page":undefined} onClick={()=>setScreen(key)}>{title}</button>)}</nav>
    <p className="demo-notice">A neutral comparison from policy documents. Underwriting and claim decisions remain with the insurer. This local demonstration has not been reviewed by an insurance expert.</p>
    {error&&<p role="alert" className="demo-error">{error}</p>}
    {!chat?<section className="demo-intro"><h1>Let’s understand the cover you need</h1><p>Reply in your own words. You can share several details at once, skip a question, correct a detail, or stop at any time.</p><button className="demo-primary" disabled={busy} onClick={()=>void begin()}>Start guided chat</button></section>:<>
      <div className="demo-chat-layout">
        <main>
          {screen==="chat"&&<section aria-label="Guided conversation"><p className="demo-status">Stage: {chat.state.stage} · Questions asked: {chat.state.question_count}</p>
            <div className="demo-transcript" aria-live="polite">{messages.map((m,i)=><article className={`demo-message ${m.role}`} key={i}><strong>{m.role==="customer"?"You":"CoverGuide"}</strong><p>{m.text}</p>{m.understanding&&<details open><summary>Here’s what I understood</summary>{m.understanding.map((line,n)=><p key={n}>{line}</p>)}</details>}</article>)}</div>
            {answering&&<p role="status">Comparing the policy documents. The guided question will resume when the evidence is ready.</p>}{chat.state.stage!=="stopped"&&<div className="demo-chat-compose"><label htmlFor="chat-reply">Your reply</label><textarea id="chat-reply" value={text} onChange={e=>setText(e.target.value)} rows={3} placeholder="Tell me in your own words…"/><button className="demo-primary" disabled={busy||answering||!text.trim()} onClick={()=>void send(text)}>{busy?"Working…":"Send message"}</button><div className="demo-chips">{["Skip","Stop","What are the PED waiting periods?"].map(value=><button disabled={busy||(answering&&value!=="Stop")} key={value} onClick={()=>void send(value)}>{value}</button>)}</div></div>}
            {chat.state.stage==="stopped"&&<button onClick={()=>void begin()}>Start a new conversation</button>}
            {chat.state.turns.length>0&&<small>Last reply processed in {(chat.state.turns.at(-1)!.elapsed_ms/1000).toFixed(1)} s. Policy answers stream separately.</small>}
          </section>}
          {screen==="catalogue"&&<section><h1>All plans</h1><p>These shortcuts send their visible text as chat messages. Restoring a plan retains its documented fit classification.</p><div className="demo-chips"><button onClick={()=>void send("Show all insurers")}>Show all insurers</button>{Array.from(new Set(cards.map(c=>c.insurer))).map(insurer=><button key={insurer} onClick={()=>void send(`Show ${insurer} in the catalogue`)}>Show {insurer} in the catalogue</button>)}</div>{cards.filter(c=>!chat.state.insurer_filter||c.insurer===chat.state.insurer_filter).map(c=><article className="demo-plan" key={c.plan_id}><small>{c.insurer}</small><h2>{c.name}</h2><p>{c.variant} · {c.plan_type}</p><button disabled={busy} onClick={()=>void send("Compare "+label(c))}>Compare {label(c)}</button><button disabled={busy} onClick={()=>void send("Restore "+label(c))}>Restore {label(c)}</button></article>)}</section>}
          {(screen==="comparison"||screen==="chat"&&(question||chat.state.stop_reason==="two_or_three_remain"))&&<section><h2>Side-by-side comparison</h2><p>{selected.length?selected.map(c=>c.name+" · "+c.variant).join(" | "):"Select compatible plans through chat or the catalogue."}</p>{!question&&selected.length>0&&<div className="demo-columns">{selected.map(c=>{const fit=Object.values(chat.state.fit_groups).flat().find(f=>f.plan_id===c.plan_id);return <article className="demo-answer-column" key={c.plan_id}><small>{c.insurer}</small><h3>{c.name}</h3><p>{c.variant}</p><p>{fit?.status==="fits"?"Fits":fit?.status==="doesnt_fit"?"Doesn’t fit":"Can’t tell"}</p>{fit&&reasons(c,fit)}</article>;})}</div>}{question&&<div className="demo-columns">{question.plans.map(p=><article className="demo-answer-column" key={p.id}><small>{p.insurer}</small><h3>{p.name}</h3><p>{p.variant} · {p.state}</p>{p.result?.message&&<p className="demo-notice">{p.result.message}</p>}{p.result?.answer?.statements.map((s,n)=><section key={n}><strong>{s.heading||"Policy excerpt"}</strong>{s.coverage_scope&&s.coverage_scope!=="base"&&<p className="demo-notice">{s.coverage_scope==="optional premium adjustment"?"Optional premium adjustment — see the quoted discount and conditions":"Optional, extra premium"}</p>}{(s.excerpts?.length?s.excerpts:[s.text]).map((t,i)=><blockquote key={i}>{t}</blockquote>)}{s.conditions.map((v,i)=><blockquote key={i}>{v.text}</blockquote>)}{s.restrictions.map((v,i)=><blockquote key={i}>{v.text}</blockquote>)}</section>)}{p.result?.validation?.anchors.map((a,n)=><button key={n} className="demo-citation" onClick={()=>void answerCitation(p,n)}>Open source · physical page {a.page}</button>)}<small>{p.model}</small></article>)}</div>}{question&&<div><button onClick={()=>void refreshComparison(question.id)}>Refresh comparison</button><button onClick={()=>void api(`/api/v2/demo/questions/${question.id}/cancel/`,{method:"POST"}).then(()=>{events.current?.close();setQuestion({...question,state:"cancelled"});if(delayedReply.current){const reply=delayedReply.current;delayedReply.current=null;setMessages(old=>[...old,reply]);}})}>Cancel answering</button></div>}</section>}
          {(screen==="prices"||screen==="chat"&&chat.state.price)&&<section><h1>Printed indicative prices</h1><p>Request a plan’s price in chat. Each missing printed axis is collected in a separate chat question; no amount, tax, discount or loading is inferred.</p>{selected.map(c=><button key={c.plan_id} onClick={()=>void send(`Show the printed price for ${label(c)}`)}>Show the printed price for {label(c)}</button>)}{chat.state.price&&<article><h2>{chat.state.price.status}</h2><p>{chat.state.price.amount_printed}</p><p>{chat.state.price.label}</p><p>{chat.state.price.caveat}</p>{chat.state.price.budget_comparison&&<p>{chat.state.price.budget_comparison.status.replaceAll("_"," ")} · {chat.state.price.budget_comparison.note}</p>}{chat.state.price.citations.map((q,i)=>{const c=cards.find(c=>c.plan_id===chat.state.price_plan);return c?<button key={i} onClick={()=>void showCitation(c,q,"prices")}>{q.quote} · Open source</button>:null;})}</article>}</section>}
          {screen==="coverage"&&<section><h1>Source coverage</h1><p>Quoted evidence and executable rules are different measures. “Not stated” does not count as filled.</p><p>Release: {chat.release_id}</p>{cards.map(c=><article className="demo-plan" key={c.plan_id}><h2>{c.insurer} · {c.name} · {c.variant}</h2><p>Quoted fields: {Object.values(c.field_coverage||{}).filter(Boolean).length}/{Object.keys(c.field_coverage||{}).length}. Executable fields: {Object.values(c.rule_coverage||{}).filter(Boolean).length}/{Object.keys(c.rule_coverage||{}).length}.</p><p>{c.status} · Card version: {c.card_version||"Legacy"}</p></article>)}</section>}
        </main>
        <aside aria-label="Live fit list"><h2>All fit groups</h2>{groups.map(([key,title])=><section key={key}><h3>{title} ({chat.state.fit_groups[key].length})</h3>{chat.state.fit_groups[key].map(f=>{const c=cards.find(c=>c.plan_id===f.plan_id)!;return <article className="demo-plan" key={f.plan_id}><small>{c.insurer}</small><h4>{c.name}</h4><p>{c.variant}</p>{chat.state.restored_plans.includes(c.plan_id)&&<p>Restored for comparison; classification retained.</p>}{reasons(c,f)}<button disabled={busy} onClick={()=>void send("Compare "+label(c))}>Compare {label(c)}</button>{key==="doesnt_fit"&&<button disabled={busy} onClick={()=>void send("Restore "+label(c))}>Restore {label(c)}</button>}</article>;})}</section>)}</aside>
      </div>
    </>}
    {citation&&<CitationViewer citation={citation} onClose={()=>setCitation(null)}/>}
    <footer className="demo-footer"><button onClick={()=>void api("/api/v1/auth/logout/",{method:"POST"}).then(onSignedOut)}>Sign out</button><button onClick={()=>setErase(true)}>Erase my account data</button>{erase&&<div><p>Erase this account and its private conversation data?</p><button onClick={()=>void api("/api/v1/account/",{method:"DELETE"}).then(onSignedOut)}>Confirm erasure</button><button onClick={()=>setErase(false)}>Keep my account</button></div>}</footer>
  </div>;
}
