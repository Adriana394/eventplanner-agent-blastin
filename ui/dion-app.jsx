const { AVAILABLE_MODELS, DEFAULT_MODEL, TIME_PREF, PLANNING_MODES, SIGHTSEEING_MODES, LANGUAGES, GROUP_SIZES, DEMO_PLAN, DEMO_CASES } = window.DION_DATA;
const { IconEvent, IconLandmark, IconFork, IconSpark, IconArrowRight, IconRefresh, IconReset, IconCheck, IconCpu, IconWand, IconChat } = window.DION_ICONS;
const { StatusBar, EmptyState, PlanHead, Recommendation, EventList, SpotList, Itinerary, Warnings, PersonalNote, ReportFile, StructuredAccordion, FollowUpPanel } = window.DION_OUT;
const { VenueTab, BriefTab, IterationTab } = window.DION_TABS;
const { DionMark, DionBubble } = window.DION_MARK;

const DEFAULT_FORM = {
  user_name: '', city: '', country: '',
  date_start: '2026-05-15', date_end: '2026-05-17',
  include_last_day: true, planning_mode: 'Full Trip',
  group_size: 2, min_budget: '', max_budget: '',
  vibe: '', categories: '', time_pref: 'No preference', free_only: false,
  sightseeing_interests: '', sightseeing_mode: 'No preference', sightseeing_free_only: false,
  must_avoid: '',
  user_notes: '',
  language: 'English'
};

const DEMO_FORM = {
  user_name: 'Adriana', city: 'Berlin', country: 'Germany',
  date_start: '2026-05-15', date_end: '2026-05-17',
  include_last_day: true, planning_mode: 'Full Trip',
  group_size: 2, min_budget: '200', max_budget: '600',
  vibe: 'techno, underground', categories: 'club, concert', time_pref: 'Night', free_only: false,
  sightseeing_interests: 'street art, viewpoints, history', sightseeing_mode: 'Mixed', sightseeing_free_only: false,
  must_avoid: 'museums, luxury dining',
  user_notes: 'Two of us, one elegant highlight, one big late night. Skip touristy Mitte.',
  language: 'English'
};

const TABS = [
  { id:'planner', label:'Planner', icon:<IconWand size={13}/> },
  { id:'venue',   label:'Concrete venue planning', icon:<IconLandmark size={13}/> },
  { id:'brief',   label:'Structured trip brief', icon:<IconCpu size={13}/> },
  { id:'iter',    label:'Follow-up iterations', icon:<IconRefresh size={13}/> },
];

const PROGRESS_STEPS_I18N = {
  en: [
    { pct:10, msg:'Starting MCP servers…' },
    { pct:30, msg:'Searching for events and places…' },
    { pct:55, msg:'Building the plan…' },
    { pct:75, msg:'Validating and refining the plan…' },
    { pct:90, msg:'Writing the report…' },
    { pct:100, msg:'Plan and report created successfully.' },
  ],
  de: [
    { pct:10, msg:'MCP-Server werden gestartet…' },
    { pct:30, msg:'Events und Orte werden gesucht…' },
    { pct:55, msg:'Plan wird erstellt…' },
    { pct:75, msg:'Plan wird geprüft und verfeinert…' },
    { pct:90, msg:'Bericht wird geschrieben…' },
    { pct:100, msg:'Plan und Bericht erfolgreich erstellt.' },
  ],
};

