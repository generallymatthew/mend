const C0 = {
  bg: '#F6F1E7', room: '#e9dec6', card: '#f9f4ed', ink: '#17372E', mute: '#65645f', line: '#dfddd6',
  acc: '#F3829A', acc1: '#fbe9ed', acc2: '#fac7d2', acc7: '#8c0d28', acc9: '#410b17',
  blu: '#17372E', blu1: '#eef7f4', blu2: '#d4ede6', blu9: '#19342c',
  pri: '#e6b8a4', pri9: '#5a3325', warn: '#c0765e',
};
const HF = '"Manrope", system-ui, sans-serif';
const BF = '"Manrope", system-ui, sans-serif';

const MOTION = {
  enter: (s, d = 0.6) => animate({ from: 0, to: 1, start: s, end: s + d, ease: Easing.easeOutCubic }),
  pop: (s, d = 0.55) => animate({ from: 0, to: 1, start: s, end: s + d, ease: Easing.easeOutBack }),
  draw: (s, d = 0.8) => animate({ from: 0, to: 1, start: s, end: s + d, ease: Easing.easeInOutCubic }),
};
const win = (T, a, b, f = 0.45) => Math.min(MOTION.enter(a, f)(T), 1 - MOTION.enter(b - f, f)(T));
const kf = (keys, T, i) => interpolate(keys.map(k => k[0]), keys.map(k => k[i]), Easing.easeInOutCubic)(T);
const abs = (x, y, w, h) => ({ position: 'absolute', left: x, top: y, width: w, height: h });


function Face({ s, bg, skin, hair, shirt, long, mood }) {
  const m = clamp(mood, 0, 1);
  const curve = -5 + 11 * m, brow = 3.5 * (1 - m);
  return (
    <svg width={s} height={s} viewBox="0 0 100 100" style={{ display: 'block', borderRadius: '50%' }}>
      <circle cx="50" cy="50" r="50" fill={bg}></circle>
      {long && <path d="M26 52 Q24 20 50 19 Q76 20 74 52 L76 84 L24 84 Z" fill={hair}></path>}
      <ellipse cx="50" cy="104" rx="36" ry="26" fill={shirt}></ellipse>
      <rect x="44" y="64" width="12" height="14" rx="5" fill={skin}></rect>
      <ellipse cx="50" cy="48" rx="20" ry="23" fill={skin}></ellipse>
      {long
        ? <path d="M29 50 Q28 21 50 21 Q72 21 71 50 Q67 33 52 30 Q40 34 29 50Z" fill={hair}></path>
        : <path d="M29 45 Q28 21 50 21 Q72 21 71 45 Q66 31 50 31 Q35 31 29 45Z" fill={hair}></path>}
      <circle cx="42" cy="49" r="2.3" fill="#2a2d2c"></circle>
      <circle cx="58" cy="49" r="2.3" fill="#2a2d2c"></circle>
      <path d={`M37 ${42 - brow * 0.2} L46 ${42 + brow}`} stroke={hair} strokeWidth="2.4" strokeLinecap="round"></path>
      <path d={`M63 ${42 - brow * 0.2} L54 ${42 + brow}`} stroke={hair} strokeWidth="2.4" strokeLinecap="round"></path>
      <path d={`M43 60 Q50 ${60 + curve} 57 60`} fill="none" stroke="#6b3a2c" strokeWidth="2.4" strokeLinecap="round"></path>
    </svg>
  );
}

function Avatar({ x, y, s, o, fill, ink, letter, name, face }) {
  return (
    <div style={{ position: 'absolute', left: x - s / 2, top: y - s / 2, width: s, height: s, opacity: o }}>
      <div style={{ width: s, height: s, borderRadius: '50%', background: fill, color: ink, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: s * 0.42, boxShadow: '0 12px 30px rgba(42,45,44,0.10)', overflow: 'hidden' }}>{face ? <Face s={s} bg={fill} {...face} /> : letter}</div>
      <div style={{ position: 'absolute', top: s + 14, left: -100, right: -100, textAlign: 'center', fontFamily: BF, fontWeight: 600, fontSize: 28, color: C0.ink }}>{name}</div>
    </div>
  );
}

