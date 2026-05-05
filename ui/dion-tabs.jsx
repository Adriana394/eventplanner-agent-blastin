// Three additional tab views: Concrete venue planning, Structured trip brief, Follow-up iterations
const { IconEvent, IconLandmark, IconFork, IconLink, IconCheck, IconWarn, IconCpu, IconRefresh, IconClock } = window.DION_ICONS;

// ─── helpers ───
function jsonHL(obj){
  const json = JSON.stringify(obj, null, 2);
  return json
    .replace(/("(\\u[0-9a-fA-F]{4}|\\[^u]|[^\\"])*"\s*:)/g, '<span class="k">$1</span>')
    .replace(/: ("(\\u[0-9a-fA-F]{4}|\\[^u]|[^\\"])*")/g, ': <span class="s">$1</span>')
    .replace(/: (-?\d+\.?\d*)/g, ': <span class="n">$1</span>')
    .replace(/: (true|false|null)/g, ': <span class="b">$1</span>');
}

// ─── Tab 2: Concrete venue planning ───
function VenueTab({ plan }){
  const [filter, setFilter] = React.useState('all'); // all / events / sightseeing / food
  const [freeOnly, setFreeOnly] = React.useState(false);
  const [search, setSearch] = React.useState('');

  if(!plan){
    return <div className="empty">
      <div className="empty-icon"><IconLandmark size={20}/></div>
      <h3>No venues yet</h3>
      <p>Generate a plan in the Planner tab — Dion's verified events, sights and food spots will appear here as a flat, filterable inventory.</p>
    </div>;
  }

  const events = plan.top_events.map(e => ({ kind:'event', name:e.name, sub:e.venue_name, when:e.start_datetime, price:e.price_display, url:e.source_url }));
  const sights = plan.sightseeing_spots.map(s => ({ kind:'sightseeing', name:s.name, sub:s.opening_hours, price:s.entry_fee_display, url:s.source_url }));
  const food = plan.food_and_drink_spots.map(f => ({ kind:'food', name:f.name, sub:`${f.venue_type} · ${f.opening_hours||'hours tbd'}`, price:f.price_hint, url:f.source_url }));
  let rows = [...events, ...sights, ...food];
  if(filter !== 'all') rows = rows.filter(r => r.kind === filter);
  if(freeOnly) rows = rows.filter(r => (r.price||'').toLowerCase().includes('free') || (r.price||'').includes('0 EUR'));
  if(search.trim()) rows = rows.filter(r => (r.name+r.sub).toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="card" style={{maxWidth:1200, margin:'0 auto'}}>
      <div className="section-label"><span className="dot"></span>Concrete venue planning</div>
      <h2 className="card-title">All verified venues, flat & filterable</h2>
      <p className="card-sub">Inventory view of <code style={{fontFamily:'var(--mono)', fontSize:12, background:'var(--surface)', padding:'1px 6px', borderRadius:4}}>CoreResult.events</code> / <code style={{fontFamily:'var(--mono)', fontSize:12, background:'var(--surface)', padding:'1px 6px', borderRadius:4}}>sightseeing_spots</code> / <code style={{fontFamily:'var(--mono)', fontSize:12, background:'var(--surface)', padding:'1px 6px', borderRadius:4}}>food_and_drink_spots</code> — without the day-by-day grouping, useful for venue-first review.</p>

      <div style={{display:'flex', gap:10, alignItems:'center', flexWrap:'wrap', marginBottom:14}}>
        <div className="lang-toggle">
          {['all','event','sightseeing','food'].map(k => (
            <button key={k} className={filter===k?'active':''} onClick={()=>setFilter(k)} style={{textTransform:'capitalize'}}>{k}</button>
          ))}
        </div>
        <input className="input" style={{flex:1, minWidth:200, maxWidth:280}} placeholder="Search venue or area…" value={search} onChange={e=>setSearch(e.target.value)}/>
        <label style={{display:'flex', alignItems:'center', gap:8, fontSize:13, color:'var(--text-2)'}}>
          <input type="checkbox" className="toggle" checked={freeOnly} onChange={e=>setFreeOnly(e.target.checked)}/>Free only
        </label>
        <span className="helper" style={{marginLeft:'auto'}}>{rows.length} venue{rows.length===1?'':'s'}</span>
      </div>

      <div style={{border:'1px solid var(--border-soft)', borderRadius:12, overflow:'hidden'}}>
        <div style={{display:'grid', gridTemplateColumns:'90px 1fr 1fr 110px 90px', padding:'10px 14px', background:'oklch(0.18 0.04 290 / 0.7)', borderBottom:'1px solid var(--border-soft)', fontFamily:'var(--mono)', fontSize:10.5, color:'var(--text-3)', letterSpacing:'0.1em', textTransform:'uppercase'}}>
          <div>Type</div><div>Venue</div><div>Detail</div><div>Price</div><div>Link</div>
        </div>
        {rows.length === 0 ? (
          <div style={{padding:'30px 14px', textAlign:'center', color:'var(--text-3)', fontSize:13}}>No venues match the current filters.</div>
        ) : rows.map((r,i)=>(
          <div key={i} style={{display:'grid', gridTemplateColumns:'90px 1fr 1fr 110px 90px', padding:'12px 14px', borderTop: i===0?'0':'1px dashed var(--border-soft)', alignItems:'center', fontSize:13}}>
            <div><span className={`stop-type ${r.kind === 'event' ? 'event' : r.kind === 'sightseeing' ? 'sightseeing' : 'food'}`}>{r.kind}</span></div>
            <div style={{fontWeight:600}}>{r.name}</div>
            <div style={{color:'var(--text-3)', fontSize:12.5}}>{r.sub || '—'}</div>
            <div style={{fontFamily:'var(--mono)', fontSize:11.5, color: (r.price||'').toLowerCase().includes('free') ? 'oklch(0.85 0.16 155)' : 'var(--text-2)'}}>{r.price || '—'}</div>
            <div>{r.url ? <a className="item-link" href={r.url} target="_blank" rel="noopener noreferrer"><IconLink size={11}/>open</a> : <span className="helper">—</span>}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Tab 3: Structured trip brief ───
function BriefTab({ plan }){
  if(!plan){
    return <div className="empty">
      <div className="empty-icon"><IconCpu size={20}/></div>
      <h3>No structured data yet</h3>
      <p>Submit a plan to inspect the raw <code style={{fontFamily:'var(--mono)'}}>UserRequest</code> and <code style={{fontFamily:'var(--mono)'}}>CoreResult</code> objects side by side.</p>
    </div>;
  }
  const core = {
    recommendation: plan.recommendation,
    events: plan.top_events,
    sightseeing_spots: plan.sightseeing_spots,
    food_and_drink_spots: plan.food_and_drink_spots,
    itinerary: plan.itinerary_overview,
    warnings: plan.warnings,
    personal_feedback: plan.personal_feedback,
  };
  return (
    <div style={{maxWidth:1400, margin:'0 auto', display:'grid', gridTemplateColumns:'1fr 1fr', gap:16}}>
      <div className="card">
        <div className="section-label"><span className="dot"></span>Input · UserRequest</div>
        <h3 style={{margin:'0 0 12px', fontSize:14}}>Structured request submitted to the planner agent</h3>
        <pre className="json-block" style={{maxHeight:'70vh', padding:'14px', background:'oklch(0.13 0.035 290)', borderRadius:10, border:'1px solid var(--border-soft)'}} dangerouslySetInnerHTML={{__html: jsonHL(plan.request)}}/>
      </div>
      <div className="card">
        <div className="section-label"><span className="dot"></span>Output · CoreResult</div>
        <h3 style={{margin:'0 0 12px', fontSize:14}}>Validated structured plan returned by Dion</h3>
        <pre className="json-block" style={{maxHeight:'70vh', padding:'14px', background:'oklch(0.13 0.035 290)', borderRadius:10, border:'1px solid var(--border-soft)'}} dangerouslySetInnerHTML={{__html: jsonHL(core)}}/>
      </div>
      <div className="card" style={{gridColumn:'1 / -1'}}>
        <div className="section-label"><span className="dot"></span>Schema reference</div>
        <div style={{display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:10, fontSize:12.5, color:'var(--text-2)', fontFamily:'var(--mono)'}}>
          <div><span style={{color:'var(--accent)'}}>UserRequest</span> → user, trip, events, sightseeing, itinerary, delivery</div>
          <div><span style={{color:'var(--accent)'}}>CoreResult</span> → recommendation (≤5), events (≤5), sightseeing_spots, food_and_drink_spots, itinerary, warnings, personal_feedback</div>
          <div><span style={{color:'var(--accent)'}}>UIResult</span> → recommendation, top_events (≤3), sightseeing_spots, food_and_drink_spots, itinerary_overview</div>
        </div>
      </div>
    </div>
  );
}

// ─── Tab 4: Follow-up iterations ───
function IterationTab({ history }){
  if(!history || history.length === 0){
    return <div className="empty">
      <div className="empty-icon"><IconRefresh size={20}/></div>
      <h3>No iterations yet</h3>
      <p>Each plan run and follow-up revision is captured here as a versioned card so you can compare what Dion changed between iterations.</p>
    </div>;
  }
  return (
    <div style={{maxWidth:1400, margin:'0 auto'}}>
      <div className="card" style={{marginBottom:14}}>
        <div className="section-label"><span className="dot"></span>Follow-up iterations</div>
        <h2 className="card-title">Plan history · {history.length} version{history.length===1?'':'s'}</h2>
        <p className="card-sub">Each card is one run of <code style={{fontFamily:'var(--mono)', fontSize:12, background:'var(--surface)', padding:'1px 6px', borderRadius:4}}>run_full_planner_flow</code> or <code style={{fontFamily:'var(--mono)', fontSize:12, background:'var(--surface)', padding:'1px 6px', borderRadius:4}}>run_followup_planner_flow</code>. The newest version is on the right.</p>
      </div>
      <div style={{display:'grid', gridTemplateColumns:`repeat(${Math.min(history.length, 3)}, 1fr)`, gap:14, overflowX:'auto'}}>
        {history.map((iter, idx)=>{
          const prev = idx > 0 ? history[idx-1] : null;
          const dEvents = prev ? iter.event_count - prev.event_count : 0;
          const dSights = prev ? iter.sight_count - prev.sight_count : 0;
          const dFood = prev ? iter.food_count - prev.food_count : 0;
          const isCurrent = idx === history.length - 1;
          return (
            <div key={iter.iteration_id} className="card" style={{
              borderColor: isCurrent ? 'oklch(0.55 0.18 295 / 0.5)' : 'var(--border-soft)',
              boxShadow: isCurrent ? '0 0 0 1px oklch(0.55 0.18 295 / 0.3), 0 12px 30px oklch(0.4 0.18 295 / 0.18)' : 'none'
            }}>
              <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8}}>
                <span className="day-label"><span className="num">{iter.iteration_id.toUpperCase()}</span></span>
                {isCurrent && <span className="meta-tag" style={{color:'oklch(0.85 0.16 155)', borderColor:'oklch(0.5 0.16 155 / 0.4)', background:'oklch(0.3 0.1 155 / 0.2)'}}>current</span>}
              </div>
              <div style={{fontFamily:'var(--mono)', fontSize:11, color:'var(--text-3)', marginBottom:12}}>
                <IconClock size={10} style={{verticalAlign:'-1px', marginRight:4}}/>{iter.created_at}
              </div>
              {iter.followup_message ? (
                <div style={{padding:'10px 12px', background:'oklch(0.22 0.06 295 / 0.3)', border:'1px solid oklch(0.5 0.15 295 / 0.3)', borderRadius:9, marginBottom:12, fontSize:12.5, lineHeight:1.5}}>
                  <div className="section-label" style={{marginBottom:4}}>Follow-up prompt</div>
                  „{iter.followup_message}"
                </div>
              ) : (
                <div style={{padding:'10px 12px', background:'oklch(0.18 0.04 290 / 0.6)', border:'1px dashed var(--border-soft)', borderRadius:9, marginBottom:12, fontSize:12.5, color:'var(--text-3)'}}>
                  Initial plan from form input
                </div>
              )}
              <div className="metrics" style={{gridTemplateColumns:'repeat(3,1fr)'}}>
                <div className="metric"><div className="k">Events</div><div className="v">{iter.event_count}{prev && <Delta n={dEvents}/>}</div></div>
                <div className="metric"><div className="k">Sights</div><div className="v">{iter.sight_count}{prev && <Delta n={dSights}/>}</div></div>
                <div className="metric"><div className="k">Food</div><div className="v">{iter.food_count}{prev && <Delta n={dFood}/>}</div></div>
              </div>
              <div className="section-label" style={{marginTop:14}}>Recommendation snapshot</div>
              <ul style={{margin:0, padding:'0 0 0 16px', fontSize:12.5, color:'var(--text-2)', lineHeight:1.55}}>
                {iter.recommendation_preview.map((s,i)=>(<li key={i} style={{marginBottom:3}}>{s}</li>))}
              </ul>
              <div style={{display:'flex', gap:6, marginTop:12, flexWrap:'wrap'}}>
                {iter.event_names.slice(0,2).map((n,i)=> <span key={i} className="meta-tag" style={{maxWidth:'100%', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>🎫 {n}</span>)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const Delta = ({ n }) => n === 0 ? null : (
  <small style={{color: n>0 ? 'oklch(0.85 0.16 155)' : 'oklch(0.78 0.16 25)', marginLeft:6, fontWeight:600}}>{n>0?'+':''}{n}</small>
);

window.DION_TABS = { VenueTab, BriefTab, IterationTab };
