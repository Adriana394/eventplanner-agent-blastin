const { IconEvent, IconLandmark, IconFork, IconSpark, IconLink, IconArrowRight, IconRefresh, IconReset, IconDownload, IconCheck, IconClock, IconWand, IconChat, IconCpu, IconWarn, IconInbox } = window.DION_ICONS;

// ───────── Output helpers ─────────
function formatDateTime(iso){
  if(!iso) return 'Time TBA';
  try{
    const d = new Date(iso);
    return d.toLocaleString('de-DE', { weekday:'short', day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' });
  }catch{ return iso; }
}
function dayLabel(s){
  if(!s) return s;
  const isoMatch = /^\d{4}-\d{2}-\d{2}$/.test(s);
  if(!isoMatch) return s;
  const d = new Date(s + 'T12:00:00');
  if(isNaN(d.getTime())) return s;
  return d.toLocaleDateString('de-DE', { weekday:'long', day:'2-digit', month:'long' });
}

function jsonHighlight(obj){
  const json = JSON.stringify(obj, null, 2);
  return json
    .replace(/("(\\u[0-9a-fA-F]{4}|\\[^u]|[^\\"])*"\s*:)/g, '<span class="k">$1</span>')
    .replace(/: ("(\\u[0-9a-fA-F]{4}|\\[^u]|[^\\"])*")/g, ': <span class="s">$1</span>')
    .replace(/: (-?\d+\.?\d*)/g, ': <span class="n">$1</span>')
    .replace(/: (true|false|null)/g, ': <span class="b">$1</span>');
}

const StatusBar = ({ status, message, elapsed }) => {
  const labels = { idle:'Awaiting Output', running:'Generating', done:'Done', error:'Error' };
  const cssClass = status === 'error' ? 'done' : status;
  const dotStyle = status === 'error' ? { background:'var(--bad)', boxShadow:'0 0 12px oklch(0.7 0.2 25 / 0.4)' } : {};
  return (
    <div className={`status ${cssClass}`}>
      <div className="dot" style={dotStyle}></div>
      <div>
        <div className="label">{labels[status] || status}</div>
        <div className="msg">{message}</div>
      </div>
      {elapsed != null && <div className="timer">{elapsed.toFixed(1)}s</div>}
    </div>
  );
};

const EmptyState = () => (
  <div className="empty">
    <div className="empty-icon"><IconInbox size={20} /></div>
    <h3>No plan generated yet</h3>
    <p>Define the trip on the left, hit <span style={{color:'var(--accent)'}}>Build plan with Dion</span>, and the structured itinerary will populate here.</p>
  </div>
);

const PlanHead = ({ req, ui }) => (
  <>
    <div className="plan-head">
      {req.user.name && <div className="chip">Traveler<strong>{req.user.name}</strong></div>}
      <div className="chip">City<strong>{req.trip.city}</strong></div>
      <div className="chip">Dates<strong>{req.trip.date_start} → {req.trip.date_end}</strong></div>
      <div className="chip">Group<strong>{req.trip.group_size}</strong></div>
      {req.trip.budget && <div className="chip">Budget<strong>{req.trip.budget.min_budget}–{req.trip.budget.max_budget} €</strong></div>}
    </div>
    <div className="metrics">
      <div className="metric"><div className="k">Events</div><div className="v">{ui.top_events.length}<small>/ 3</small></div></div>
      <div className="metric"><div className="k">Sightseeing</div><div className="v">{ui.sightseeing_spots.length}</div></div>
      <div className="metric"><div className="k">Food & Drink</div><div className="v">{ui.food_and_drink_spots.length}</div></div>
    </div>
  </>
);

const Recommendation = ({ rec }) => (
  <div className="recommend">
    <h4><IconSpark /> Dion's Recommendation</h4>
    <ul>{rec.sentences.map((s,i)=> <li key={i}>{s}</li>)}</ul>
  </div>
);

const EventList = ({ items }) => (
  <>
    <div className="block-title"><h4><IconEvent /> Selected Events</h4><span className="count">{items.length} venues</span></div>
    {items.map((e,i)=>(
      <div key={i} className="item">
        <div className="item-head">
          <div style={{minWidth:0, flex:1}}>
            <div className="item-name">{e.name}</div>
            <div className="item-meta">
              <span className="meta-tag">{formatDateTime(e.start_datetime)}</span>
              <span className="meta-tag">@ {e.venue_name}</span>
              <span className={`meta-tag ${(e.price_display||'').toLowerCase()==='free' ? 'free' : 'price'}`}>{e.price_display || 'price tbd'}</span>
            </div>
          </div>
          {e.source_url && <a className="item-link" href={e.source_url} target="_blank" rel="noopener noreferrer"><IconLink size={11}/> ticket</a>}
        </div>
      </div>
    ))}
  </>
);

const SpotList = ({ items, label, icon }) => (
  <>
    <div className="block-title"><h4>{icon} {label}</h4><span className="count">{items.length} spots</span></div>
    {items.map((s,i)=>(
      <div key={i} className="item">
        <div className="item-head">
          <div style={{minWidth:0, flex:1}}>
            <div className="item-name">{s.name}</div>
            <div className="item-meta">
              {s.venue_type && <span className="meta-tag">{s.venue_type}</span>}
              {s.entry_fee_display && <span className={`meta-tag ${s.entry_fee_display==='free' ? 'free':'price'}`}>{s.entry_fee_display}</span>}
              {s.price_hint && <span className="meta-tag price">{s.price_hint}</span>}
              {s.opening_hours && <span className="meta-tag"><IconClock size={10} style={{marginRight:3, verticalAlign:'-1px'}}/>{s.opening_hours}</span>}
            </div>
          </div>
          {s.source_url && <a className="item-link" href={s.source_url} target="_blank" rel="noopener noreferrer"><IconLink size={11}/> source</a>}
        </div>
      </div>
    ))}
  </>
);

const Itinerary = ({ days }) => {
  const [open, setOpen] = React.useState(() => days.map(()=>true));
  return (
    <>
      <div className="block-title"><h4><IconArrowRight /> Trip Flow</h4><span className="count">{days.length} days</span></div>
      {days.map((day, di)=>(
        <div key={di} className="day">
          <div className="day-head" onClick={()=>setOpen(o=>{ const n=[...o]; n[di]=!n[di]; return n; })}>
            <div className="day-label"><span className="num">DAY {di+1}</span>{dayLabel(day.day_label)}</div>
            <span className="day-stops-count">{day.stops.length} stops {open[di] ? '▾' : '▸'}</span>
          </div>
          {open[di] && (
            <div className="day-body">
              {day.stops.map((stop, si)=>(
                <div key={si} className="stop">
                  <div className="stop-time">{stop.start_time || '—'}</div>
                  <div>
                    <div>
                      <span className={`stop-type ${stop.stop_type}`}>{stop.stop_type}</span>
                      <span className="stop-title">{stop.title}</span>
                    </div>
                    {stop.notes && <div className="stop-note">{stop.notes}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </>
  );
};

const Warnings = ({ items }) => items.length === 0 ? null : (
  <>
    <div className="block-title"><h4><IconWarn /> Warnings</h4><span className="count">{items.length}</span></div>
    {items.map((w,i)=>(
      <div key={i} className="item" style={{borderColor:'oklch(0.5 0.16 75 / 0.3)', background:'oklch(0.22 0.06 75 / 0.15)'}}>
        <div style={{fontSize:12.5, lineHeight:1.5, color:'oklch(0.9 0.05 75)'}}>{w}</div>
      </div>
    ))}
  </>
);

const PersonalNote = ({ items }) => items.length === 0 ? null : (
  <>
    <div className="block-title"><h4><IconChat /> Dion's Personal Note</h4></div>
    {items.map((n,i)=>(
      <div key={i} className="item" style={{borderColor:'oklch(0.5 0.15 295 / 0.3)'}}>
        <div style={{fontSize:13, lineHeight:1.5, color:'var(--text)'}}>{n}</div>
      </div>
    ))}
  </>
);

const ReportFile = ({ path, sizeKb }) => {
  const filename = path ? path.split('/').pop() : 'plan.md';
  return (
    <div className="file-card">
      <div className="file-icon"></div>
      <div className="file-meta">
        <div className="file-name">{filename}</div>
        <div className="file-size">{sizeKb} KB · saved at {path}</div>
      </div>
      <button className="file-dl"><IconDownload size={12} style={{marginRight:5, verticalAlign:'-2px'}}/>Download</button>
    </div>
  );
};

const StructuredAccordion = ({ title, data }) => (
  <details className="accordion">
    <summary>{title}</summary>
    <pre className="json-block" dangerouslySetInnerHTML={{__html: jsonHighlight(data)}}/>
  </details>
);

const FollowUpPanel = ({ value, onChange, onSubmit, onReset, busy }) => (
  <div className="followup">
    <div style={{display:'flex', alignItems:'center', gap:8, marginBottom:8}}>
      <IconWand /><strong style={{fontSize:13.5}}>Follow-up</strong>
      <span style={{fontFamily:'var(--mono)', fontSize:10.5, color:'var(--text-3)', marginLeft:'auto'}}>iteration #2</span>
    </div>
    <div style={{fontSize:12.5, color:'var(--text-3)', marginBottom:10, lineHeight:1.5}}>
      Ask Dion to revise the current plan instead of creating a new one. Or change the form values and re-submit.
    </div>
    <textarea
      value={value} onChange={e=>onChange(e.target.value)}
      placeholder="z. B. Tausch das Restaurant am Tag 2 gegen etwas Asiatisches und reduziere Sightseeing am Sonntag."
      maxLength={320}
    />
    <div className="followup-row">
      <span className="helper">{value.length}/320</span>
      <button className="btn btn-ghost" onClick={onReset}><IconReset size={13}/>Start fresh</button>
      <button className="btn btn-primary" onClick={onSubmit} disabled={busy}>
        <IconRefresh size={13}/>{busy ? 'Updating…' : 'Update plan'}
      </button>
    </div>
  </div>
);

window.DION_OUT = { StatusBar, EmptyState, PlanHead, Recommendation, EventList, SpotList, Itinerary, Warnings, PersonalNote, ReportFile, StructuredAccordion, FollowUpPanel };