function Pill({ x, y, w, o, sc = 1, bg, ink, children, border, size = 28 }) {
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, opacity: o, transform: `scale(${sc})`, transformOrigin: 'left center', background: bg, color: ink, border: border || 'none', borderRadius: 999, padding: '20px 30px', fontFamily: BF, fontWeight: 600, fontSize: size, boxSizing: 'border-box' }}>{children}</div>
  );
}

function Room() {
  const { T, CUES } = useComposition();
  const o = 1 - MOTION.enter(CUES.Close - 0.2, 0.6)(T);
  return <div style={{ ...abs(80, 170, 1760, 770), borderRadius: 56, background: C0.room, opacity: o }}></div>;
}

function Rail() {
  const { T, CUES: C } = useComposition();
  const steps = [['Conflict', 0], ['Private 1:1', C.Book], ['Reflect', C.Reflect], ['Decide', C.Decide], ['Resolve', C.HandleIt], ['Check in', C.CheckIn]];
  let active = 0; steps.forEach((s, i) => { if (T >= s[1]) active = i; });
  const o = MOTION.enter(0.2)(T) * (1 - MOTION.enter(C.Close - 0.2, 0.5)(T));
  return (
    <div style={{ position: 'absolute', left: 120, right: 120, top: 972, height: 60, display: 'flex', alignItems: 'center', gap: 18, opacity: o }}>
      {steps.map((s, i) => (
        <React.Fragment key={i}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 22, height: 22, borderRadius: '50%', background: i <= active ? C0.acc : C0.line, transform: `scale(${i === active ? 1.25 : 1})` }}></div>
            <span style={{ fontFamily: BF, fontSize: 24, fontWeight: i === active ? 700 : 500, color: i === active ? C0.ink : C0.mute }}>{s[0]}</span>
          </div>
          {i < steps.length - 1 && <div style={{ flex: 1, height: 4, borderRadius: 4, background: i < active ? C0.acc2 : C0.line }}></div>}
        </React.Fragment>
      ))}
    </div>
  );
}

