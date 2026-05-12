# Dion — Animated Brand Mark & Welcome Bubble

Drop-in für die Topbar der Dion Event Planner App. Drei Schritte: CSS einfügen, zwei Komponenten anlegen, in der Topbar mounten.

---

## 1) CSS — in den globalen Stylesheet einfügen

Ersetzt die bisherige `.brand-mark`-Regel (conic-gradient Platzhalter) komplett. Hängt das Bubble- und Keyframes-Setup an.

```css
.brand{ display:flex; align-items:center; gap:12px; position:relative; }

.brand-mark{
  width:44px; height:44px;
  position:relative;
  color: var(--accent);
  filter: drop-shadow(0 4px 16px var(--accent-glow));
  animation: dion-float 4.2s ease-in-out infinite;
  cursor: pointer;
}
.brand-mark svg{ width:100%; height:100%; display:block; overflow:visible; }
.brand-mark .dion-pin{ transform-origin: 26px 36px; animation: dion-bob 2.8s ease-in-out infinite; }
.brand-mark .dion-cup{
  transform-origin: 54px 38px;
  animation: dion-clink 3.6s ease-in-out infinite;
}
.brand-mark .dion-fizz{ transform-origin: 54px 30px; animation: dion-fizz 2.4s ease-out infinite; }
.brand-mark .dion-confetti > *{ animation: dion-confetti 5s ease-in-out infinite; }
.brand-mark .dion-confetti > *:nth-child(2){ animation-delay: -0.6s; animation-duration: 4.4s; }
.brand-mark .dion-confetti > *:nth-child(3){ animation-delay: -1.2s; animation-duration: 5.8s; }
.brand-mark .dion-confetti > *:nth-child(4){ animation-delay: -1.8s; animation-duration: 4.8s; }
.brand-mark .dion-confetti > *:nth-child(5){ animation-delay: -2.4s; animation-duration: 5.4s; }
.brand-mark .dion-confetti > *:nth-child(6){ animation-delay: -3.0s; animation-duration: 4.6s; }
.brand-mark .dion-confetti > *:nth-child(7){ animation-delay: -3.6s; animation-duration: 5.2s; }
.brand-mark .dion-confetti > *:nth-child(8){ animation-delay: -4.2s; animation-duration: 4.8s; }
.brand-mark .dion-wink{ animation: dion-blink 5.5s ease-in-out infinite; transform-origin: center; transform-box: fill-box; }

@keyframes dion-float{
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-2px); }
}
@keyframes dion-bob{
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%      { transform: translateY(-1px) rotate(-1.5deg); }
}
@keyframes dion-clink{
  0%, 70%, 100% { transform: rotate(0deg) translateY(0); }
  78%           { transform: rotate(-10deg) translateY(-1px); }
  86%           { transform: rotate(4deg) translateY(0); }
  94%           { transform: rotate(0deg) translateY(0); }
}
@keyframes dion-fizz{
  0%   { transform: translateY(2px); opacity: 0.4; }
  50%  { transform: translateY(-2px); opacity: 1; }
  100% { transform: translateY(-6px); opacity: 0; }
}
@keyframes dion-confetti{
  0%, 100% { transform: translate(0, 0); opacity: var(--c-op, 1); }
  50%      { transform: translate(var(--c-dx, 1px), var(--c-dy, -2px)); opacity: 0.6; }
}
@keyframes dion-blink{
  0%, 92%, 100% { transform: scaleY(1); }
  95%, 97%      { transform: scaleY(0.1); }
}

/* ---- Welcome speech bubble next to Dion ---- */
.dion-bubble{
  position: absolute;
  top: 50%;
  left: calc(100% + 14px);
  transform: translateY(-50%);
  background: linear-gradient(180deg, oklch(0.26 0.07 295), oklch(0.22 0.06 295));
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 14px;
  width: 280px;
  color: var(--text);
  font-size: 12.5px;
  line-height: 1.45;
  box-shadow: 0 12px 32px oklch(0 0 0 / 0.4), 0 0 0 1px oklch(1 0 0 / 0.04) inset;
  z-index: 60;
  opacity: 0;
  pointer-events: none;
  animation: dion-bubble-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.9s forwards,
             dion-bubble-out 0.4s ease-in 9s forwards;
}
.dion-bubble.is-dismissed{ animation: dion-bubble-out 0.3s ease-in forwards !important; }
.dion-bubble::before{
  content: "";
  position: absolute;
  left: -8px; top: 50%; transform: translateY(-50%) rotate(45deg);
  width: 12px; height: 12px;
  background: oklch(0.26 0.07 295);
  border-left: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  border-radius: 2px;
}
.dion-bubble .bubble-head{
  display:flex; align-items:center; gap:8px;
  font-family: var(--mono); font-size: 10px;
  color: var(--text-3); letter-spacing: 0.14em; text-transform: uppercase;
  margin-bottom: 6px;
}
.dion-bubble .bubble-head .dot{
  width:6px; height:6px; border-radius:50%; background: var(--good);
  box-shadow: 0 0 8px var(--good);
  animation: dion-pulse 1.6s ease-in-out infinite;
}
.dion-bubble .bubble-body{ color: var(--text); }
.dion-bubble .bubble-body b{ color: var(--accent); font-weight:600; }
.dion-bubble .bubble-close{
  position:absolute; top:6px; right:6px;
  width:20px; height:20px; border-radius:6px;
  display:flex; align-items:center; justify-content:center;
  color: var(--text-3); cursor:pointer; pointer-events: auto;
  font-size: 14px; line-height: 1;
  border:0; background:transparent;
}
.dion-bubble .bubble-close:hover{ color: var(--text); background: oklch(1 0 0 / 0.06); }

@keyframes dion-bubble-in{
  0%   { opacity: 0; transform: translateY(-50%) translateX(-6px) scale(0.92); pointer-events:none; }
  100% { opacity: 1; transform: translateY(-50%) translateX(0) scale(1); pointer-events:auto; }
}
@keyframes dion-bubble-out{
  0%   { opacity: 1; transform: translateY(-50%) translateX(0) scale(1); }
  100% { opacity: 0; transform: translateY(-50%) translateX(-4px) scale(0.96); pointer-events:none; }
}
@keyframes dion-pulse{
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.5; transform: scale(0.85); }
}
```