function App(){
  const [tab, setTab] = React.useState('planner');
  const [model, setModel] = React.useState(DEFAULT_MODEL);
  const [lang, setLang] = React.useState('en');
  const [form, setForm] = React.useState(DEFAULT_FORM);
  const [scope, setScope] = React.useState({ events:true, sightseeing:true, food:true });
  const [followup, setFollowup] = React.useState('');
  const [status, setStatus] = React.useState({ state:'idle', msg:'No plan generated yet', elapsed:null });
  const [plan, setPlan] = React.useState(null);
  const [coreResultJson, setCoreResultJson] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [history, setHistory] = React.useState([]);

  const set = (k) => (e) => {
    const v = e?.target?.type === 'checkbox' ? e.target.checked : (e?.target ? e.target.value : e);
    setForm(f => ({ ...f, [k]: v }));
  };
  const setScopeKey = (k) => () => setScope(s => ({ ...s, [k]: !s[k] }));

  const buildApiRequest = () => ({
    user_name: form.user_name,
    city: form.city,
    country: form.country,
    date_start: form.date_start,
    date_end: form.date_end,
    include_last_day: form.include_last_day,
    planning_mode: form.planning_mode,
    events_enabled: scope.events,
    sightseeing_enabled: scope.sightseeing,
    food_drink_enabled: scope.food,
    group_size: form.group_size,
    min_budget: form.min_budget ? parseFloat(form.min_budget) : null,
    max_budget: form.max_budget ? parseFloat(form.max_budget) : null,
    vibe: form.vibe,
    categories: form.categories,
    time_pref: form.time_pref,
    free_only: form.free_only,
    sightseeing_interests: form.sightseeing_interests,
    sightseeing_mode: form.sightseeing_mode,
    sightseeing_free_only: form.sightseeing_free_only,
    must_avoid: form.must_avoid,
    user_notes: form.user_notes,
    language: form.language,
    model,
  });

  const runPlan = async (isFollowUp=false) => {
    setBusy(true);
    const t0 = performance.now();
    const elapsed = () => parseFloat(((performance.now() - t0) / 1000).toFixed(1));

    const isDe = form.language === 'Deutsch';
    const progressSteps = PROGRESS_STEPS_I18N[isDe ? 'de' : 'en'];
    setStatus({ state:'running', msg: isFollowUp ? (isDe ? 'Dion überarbeitet den aktuellen Plan…' : 'Dion is revising the current plan…') : (isDe ? 'Dion erstellt den Plan…' : 'Dion is building the plan…'), elapsed: 0 });

    // Advance progress steps on a timer while the API call runs in parallel
    let stepIdx = 0;
    const stepTimer = setInterval(() => {
      stepIdx = Math.min(stepIdx + 1, progressSteps.length - 2);
      setStatus({ state:'running', msg: progressSteps[stepIdx].msg, elapsed: elapsed() });
    }, 18000);

    try {
      let data;
      if (isFollowUp) {
        const resp = await fetch('/api/followup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            plan_request: buildApiRequest(),
            core_result_json: coreResultJson,
            followup_message: followup,
          }),
        });
        if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail || 'Follow-up failed'); }
        data = await resp.json();
      } else {
        const resp = await fetch('/api/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildApiRequest()),
        });
        if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail || 'Planning failed'); }
        data = await resp.json();
      }

      clearInterval(stepTimer);
      const nextPlan = data.plan;
      setPlan(nextPlan);
      setCoreResultJson(data.core_result_json);
      setHistory(h => [...h, {
        iteration_id: 'v' + (h.length + 1),
        created_at: new Date().toISOString().slice(0, 19).replace('T', ' '),
        followup_message: isFollowUp ? followup : null,
        event_count: nextPlan.top_events.length,
        sight_count: nextPlan.sightseeing_spots.length,
        food_count: nextPlan.food_and_drink_spots.length,
        recommendation_preview: (nextPlan.recommendation?.sentences || []).slice(0, 3),
        event_names: nextPlan.top_events.map(e => e.name),
      }]);
      setStatus({ state:'done', msg: isFollowUp ? (isDe ? 'Plan erfolgreich aktualisiert.' : 'Plan updated successfully.') : (isDe ? 'Plan und Bericht erfolgreich erstellt.' : 'Plan and report created successfully.'), elapsed: elapsed() });
    } catch(err) {
      clearInterval(stepTimer);
      setStatus({ state:'error', msg: err.message, elapsed: elapsed() });
    }
    setBusy(false);
  };

  const reset = () => {
    setPlan(null); setCoreResultJson(null); setFollowup('');
    setStatus({ state:'idle', msg:'No plan generated yet', elapsed:null });
    setForm(DEFAULT_FORM);
    setScope({ events:true, sightseeing:true, food:true });
    setHistory([]);
  };

  const fillDemo = () => setForm(DEMO_FORM);

  const loadDemoCase = (caseId) => {
    if(!caseId) return;
    const c = DEMO_CASES.find(x => x.id === caseId);
    if(!c) return;
    setForm({ ...DEFAULT_FORM, ...c.form });
    setScope({ ...c.scope });
    if(c.followup_message) setFollowup(c.followup_message);
  };

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <div>
            <div className="brand-name">Dion <span style={{color:'var(--text-3)', fontWeight:500}}>by BLASTIn</span></div>
            <div className="brand-sub">event_planner.agent · v0.4.2</div>
          </div>
        </div>

        <nav className="tabs">
          {TABS.map(t => (
            <div key={t.id} className={`tab ${tab===t.id?'active':''}`} onClick={()=>setTab(t.id)}>
              <span className="row">{t.icon}<span style={{marginLeft:6}}>{t.label}</span></span>
            </div>
          ))}
        </nav>

        <div className="topbar-right">
          <div className="model-select" title="Planner LLM (via OpenRouter)">
            <span className="lbl">Model</span>
            <select value={model} onChange={e=>setModel(e.target.value)}>
              {AVAILABLE_MODELS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="lang-toggle">
            <button className={lang==='en'?'active':''} onClick={()=>setLang('en')}>EN</button>
            <button className={lang==='de'?'active':''} onClick={()=>setLang('de')}>DE</button>
          </div>
        </div>
      </header>

      {tab !== 'planner' && (
        <div style={{padding:'24px'}}>
          {tab === 'venue' && <VenueTab plan={plan}/>}
          {tab === 'brief' && <BriefTab plan={plan}/>}
          {tab === 'iter' && <IterationTab history={history}/>}
        </div>
      )}

      {tab === 'planner' && <div className="shell">
        {/* ─── LEFT: form ─── */}
        <div>
          <div className="card" style={{marginBottom:18}}>
            <div className="section-label"><span className="dot"></span>Planning Scope</div>
            <h2 className="card-title">Choose what Dion should include</h2>
            <p className="card-sub">Toggle categories on/off — they update the request scope and hide the related Direction panels below.</p>
            <div className="scope-grid">
              <ScopeCard active={scope.events} onClick={setScopeKey('events')} icon={<IconEvent size={16}/>}
                title="Events" desc="Concerts, shows, club nights, ticketed experiences." />
              <ScopeCard active={scope.sightseeing} onClick={setScopeKey('sightseeing')} icon={<IconLandmark size={16}/>}
                title="Sightseeing" desc="Landmarks, viewpoints, museums and city highlights." />
              <ScopeCard active={scope.food} onClick={setScopeKey('food')} icon={<IconFork size={16}/>}
                title="Food & Drinks" desc="Restaurants, bars, cafés tuned to the trip's mood." />
            </div>
          </div>

          <div className="card">
            <div className="cmd-bar"><span className="arrow">▸</span>POST /planner/run<span style={{flex:1}}/><span>scope: {[scope.events&&'events',scope.sightseeing&&'sightseeing',scope.food&&'food'].filter(Boolean).join(', ') || 'none'}</span></div>
            <div className="section-label"><span className="dot"></span>Plan the trip</div>
            <h2 className="card-title">Trip brief</h2>
            <p className="card-sub">Fill out only the parts that match the active planning scope. Required fields are marked.</p>

            <div className="form-section">
              <div className="form-grid">
                <Field label="Name"><input className="input" placeholder="e.g. Adriana" value={form.user_name} onChange={set('user_name')}/></Field>
                <Field label={<>City <span className="req">*</span></>}><input className="input" placeholder="e.g. Berlin" value={form.city} onChange={set('city')}/></Field>
                <Field label="Country"><input className="input" placeholder="e.g. Germany" value={form.country} onChange={set('country')}/></Field>
                <Field label="Output language">
                  <select className="select" value={form.language} onChange={set('language')}>{LANGUAGES.map(l => <option key={l}>{l}</option>)}</select>
                </Field>
              </div>
            </div>

            <div className="form-section">
              <div className="section-label" style={{marginTop:0}}>Trip setup</div>
              <div className="form-grid">
                <Field label={<>Start date <span className="req">*</span></>}>
                  <input className="input" type="date" value={form.date_start} onChange={set('date_start')}/>
                </Field>
                <Field label={<>End date <span className="req">*</span></>}>
                  <input className="input" type="date" value={form.date_end} onChange={set('date_end')}/>
                </Field>
                <Field label="Group size">
                  <select className="select" value={form.group_size} onChange={e=>setForm(f=>({...f, group_size:Number(e.target.value)}))}>
                    {GROUP_SIZES.map(n => <option key={n} value={n}>{n} {n===1?'person':'people'}</option>)}
                  </select>
                </Field>
                <Field label="Planning mode">
                  <select className="select" value={form.planning_mode} onChange={set('planning_mode')}>{PLANNING_MODES.map(m => <option key={m}>{m}</option>)}</select>
                </Field>
              </div>
              <div className="checkbox-row" style={{marginTop:10}}>
                <input id="last-day" type="checkbox" className="toggle" checked={form.include_last_day} onChange={set('include_last_day')}/>
                <label htmlFor="last-day">Include last trip day in itinerary</label>
              </div>
            </div>

            <div className="form-section">
              <div className="section-label" style={{marginTop:0}}>Budget <span className="helper" style={{textTransform:'none', letterSpacing:0, marginLeft:6}}>(EUR · provide at least one)</span></div>
              <div className="form-grid">
                <Field label="Minimum"><input className="input" type="number" min="0" step="10" placeholder="0" value={form.min_budget} onChange={set('min_budget')}/></Field>
                <Field label="Maximum"><input className="input" type="number" min="0" step="10" placeholder="600" value={form.max_budget} onChange={set('max_budget')}/></Field>
              </div>
            </div>

            <div className="form-section">
              <div className="section-label" style={{marginTop:0}}>Constraints</div>
              <Field label="Avoid list" hint="Comma-separated. Items, venue types or vibes Dion should skip.">
                <input className="input" placeholder="e.g. museums, luxury dining, family events" value={form.must_avoid} onChange={set('must_avoid')}/>
              </Field>
            </div>

            {/* Direction panels */}
            <div className="form-section">
              <div className="section-label" style={{marginTop:0}}>Direction</div>
              <div className="direction-grid">
                <div className={`dir-card ${!scope.events ? 'disabled':''}`}>
                  <div className="dir-head"><IconEvent size={14}/>Event Direction <span className="pill">events</span></div>
                  <div style={{display:'grid', gap:12}}>
                    <Field label="Desired vibe"><input className="input" placeholder="e.g. elegant, energetic, underground, classical" value={form.vibe} onChange={set('vibe')}/></Field>
                    <Field label="Event categories"><input className="input" placeholder="e.g. concert, club, theatre" value={form.categories} onChange={set('categories')}/></Field>
                    <div className="row-2">
                      <Field label="Preferred time">
                        <select className="select" value={form.time_pref} onChange={set('time_pref')}>{TIME_PREF.map(t => <option key={t}>{t}</option>)}</select>
                      </Field>
                      <Field label="Free only?">
                        <select className="select" value={form.free_only?'Yes':'No'} onChange={e=>setForm(f=>({...f, free_only:e.target.value==='Yes'}))}>
                          <option>No</option><option>Yes</option>
                        </select>
                      </Field>
                    </div>
                  </div>
                </div>
                <div className={`dir-card ${!scope.sightseeing ? 'disabled':''}`}>
                  <div className="dir-head"><IconLandmark size={14}/>City Direction <span className="pill">sightseeing</span></div>
                  <div style={{display:'grid', gap:12}}>
                    <Field label="Sightseeing interests"><input className="input" placeholder="e.g. landmarks, viewpoints, art" value={form.sightseeing_interests} onChange={set('sightseeing_interests')}/></Field>
                    <Field label="Sightseeing mode">
                      <select className="select" value={form.sightseeing_mode} onChange={set('sightseeing_mode')}>{SIGHTSEEING_MODES.map(s => <option key={s}>{s}</option>)}</select>
                    </Field>
                    <Field label="Free only?">
                      <select className="select" value={form.sightseeing_free_only?'Yes':'No'} onChange={e=>setForm(f=>({...f, sightseeing_free_only:e.target.value==='Yes'}))}>
                        <option>No</option><option>Yes</option>
                      </select>
                    </Field>
                  </div>
                </div>
              </div>
            </div>

            <div className="form-section">
              <div className="section-label" style={{marginTop:0}}>Output & Notes</div>
              <Field label="Short planning note" hint={`${form.user_notes.length}/220 characters`}>
                <textarea className="textarea" maxLength={220} placeholder="e.g. We want one elegant highlight and one memorable late-night venue." value={form.user_notes} onChange={set('user_notes')}/>
              </Field>
            </div>

            <div className="cta-row">
              <span className="helper">↵ Submit · ⎋ reset</span>
              <div style={{display:'flex', gap:10, alignItems:'center', flexWrap:'wrap'}}>
                <div className="demo-picker" title="Load a regression case from DEMO_CASES.md">
                  <span className="lbl">Demo case</span>
                  <select onChange={e=>{ loadDemoCase(e.target.value); e.target.value=''; }} defaultValue="">
                    <option value="" disabled>Load a regression case…</option>
                    {DEMO_CASES.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                  </select>
                </div>
                <button className="btn btn-primary" onClick={()=>runPlan(false)} disabled={busy}>
                  <IconWand size={14}/>Build plan with Dion
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ─── RIGHT: output ─── */}
        <div className="output">
          <StatusBar status={status.state} message={status.msg} elapsed={status.elapsed}/>

          {!plan && status.state !== 'running' && <EmptyState/>}

          {plan && (
            <>
              <div className="card">
                <div className="section-label"><span className="dot"></span>Result Block</div>
                <PlanHead req={plan.request} ui={plan}/>
                <Recommendation rec={plan.recommendation}/>
                <EventList items={plan.top_events}/>
                <SpotList items={plan.sightseeing_spots} label="City Highlights" icon={<IconLandmark/>}/>
                <SpotList items={plan.food_and_drink_spots} label="Food & Drinks" icon={<IconFork/>}/>
                <Itinerary days={plan.itinerary_overview}/>
                <Warnings items={plan.warnings}/>
                <PersonalNote items={plan.personal_feedback}/>
              </div>

              <div className="card tight">
                <div className="section-label"><span className="dot"></span>Saved Report</div>
                <ReportFile path={plan.saved_report_path} sizeKb={plan.report_size_kb}/>
              </div>

              <FollowUpPanel
                value={followup}
                onChange={setFollowup}
                onSubmit={()=>runPlan(true)}
                onReset={reset}
                busy={busy}
                form={form}
                onFormChange={set}
              />

              <div className="card tight">
                <div className="section-label"><span className="dot"></span>Structured data</div>
                <StructuredAccordion title="Show structured request" data={plan.request}/>
                <div style={{height:0}}/>
                <StructuredAccordion title="Show structured core result" data={{
                  recommendation: plan.recommendation,
                  events: plan.top_events,
                  sightseeing_spots: plan.sightseeing_spots,
                  food_and_drink_spots: plan.food_and_drink_spots,
                  itinerary: plan.itinerary_overview,
                  warnings: plan.warnings,
                  personal_feedback: plan.personal_feedback
                }}/>
                <div style={{height:0}}/>
                <StructuredAccordion title="Show structured report data" data={{
                  title: `${plan.request.trip.city} — ${plan.request.trip.date_start} → ${plan.request.trip.date_end}`,
                  saved_report_path: plan.saved_report_path,
                  recommendation: plan.recommendation,
                  sections: plan.markdown_report_sections || [],
                }}/>
              </div>
            </>
          )}
        </div>
      </div>}

      <div className="dion-fab">
        <DionMark />
        <DionBubble />
      </div>
    </>
  );
}

const ScopeCard = ({ active, onClick, icon, title, desc }) => (
  <div className={`scope ${active?'active':''}`} onClick={onClick}>
    <div className="scope-head">
      <div className="scope-icon">{icon}</div>
      <input type="checkbox" className="toggle" checked={active} onChange={()=>{}} onClick={e=>e.stopPropagation()}/>
    </div>
    <div className="scope-title">{title}</div>
    <div className="scope-desc">{desc}</div>
  </div>
);

const Field = ({ label, hint, children }) => (
  <div className="field">
    <div className="field-label">{label}</div>
    {children}
    {hint && <div className="field-hint">{hint}</div>}
  </div>
);

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