function People() {
  const { T, CUES: C } = useComposition();
  const sam = [
    [0, 760, 540, 240], [C.Hesitate - 0.2, 760, 540, 240], [C.Hesitate + 0.6, 960, 470, 260],
    [C.Book - 0.3, 960, 470, 260], [C.Book + 0.5, 330, 560, 210],
    [C.Decide - 0.3, 330, 560, 210], [C.Decide + 0.5, 960, 300, 160],
    [C.HandleIt - 0.2, 960, 300, 160], [C.HandleIt + 0.6, 1220, 540, 220],
    [C.HandleIt + 4.2, 1220, 540, 220], [C.HandleIt + 5, 1290, 540, 220],
    [C.Support - 0.3, 1290, 540, 220], [C.Support + 0.5, 1260, 720, 180],
    [C.CheckIn - 0.3, 1260, 720, 180], [C.CheckIn + 0.5, 520, 540, 230],
  ];
  const pri = [
    [0, 1160, 540, 240], [C.Hesitate - 0.2, 1160, 540, 240], [C.Hesitate + 0.6, 1480, 470, 200], [C.Book, 1480, 470, 200], [C.Book + 0.01, 1680, 540, 220],
    [C.HandleIt + 4.2, 1680, 540, 220], [C.HandleIt + 5, 1590, 540, 220],
    [C.Support - 0.3, 1590, 540, 220], [C.Support + 0.5, 1740, 720, 180],
  ];
  const samO = MOTION.enter(0.1)(T) * (1 - MOTION.enter(C.Close - 0.2, 0.5)(T));
  const priO = interpolate(
    [0.2, 0.7, C.Hesitate + 0.3, C.Hesitate + 0.9, C.Book - 0.2, C.Book + 0.3, C.HandleIt + 3.8, C.HandleIt + 4.4, C.CheckIn - 0.4, C.CheckIn + 0.2],
    [0, 1, 1, 0.28, 0.28, 0, 0, 1, 1, 0], Easing.easeInOutCubic)(T);
  const ez = Easing.easeInOutCubic;
  const samMood = interpolate([0.8, 1.6, C.Hesitate, C.Reflect + 4, C.Reflect + 6, C.HandleIt + 4.8, C.HandleIt + 6, C.Support, C.Support + 1, C.CheckIn + 3.4, C.CheckIn + 4], [0.5, 0, 0.1, 0.3, 0.7, 0.7, 1, 1, 0.6, 0.6, 1], ez)(T);
  const priMood = interpolate([0.8, 1.6, C.HandleIt + 4.6, C.HandleIt + 5.8, C.Support, C.Support + 1], [0.5, 0, 0.3, 1, 1, 0.6], ez)(T);
  const mendO = win(T, C.Support + 2.0, C.CheckIn);
  const mendS = 170 * (0.6 + 0.4 * MOTION.pop(C.Support + 2.0)(T));
  const d1 = MOTION.draw(C.Support + 2.5)(T), d2 = MOTION.draw(C.Support + 2.8)(T);
  return (
    <React.Fragment>
      <svg width="1920" height="1080" style={{ position: 'absolute', left: 0, top: 0, opacity: mendO }}>
        <line x1="1500" y1="380" x2={1500 + (1260 - 1500) * d1} y2={380 + (720 - 380) * d1} stroke={C0.acc2} strokeWidth="10" strokeLinecap="round"></line>
        <line x1="1500" y1="380" x2={1500 + (1740 - 1500) * d2} y2={380 + (720 - 380) * d2} stroke={C0.acc2} strokeWidth="10" strokeLinecap="round"></line>
        <line x1="1260" y1="720" x2={1260 + 480 * MOTION.draw(C.Support + 3.4)(T)} y2="720" stroke={C0.acc2} strokeWidth="10" strokeLinecap="round" strokeDasharray="2 22"></line>
      </svg>
      <Avatar x={1500} y={380} s={mendS} o={mendO} fill={C0.acc} ink="#ffffff" letter="M" name="Mend" />
      <Avatar face={{ skin: '#a8704f', hair: '#231b18', shirt: C0.acc7, long: true, mood: priMood }} x={kf(pri, T, 1)} y={kf(pri, T, 2)} s={kf(pri, T, 3)} o={priO} fill={C0.pri} ink={C0.pri9} letter="P" name="Priya" />
      <Avatar face={{ skin: '#e2b08c', hair: '#4a3426', shirt: '#4e5c86', long: false, mood: samMood }} x={kf(sam, T, 1)} y={kf(sam, T, 2)} s={kf(sam, T, 3)} o={samO} fill={C0.blu} ink="#ffffff" letter="S" name="Sam" />
    </React.Fragment>
  );
}

function Conflict() {
  const { T, CUES: C } = useComposition();
  const o = win(T, 0.6, C.Hesitate + 0.4, 0.3);
  const d = MOTION.draw(0.9, 0.7)(T);
  const shake = T > 1.6 && T < C.Hesitate ? Math.sin(T * 26) * 4 * (1 - MOTION.enter(1.6, 1.4)(T)) : 0;
  const pts = '890,520 930,470 960,560 995,480 1030,540';
  return (
    <svg width="1920" height="1080" style={{ position: 'absolute', left: 0, top: shake, opacity: o }}>
      <polyline points={pts} fill="none" stroke={C0.warn} strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - d}></polyline>
    </svg>
  );
}

function Hesitate() {
  const { T, CUES: C } = useComposition();
  const h = C.Hesitate;
  const out = 1 - MOTION.enter(C.Book - 0.2, 0.4)(T);
  const opt = (label, x, at) => {
    const a = MOTION.pop(h + at)(T), s = MOTION.draw(h + at + 1.0, 0.5)(T);
    return (
      <div style={{ position: 'absolute', left: x, top: 740, width: 480, opacity: a * out * (1 - 0.45 * s), transform: `translateY(${(1 - a) * 30}px)` }}>
        <div style={{ position: 'relative', background: C0.card, borderRadius: 999, padding: '22px 32px', fontFamily: BF, fontWeight: 600, fontSize: 30, color: C0.ink, textAlign: 'center', boxShadow: '0 8px 24px rgba(42,45,44,0.08)' }}>
          {label}
          <div style={{ position: 'absolute', left: 36, top: '50%', height: 5, borderRadius: 5, width: `calc(${s * 100}% - ${s * 72}px)`, background: C0.warn }}></div>
        </div>
      </div>
    );
  };
  return <React.Fragment>{opt('Tell my manager', 440, 0.9)}{opt("Tell Priya's manager", 1000, 1.3)}</React.Fragment>;
}

