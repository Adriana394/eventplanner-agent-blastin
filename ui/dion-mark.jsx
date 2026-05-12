function DionMark(){
  return (
    <div className="brand-mark" title="Dion · dein Eventplaner">
      <svg viewBox="0 0 64 64" aria-label="Dion">
        {/* schwebendes Konfetti rundum */}
        <g className="dion-confetti" fill="currentColor" stroke="currentColor" strokeLinecap="round">
          <circle cx="6"  cy="18" r="1.4" style={{"--c-dx":"1px","--c-dy":"-2px"}} />
          <circle cx="4"  cy="36" r="1.5" opacity="0.85" style={{"--c-dx":"-1px","--c-dy":"-2px"}} />
          <circle cx="14" cy="6"  r="1.2" opacity="0.7"  style={{"--c-dx":"1px","--c-dy":"1px"}} />
          <circle cx="42" cy="58" r="1.4" style={{"--c-dx":"1px","--c-dy":"-1px"}} />
          <circle cx="12" cy="54" r="1.2" opacity="0.75" style={{"--c-dx":"-1px","--c-dy":"-2px"}} />
          <line x1="10" y1="30" x2="7"  y2="33" strokeWidth="2"   style={{"--c-dx":"-1px","--c-dy":"-2px"}} />
          <line x1="20" y1="60" x2="18" y2="57" strokeWidth="1.6" opacity="0.8" style={{"--c-dx":"1px","--c-dy":"-2px"}} />
          <path d="M38 4v2.5M36.8 5.2h2.4" strokeWidth="1.4" fill="none" style={{"--c-dx":"1px","--c-dy":"1px"}} />
        </g>

        {/* Pokal, der gelegentlich anstößt */}
        <g className="dion-cup">
          <path d="M48 28h12l-1.5 7c-.5 2-2.5 3-4.5 3s-4-1-4.5-3z" fill="currentColor"/>
          <path d="M54 38v6M50 44h8" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
        </g>

        {/* Sprudel aus dem Pokal */}
        <g className="dion-fizz" fill="currentColor" stroke="none">
          <circle cx="50" cy="22" r="1.3"/>
          <circle cx="56" cy="18" r="1.5"/>
          <circle cx="60" cy="14" r="1.2" opacity="0.8"/>
          <circle cx="52" cy="12" r="1.1" opacity="0.7"/>
          <path d="M58 24v2.5M57 25.2h2" stroke="currentColor" strokeWidth="1.3" fill="none" strokeLinecap="round"/>
        </g>

        {/* die Pinky-Figur mit Efeu-Krone, Zwinkern + Grinsen */}
        <g className="dion-pin" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" fill="none">
          <path d="M24 22c-7 0-12 5-12 11 0 5 3 8 7 10l4 11a1.5 1.5 0 0 0 3 0l4-11c4-2 7-5 7-10 0-6-6-11-13-11z"/>
          {/* Efeu-Krone */}
          <ellipse cx="16" cy="19" rx="1.8" ry="3.4" transform="rotate(-35 16 19)" fill="currentColor" stroke="none"/>
          <ellipse cx="24" cy="16" rx="1.8" ry="3.8" fill="currentColor" stroke="none"/>
          <ellipse cx="32" cy="19" rx="1.8" ry="3.4" transform="rotate(35 32 19)" fill="currentColor" stroke="none"/>
          {/* Zwinker-Auge */}
          <path className="dion-wink" d="M18 31c1-1 3-1 4 0" strokeWidth="2"/>
          {/* offenes Auge */}
          <circle cx="28" cy="31" r="1.6" fill="currentColor" stroke="none"/>
          {/* schiefes Grinsen */}
          <path d="M19 35c2.5 2 6 2 9 0"/>
        </g>
      </svg>
    </div>
  );
}

function DionBubble(){
  const [dismissed, setDismissed] = React.useState(false);
  const [hidden,    setHidden]    = React.useState(false);

  React.useEffect(() => {
    const t = setTimeout(() => setHidden(true), 10000);
    return () => clearTimeout(t);
  }, []);

  if (hidden) return null;

  return (
    <div className={`dion-bubble ${dismissed ? 'is-dismissed' : ''}`} role="status">
      <button className="bubble-close" onClick={() => setDismissed(true)} aria-label="Schließen">×</button>
      <div className="bubble-head"><span className="dot" />Hey, ich bin Dion</div>
      <div className="bubble-body">
        Verrat mir deine <b>Stadt</b>, dein <b>Wochenende</b> und worauf du <b>Lust</b> hast — ich finde Events und Spots, die zu dir passen.
      </div>
    </div>
  );
}

window.DION_MARK = { DionMark, DionBubble };