> Erwartete CSS-Variablen im umliegenden Theme: `--accent`, `--accent-glow`, `--border`, `--text`, `--text-3`, `--good`, `--mono`. Falls deine App andere Namen nutzt — einfach mappen.

---

## 2) React-Komponenten

Lege eine neue Datei an, z. B. `components/DionMark.jsx` (oder häng's an einen bestehenden Components-Bundle an).

```jsx
import React from 'react';

export function DionMark(){
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

export function DionBubble(){
  const [dismissed, setDismissed] = React.useState(false);
  const [hidden,    setHidden]    = React.useState(false);

  // nach 10 s komplett aus dem DOM entfernen
  React.useEffect(() => {
    const t = setTimeout(() => setHidden(true), 10000);
    return () => clearTimeout(t);
  }, []);

  if (hidden) return null;

  return (
    <div className={`dion-bubble ${dismissed ? 'is-dismissed' : ''}`} role="status">
      <button className="bubble-close" onClick={() => setDismissed(true)} aria-label="Schließen">×</button>
      <div className="bubble-head"><span className="dot" />Hallo, ich bin Dion</div>
      <div className="bubble-body">
        Dein <b>Event- &amp; Trip-Planer</b>. Sag mir <b>Stadt, Datum und Vibe</b> — ich kuratiere Konzerte, Spots und einen Tag-für-Tag-Plan.
      </div>
    </div>
  );
}
```

---

## 3) In der Topbar mounten

Wo du bisher den Logo-Platzhalter renderst — Marke und Sprechblase einsetzen. `position:relative` auf `.brand` ist über das CSS oben schon gesetzt; die Bubble positioniert sich von dort.

```jsx
<header className="topbar">
  <div className="brand">
    <DionMark />
    <div>
      <div className="brand-name">Dion <span>by BLASTIn</span></div>
      <div className="brand-sub">event_planner.agent · v0.4.2</div>
    </div>
    <DionBubble />
  </div>
  …
</header>
```

---

## Was animiert ist

- **Pin-Figur**: leichtes Auf-und-Ab, minimale Neigung
- **Pokal**: alle ~3,6 s kurzes Anstoßen (Kipp-Bewegung)
- **Sprudel über dem Pokal**: steigt auf und fadet aus, loopt
- **Konfetti** (8 Partikel): jedes mit eigener Phase und Distanz, schwebt unauffällig
- **Zwinkern**: alle 5,5 s schließt sich das linke Auge kurz
- **Sprechblase**: erscheint nach 0,9 s, verschwindet automatisch nach 10 s, oder per × sofort

## Anpassen

- **Bubble-Text** in `DionBubble` direkt im JSX
- **Bubble-Dauer**: `setTimeout(…, 10000)` + die `9s`/`10s` in den CSS-Animationen synchron halten
- **Größe**: `.brand-mark` Breite/Höhe (Default 44 px)
- **Farbe**: `.brand-mark { color: … }` — die SVG nutzt `currentColor`