function Chat() {
  const { T, CUES: C } = useComposition();
  const winO = win(T, C.Book + 0.1, C.Decide + 0.1);
  const landO = 1 - MOTION.enter(C.Book + 2.5, 0.5)(T);
  const chatO = MOTION.enter(C.Intake - 0.3, 0.5)(T);
  const cx = interpolate([C.Book + 0.6, C.Book + 1.8], [1760, 1140], Easing.easeInOutCubic)(T);
  const cy = interpolate([C.Book + 0.6, C.Book + 1.8], [980, 700], Easing.easeInOutCubic)(T);
  const press = T > C.Book + 2.0 && T < C.Book + 2.25 ? 0.95 : 1;
  const msgs = [
    [C.Intake + 0.4, 'm', "Hi Sam. This is private. Nothing you say here is recorded. What happened?"],
    [C.Intake + 1.9, 's', 'Priya overrode my timeline in front of the client. I felt blindsided.'],
    [C.Intake + 3.3, 'm', 'When did things start feeling tense between you two?'],
    [C.Intake + 4.6, 's', 'A few weeks ago, when the launch date moved.'],
    [C.Reflect + 0.3, 'm', 'Why do you think Priya pushed for the earlier date?'],
    [C.Reflect + 1.6, 's', "She's worried the client walks if we slip."],
    [C.Reflect + 3.0, 'm', 'Is there anything you did that made it harder?'],
    [C.Reflect + 4.3, 's', 'I went quiet instead of raising it with her.'],
  ];
  const SLOT = 118, VIS = 4;
  const shown = msgs.reduce((a, m) => a + MOTION.enter(m[0], 0.5)(T), 0);
  const off = Math.max(0, shown - VIS) * SLOT;
  const ins = MOTION.pop(C.Reflect + 5.5, 0.7)(T) * (1 - MOTION.enter(C.Decide - 0.3, 0.4)(T));
  return (
    <div style={{ ...abs(640, 230, 1120, 660), opacity: winO }}>
      <div style={{ position: 'absolute', inset: 0, background: C0.card, borderRadius: 44, boxShadow: '0 24px 60px rgba(42,45,44,0.12)', overflow: 'hidden' }}>
        <div style={{ height: 88, display: 'flex', alignItems: 'center', gap: 16, padding: '0 40px', borderBottom: `2px solid ${C0.room}` }}>
          <div style={{ width: 44, height: 44, borderRadius: '50%', background: C0.acc, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: 24 }}>M</div>
          <span style={{ fontFamily: HF, fontSize: 30, color: C0.ink }}>Mend</span>
          <span style={{ marginLeft: 'auto', fontFamily: BF, fontSize: 24, fontWeight: 600, color: C0.acc7, background: C0.acc1, borderRadius: 999, padding: '8px 20px' }}>Private · not recorded</span>
        </div>
        <div style={{ position: 'absolute', left: 60, right: 60, top: 150, opacity: landO, display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div style={{ fontFamily: HF, fontSize: 64, lineHeight: 1.05, color: C0.ink }}>Talk it through, privately.</div>
          <div style={{ fontFamily: BF, fontSize: 30, color: C0.mute }}>No case number. No manager notified.</div>
          <div style={{ marginTop: 40, alignSelf: 'flex-start', background: C0.acc, color: '#fff', borderRadius: 999, padding: '26px 44px', fontFamily: BF, fontWeight: 700, fontSize: 32, transform: `scale(${press})` }}>Start a private session</div>
        </div>
        <div style={{ position: 'absolute', left: 44, right: 44, top: 110, bottom: 30, overflow: 'hidden', opacity: chatO }}>
          <div style={{ transform: `translateY(${-off}px)` }}>
            {msgs.map((m, i) => {
              const a = MOTION.enter(m[0], 0.5)(T);
              const me = m[1] === 's';
              return (
                <div key={i} style={{ height: SLOT * a, display: 'flex', justifyContent: me ? 'flex-end' : 'flex-start', alignItems: 'flex-start', opacity: a }}>
                  <div style={{ maxWidth: 760, background: me ? C0.blu2 : C0.acc1, color: me ? C0.blu9 : C0.acc9, borderRadius: 32, padding: '20px 28px', fontFamily: BF, fontSize: 28, lineHeight: 1.3, transform: `translateY(${(1 - a) * 20}px)` }}>{m[2]}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 120, right: 120, top: 180, opacity: Math.min(1, ins), transform: `scale(${0.85 + 0.15 * ins})`, background: C0.acc, color: '#fff', borderRadius: 40, padding: '44px 52px', boxShadow: '0 30px 70px rgba(27,52,47,0.28)' }}>
        <div style={{ fontFamily: BF, fontWeight: 700, fontSize: 24, letterSpacing: '0.08em', textTransform: 'uppercase', color: C0.acc2, marginBottom: 14 }}>Sam's realization</div>
        <div style={{ fontFamily: HF, fontSize: 48, lineHeight: 1.15 }}>We both want the launch to succeed. We just disagree on how.</div>
      </div>
      <svg width="60" height="60" viewBox="0 0 24 24" style={{ position: 'absolute', left: cx - 640, top: cy - 230, opacity: landO * MOTION.enter(C.Book + 0.4, 0.3)(T) }}>
        <path d="M4 3 L19 12 L12 13.5 L9 20 Z" fill={C0.ink} stroke="#fff" strokeWidth="1.5" strokeLinejoin="round"></path>
      </svg>
    </div>
  );
}

function Decide() {
  const { T, CUES: C } = useComposition();
  const d = C.Decide;
  const out = 1 - MOTION.enter(C.HandleIt + 0.4, 0.5)(T);
  const a = MOTION.pop(d + 0.7)(T), b = MOTION.pop(d + 1.1)(T), pick = MOTION.enter(d + 3.0, 0.4)(T);
  const card = (x, t, sub, v, hi) => (
    <div style={{ ...abs(x, 520, 640, 300), opacity: v * out, transform: `translateY(${(1 - v) * 40}px) scale(${1 + 0.04 * hi})`, background: C0.card, borderRadius: 44, border: `4px solid ${hi > 0 ? C0.acc : 'transparent'}`, padding: '44px 48px', boxSizing: 'border-box', boxShadow: '0 16px 40px rgba(42,45,44,0.08)', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <span style={{ fontFamily: BF, fontWeight: 700, fontSize: 24, letterSpacing: '0.08em', textTransform: 'uppercase', color: C0.acc7 }}>{sub}</span>
      <span style={{ fontFamily: HF, fontSize: 44, lineHeight: 1.12, color: C0.ink }}>{t}</span>
    </div>
  );
  return <React.Fragment>{card(280, "I've got this. I'll talk to Priya myself.", 'Path 1', a, pick)}{card(1000, "I'd like help talking it through together.", 'Path 2', b, 0)}</React.Fragment>;
}

function HandleIt() {
  const { T, CUES: C } = useComposition();
  const h = C.HandleIt;
  const o = win(T, h + 0.5, C.Support + 0.2);
  const tips = ['Open with the goal you share', 'Name your own part first', 'Agree how you’ll decide next time'];
  const say = MOTION.pop(h + 5.0)(T) * (1 - MOTION.enter(C.Support - 0.3, 0.3)(T));
  const link = MOTION.draw(h + 5.8, 0.6)(T) * (1 - MOTION.enter(C.Support - 0.3, 0.3)(T));
  const badge = MOTION.pop(h + 6.3)(T) * (1 - MOTION.enter(C.Support - 0.3, 0.3)(T));
  return (
    <React.Fragment>
      <div style={{ ...abs(160, 300, 820, 460), opacity: o, background: C0.card, borderRadius: 44, padding: '48px 52px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 22, boxShadow: '0 16px 40px rgba(42,45,44,0.08)' }}>
        <span style={{ fontFamily: BF, fontWeight: 700, fontSize: 24, letterSpacing: '0.08em', textTransform: 'uppercase', color: C0.acc7 }}>Mend coaches the conversation</span>
        {tips.map((t, i) => {
          const a = MOTION.pop(h + 1.0 + i * 1.0)(T);
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 24, opacity: Math.min(1, a), transform: `translateX(${(1 - a) * -30}px)` }}>
              <div style={{ flex: 'none', width: 64, height: 64, borderRadius: '50%', background: C0.acc, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: 30 }}>{i + 1}</div>
              <span style={{ fontFamily: BF, fontSize: 34, fontWeight: 600, color: C0.ink }}>{t}</span>
            </div>
          );
        })}
      </div>
      <div style={{ ...abs(1110, 250, 560, 0), opacity: Math.min(1, say) }}>
        <div style={{ transform: `scale(${0.8 + 0.2 * say})`, transformOrigin: 'bottom left', background: C0.blu2, color: C0.blu9, borderRadius: 32, padding: '22px 30px', fontFamily: BF, fontSize: 28, lineHeight: 1.3 }}>“Can we talk about the launch? I think we want the same thing.”</div>
      </div>
      <div style={{ position: 'absolute', left: 1440 - 40 * link, top: 534, width: 80 * link, height: 12, borderRadius: 12, background: C0.acc }}></div>
      <div style={{ ...abs(1120, 780, 640, 80), display: 'flex', alignItems: 'flex-start', justifyContent: 'center', opacity: Math.min(1, badge) }}>
        <div style={{ transform: `scale(${0.8 + 0.2 * badge})`, background: C0.acc, color: '#fff', borderRadius: 999, padding: '18px 32px', fontFamily: BF, fontWeight: 700, fontSize: 28, whiteSpace: 'nowrap' }}>Resolved between them · nothing on file</div>
      </div>
    </React.Fragment>
  );
}

function Support() {
  const { T, CUES: C } = useComposition();
  const s = C.Support;
  const o = win(T, s + 0.4, C.CheckIn + 0.1);
  const steps = [['1:1 with each person first', 'Mend hears Priya alone, too'], ['A facilitated joint session', 'Either person can pause or leave'], ['Agreement happens privately', 'One at a time, afterward']];
  return (
    <div style={{ ...abs(160, 250, 820, 600), opacity: o, display: 'flex', flexDirection: 'column', gap: 22 }}>
      {steps.map((st, i) => {
        const a = MOTION.pop(s + 0.8 + i * 1.3)(T);
        return (
          <div key={i} style={{ opacity: Math.min(1, a), transform: `translateX(${(1 - a) * -30}px)`, background: C0.card, borderRadius: 40, padding: '28px 36px', display: 'flex', alignItems: 'center', gap: 24, boxShadow: '0 12px 30px rgba(42,45,44,0.07)' }}>
            <div style={{ flex: 'none', width: 64, height: 64, borderRadius: '50%', background: C0.blu, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: 30 }}>{i + 1}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontFamily: HF, fontSize: 36, color: C0.ink }}>{st[0]}</span>
              <span style={{ fontFamily: BF, fontSize: 26, color: C0.mute }}>{st[1]}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CheckIn() {
  const { T, CUES: C } = useComposition();
  const k = C.CheckIn;
  const o = win(T, k + 0.4, C.Close + 0.2);
  const press = MOTION.enter(k + 3.0, 0.2)(T);
  const done = MOTION.pop(k + 3.6)(T);
  return (
    <div style={{ ...abs(860, 290, 860, 520), opacity: o, transform: `translateY(${(1 - MOTION.enter(k + 0.4)(T)) * 40}px)`, background: C0.card, borderRadius: 44, padding: '48px 52px', boxSizing: 'border-box', boxShadow: '0 24px 60px rgba(42,45,44,0.12)', display: 'flex', flexDirection: 'column', gap: 22 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ width: 44, height: 44, borderRadius: '50%', background: C0.acc, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: 24 }}>M</div>
        <span style={{ fontFamily: BF, fontWeight: 600, fontSize: 26, color: C0.mute }}>Mend · two weeks later</span>
      </div>
      <div style={{ fontFamily: HF, fontSize: 50, lineHeight: 1.1, color: C0.ink }}>Does it feel resolved with Priya?</div>
      <div style={{ display: 'flex', gap: 18, marginTop: 10 }}>
        <div style={{ background: C0.acc, color: '#fff', borderRadius: 999, padding: '22px 34px', fontFamily: BF, fontWeight: 700, fontSize: 28, transform: `scale(${1 - 0.05 * press * (1 - done)})` }}>Yes, it’s resolved</div>
        <div style={{ border: `3px solid ${C0.acc}`, color: C0.acc7, borderRadius: 999, padding: '19px 31px', fontFamily: BF, fontWeight: 700, fontSize: 28 }}>I need more support</div>
      </div>
      <div style={{ opacity: Math.min(1, done), transform: `translateY(${(1 - done) * 16}px)`, fontFamily: BF, fontSize: 28, color: C0.acc7, fontWeight: 600 }}>Closed. Nothing about it ever reached a manager.</div>
    </div>
  );
}

function Close() {
  const { T, CUES: C } = useComposition();
  const a = MOTION.enter(C.Close + 0.3, 0.8)(T), b = MOTION.enter(C.Close + 1.2, 0.8)(T);
  const cir = MOTION.pop(C.Close + 0.1, 0.9)(T);
  return (
    <React.Fragment>
      <div style={{ position: 'absolute', right: -180, top: -160, width: 760, height: 760, borderRadius: '50%', background: C0.acc2, transform: `scale(${cir})` }}></div>
      <div style={{ position: 'absolute', right: 420, top: 560, width: 260, height: 260, borderRadius: '50%', background: C0.blu2, transform: `scale(${cir})` }}></div>
      <div style={{ position: 'absolute', left: 160, top: 300, width: 1300, display: 'flex', flexDirection: 'column', gap: 36 }}>
        <div style={{ opacity: a, transform: `translateY(${(1 - a) * 30}px)`, fontFamily: HF, fontSize: 104, lineHeight: 1.0, color: C0.ink }}>Repair it with your teammate. Keep it off your record.</div>
        <div style={{ opacity: b, display: 'flex', alignItems: 'center', gap: 18 }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: C0.acc, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: 34 }}>M</div>
          <span style={{ fontFamily: HF, fontSize: 48, color: C0.ink }}>Mend</span>
        </div>
      </div>
    </React.Fragment>
  );
}

function Piece() {
  const { T, CUES: C } = useComposition();
  const caps = [
    { at: 0.3, text: 'Priya and Sam clash over a launch deadline.' },
    { at: C.Hesitate + 0.2, text: 'Sam wants it fixed, without bringing in either manager.' },
    { at: C.Book + 0.2, text: 'Sam books a private 1:1 with Mend.' },
    { at: C.Intake + 0.1, text: 'Mend listens and asks clarifying questions.' },
    { at: C.Reflect + 0.1, text: 'Then helps Sam see both sides, including their own.' },
    { at: C.Decide + 0.2, text: 'What would Sam like to do now?' },
    { at: C.HandleIt + 0.2, text: 'Path 1: Sam feels ready to resolve it directly.' },
    { at: C.Support + 0.2, text: 'Path 2: Sam wants support resolving it together.' },
    { at: C.CheckIn + 0.2, text: 'Later, Mend checks in, privately.', until: C.Close - 0.1 },
  ];
  return (
    <div data-screen-label={`t=${Math.floor(T)}s`} style={{ position: 'absolute', inset: 0, background: C0.bg, overflow: 'hidden', fontFamily: BF }}>
      <Room />
      <Conflict />
      <Hesitate />
      <Chat />
      <Decide />
      <HandleIt />
      <Support />
      <CheckIn />
      <People />
      <Close />
      <Rail />
      <Captions items={caps} style={{ top: 58, bottom: 'auto', left: 120, right: 120, textAlign: 'left', font: `400 52px ${HF}`, color: C0.ink, textShadow: 'none' }} />
    </div>
  );
}

function MendFlow() {
  return (
    <CompositionStage width={1920} height={1080} bg={C0.bg} scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
      <Piece />
    </CompositionStage>
  );
}
window.MendFlow = MendFlow;
