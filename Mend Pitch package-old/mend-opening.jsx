const C0 = {
  bg: '#fbfaf7', room: '#f2f1ec', card: '#fdfcfa', ink: '#2a2d2c', mute: '#65645f', line: '#dfddd6',
  acc: '#4f8a7e', acc1: '#eef6f4', acc2: '#dbece8', acc7: '#386a60', acc9: '#1b342f',
  blu: '#8193c6', blu1: '#f1f4fb', blu2: '#e2e8f6', blu9: '#252b40',
  pri: '#e6b8a4', pri9: '#5a3325', warn: '#c0765e',
};
const HF = '"Caprasimo", Georgia, serif';
const BF = '"Figtree", system-ui, sans-serif';

const MOTION = {
  enter: (s, d = 0.6) => animate({ from: 0, to: 1, start: s, end: s + d, ease: Easing.easeOutCubic }),
  pop: (s, d = 0.55) => animate({ from: 0, to: 1, start: s, end: s + d, ease: Easing.easeOutBack }),
  draw: (s, d = 0.8) => animate({ from: 0, to: 1, start: s, end: s + d, ease: Easing.easeInOutCubic }),
};
const win = (T, a, b, f = 0.45) => Math.min(MOTION.enter(a, f)(T), 1 - MOTION.enter(b - f, f)(T));
const kf = (keys, T, i) => interpolate(keys.map(k => k[0]), keys.map(k => k[i]), Easing.easeInOutCubic)(T);
const abs = (x, y, w, h) => ({ position: 'absolute', left: x, top: y, width: w, height: h });


function Face({ s, bg, skin, hair, shirt, long, mood, talk = 0 }) {
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
      {talk > 0.02
        ? <ellipse cx="50" cy="61" rx="5.5" ry={1.2 + 4.5 * talk} fill="#6b3a2c"></ellipse>
        : <path d={`M43 60 Q50 ${60 + curve} 57 60`} fill="none" stroke="#6b3a2c" strokeWidth="2.4" strokeLinecap="round"></path>}
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


const SAMF = { skin: '#e2b08c', hair: '#4a3426', shirt: '#4e5c86', long: false };
const PRIF = { skin: '#a8704f', hair: '#231b18', shirt: '#386a60', long: true };

function useLines() {
  const { CUES: C } = useComposition();
  return [
    [C.IntakeSam + 0.6, C.IntakeSam + 2.8, 'm', 'Sam, it’s just the two of us. Tell me broadly what happened.', true],
    [C.IntakeSam + 3.0, C.IntakeSam + 4.8, 's', 'Priya overrode my plan in front of the client.', true],
    [C.IntakeSam + 5.0, C.IntakeSam + 6.4, 'm', 'How are you feeling about it now?', true],
    [C.IntakeSam + 6.6, C.IntakeSam + 8.0, 's', 'Frustrated. And honestly, a bit embarrassed.', true],
    [C.IntakePriya + 0.5, C.IntakePriya + 2.3, 'm', 'Priya, what’s been going on from your side?', true],
    [C.IntakePriya + 2.5, C.IntakePriya + 4.5, 'p', 'Sam’s been avoiding me since the launch date moved.', true],
    [C.IntakePriya + 4.7, C.IntakePriya + 5.8, 'm', 'And how does that feel?', true],
    [C.IntakePriya + 6.0, C.IntakePriya + 7.4, 'p', 'Stressful. I don’t want this to drag on.', true],
    [C.Screen + 0.8, C.Screen + 3.0, 'm', '', false],
    [C.Apart + 0.8, C.Apart + 2.8, 'm', '', false],
    [C.Arrive + 0.6, C.Arrive + 2.2, 'm', 'Hi Sam, hi Priya. Thanks for being here.', true],
    [C.Arrive + 2.4, C.Arrive + 4.3, 'm', 'Before we start, let’s name the obvious.', true],
    [C.Awkward + 0.2, C.Awkward + 2.6, 'm', 'Talking through a conflict with an AI can feel a little cringey. That’s fair.', true],
    [C.Awkward + 2.8, C.Awkward + 3.9, 's', 'Honestly, yeah. It’s a bit weird.', true],
    [C.Awkward + 4.0, C.Awkward + 4.6, 'p', 'Same.', true],
    [C.Awkward + 4.8, C.Awkward + 6.0, 'm', 'But that awkwardness is a feature, not a bug.', true],
    [C.Awkward + 6.2, C.Awkward + 8.9, 'm', 'A little cringey beats having management in the middle of this, for both of your careers.', true],
    [C.Why + 0.8, C.Why + 2.3, 'm', '', false],
    [C.Why + 2.4, C.Why + 3.9, 'm', '', false],
    [C.Why + 4.0, C.Why + 6.0, 'm', '', false],
    [C.Invisible + 1.0, C.Invisible + 3.2, 'm', '', false],
    [C.Ground + 0.4, C.Ground + 2.0, 'm', 'Either of you can pause or leave at any time.', true],
    [C.Ground + 2.1, C.Ground + 4.6, 'm', 'Nothing said here is recorded, and no one above you will know it happened.', true],
    [C.Begin + 0.3, C.Begin + 1.6, 'm', 'Sam, would you like to start?', true],
    [C.Begin + 1.9, C.Begin + 3.4, 's', 'Okay. I’ll start.', true],
    [C.Heat + 0.2, C.Heat + 2.6, 's', 'The deadline change felt rushed. Kind of careless.', true],
    [C.Heat + 2.8, C.Heat + 4.4, 'p', 'Careless? I was the one saving the account.', true],
    [C.Heat + 4.6, C.Heat + 5.8, 'm', 'Let’s pause here for a moment.', true],
    [C.Caucus + 0.4, C.Caucus + 2.6, 'm', 'Priya, it’s just us now. Sam can’t hear this. Are you okay?', true],
    [C.Caucus + 2.8, C.Caucus + 4.4, 'p', 'I’m okay. That word just stung.', true],
    [C.Caucus + 4.6, C.Caucus + 6.8, 'm', 'That makes sense. How would you like to respond when we’re back?', true],
    [C.Caucus + 7.0, C.Caucus + 9.2, 'p', 'Tell Sam how it landed, without firing back.', true],
    [C.Caucus + 9.4, C.Caucus + 10.6, 'm', 'That sounds like a good plan.', true],
    [C.Resume + 0.6, C.Resume + 3.6, 'p', 'Sam, when you said careless, it felt like my work didn’t count.', true],
    [C.Resume + 3.8, C.Resume + 5.4, 's', 'That’s fair. It’s not what I meant.', true],
  ];
}
const talkOf = (lines, who, T) => {
  for (const l of lines) if (l[2] === who && T >= l[0] && T < l[1]) {
    const env = Math.min(1, (T - l[0]) / 0.12, (l[1] - T) / 0.12);
    return env * (0.35 + 0.65 * Math.abs(Math.sin((T - l[0]) * 11.5)) * (0.7 + 0.3 * Math.sin((T - l[0]) * 3.1)));
  }
  return 0;
};

function Ball({ s, talk, bob }) {
  return (
    <div style={{ position: 'relative', width: s, height: s, transform: 'translateY(' + bob + 'px)' }}>
      <div style={{ position: 'absolute', inset: -s * 0.12 * talk, borderRadius: '50%', background: C0.acc2, opacity: 0.8 * Math.min(1, talk * 2) }}></div>
      <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: 'radial-gradient(circle at 34% 30%, #7fb3a7 0%, ' + C0.acc + ' 55%, ' + C0.acc7 + ' 100%)', boxShadow: '0 ' + s * 0.08 + 'px ' + s * 0.2 + 'px rgba(27,52,47,0.22)' }}></div>
      <div style={{ position: 'absolute', left: '50%', top: '58%', width: s * 0.2, height: s * (0.035 + 0.16 * talk), borderRadius: 999, background: C0.card, transform: 'translate(-50%,-50%)' }}></div>
    </div>
  );
}

function ORoom() {
  const { T, CUES: C } = useComposition();
  const o = 1 - MOTION.enter(C.Close - 0.2, 0.6)(T);
  return <div style={{ ...abs(80, 170, 1760, 800), borderRadius: 56, background: C0.room, opacity: o }}></div>;
}

const TILE = { y: 290, w: 460, h: 440, xs: [240, 730, 1220] };

function OCall() {
  const { T, CUES: C } = useComposition();
  const lines = useLines();
  const ez = Easing.easeInOutCubic;
  const o = interpolate([C.Arrive - 0.4, C.Arrive + 0.2, C.Why - 0.1, C.Why + 0.4, C.Ground - 0.4, C.Ground + 0.1, C.Close - 0.2, C.Close + 0.3], [0, 1, 1, 0, 0, 1, 1, 0], ez)(T);
  const sc = interpolate([C.Why - 0.1, C.Why + 0.4, C.Ground - 0.4, C.Ground + 0.1], [1, 0.94, 0.94, 1], ez)(T);
  const samMood = interpolate([C.Awkward + 1.0, C.Awkward + 2.0, C.Ground + 0.5, C.Ground + 2.5, C.Begin + 1.5, C.Heat + 0.2, C.Heat + 3.0, C.Resume + 3.6, C.Resume + 4.4], [0.6, 0.4, 0.4, 0.75, 0.8, 0.5, 0.3, 0.35, 0.65], ez)(T);
  const priMood = interpolate([C.Awkward + 1.0, C.Awkward + 2.0, C.Awkward + 3.9, C.Awkward + 4.4, C.Ground + 0.5, C.Ground + 2.5, C.Heat + 2.2, C.Heat + 2.8, C.Caucus + 2.8, C.Caucus + 10, C.Resume + 4.4], [0.6, 0.4, 0.4, 0.5, 0.5, 0.8, 0.75, 0.1, 0.2, 0.5, 0.6], ez)(T);
  const cv = win(T, C.Caucus + 0.1, C.Resume + 0.2, 0.4);
  const ts = talkOf(lines, 's', T), tp = talkOf(lines, 'p', T), tm = talkOf(lines, 'm', T);
  let cur = null; for (const l of lines) if (l[4] && T >= l[0] - 0.1 && T < l[1] + 0.35) cur = l;
  const subO = cur ? Math.min(1, (T - cur[0] + 0.1) / 0.2, (cur[1] + 0.35 - T) / 0.2) : 0;
  const names = { m: 'Mend', s: 'Sam', p: 'Priya' };
  const ct = Math.max(0, T - C.Arrive), mins = Math.floor(ct / 60), secs = Math.floor(ct % 60);
  const tile = (i, bg, speaking, name, child) => (
    <div style={{ position: 'absolute', left: TILE.xs[i] - 200, top: TILE.y - 180, width: TILE.w, height: TILE.h, borderRadius: 36, background: bg, overflow: 'hidden', boxShadow: speaking > 0.05 ? '0 0 0 6px ' + C0.acc : '0 0 0 0px ' + C0.acc }}>
      {child}
      <div style={{ position: 'absolute', left: 20, bottom: 20, background: 'rgba(253,252,250,0.92)', borderRadius: 999, padding: '8px 18px', fontFamily: BF, fontWeight: 700, fontSize: 24, color: C0.ink }}>{name}</div>
    </div>
  );
  return (
    <div style={{ ...abs(200, 180, 1520, 770), opacity: o, transform: 'scale(' + sc + ')' }}>
      <div style={{ position: 'absolute', inset: 0, background: C0.card, borderRadius: 44, boxShadow: '0 24px 60px rgba(42,45,44,0.12)', overflow: 'hidden' }}>
        <div style={{ height: 84, display: 'flex', alignItems: 'center', gap: 16, padding: '0 40px' }}>
          <span style={{ fontFamily: HF, fontSize: 30, color: C0.ink }}>Mend</span>
          <span style={{ fontFamily: BF, fontSize: 26, color: cv > 0.5 ? C0.acc7 : C0.mute, fontWeight: cv > 0.5 ? 700 : 400 }}>{cv > 0.5 ? 'Private check-in · Priya' : 'Joint session'}</span>
          <span style={{ marginLeft: 'auto', fontFamily: BF, fontSize: 24, fontWeight: 600, color: C0.acc7, background: C0.acc1, borderRadius: 999, padding: '8px 20px' }}>Not recorded</span>
          <span style={{ fontFamily: BF, fontSize: 24, fontWeight: 600, color: C0.mute, fontVariantNumeric: 'tabular-nums' }}>{mins + ':' + String(secs).padStart(2, '0')}</span>
        </div>
        {tile(0, C0.blu2, ts, 'Sam', <React.Fragment><div style={{ position: 'absolute', left: 80, top: 50, filter: 'saturate(' + (1 - 0.7 * cv) + ')' }}><Face s={300} bg={C0.blu2} {...SAMF} mood={samMood} talk={ts} /></div><div style={{ position: 'absolute', inset: 0, background: 'rgba(42,45,44,0.62)', opacity: cv, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10 }}><span style={{ fontFamily: HF, fontSize: 36, color: '#fff' }}>On hold</span><span style={{ fontFamily: BF, fontWeight: 600, fontSize: 24, color: C0.room }}>Sam can’t hear this</span></div></React.Fragment>)}
        {tile(1, C0.acc1, tm, 'Mend', null)}
        {tile(2, '#f6e3da', tp, 'Priya', <div style={{ position: 'absolute', left: 80, top: 50 }}><Face s={300} bg={'#f6e3da'} {...PRIF} mood={priMood} talk={tp} /></div>)}
        <div style={{ position: 'absolute', left: 40, right: 40, top: 570, height: 92, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: subO }}>
          {cur && <div style={{ flex: 'none', width: 'max-content', maxWidth: 1300, boxSizing: 'border-box', background: C0.ink, color: C0.card, borderRadius: 24, padding: '14px 28px', fontFamily: BF, fontSize: 30, lineHeight: 1.3, textAlign: 'center' }}><strong style={{ fontWeight: 700, color: C0.acc2 }}>{names[cur[2]]}: </strong>{cur[3]}</div>}
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, display: 'flex', justifyContent: 'center', gap: 16 }}>
          {['Mute', 'Pause session', 'Leave'].map((b, i) => (
            <div key={i} style={{ background: i === 2 ? '#f6e3da' : C0.room, color: i === 2 ? C0.pri9 : C0.ink, borderRadius: 999, padding: '14px 28px', fontFamily: BF, fontWeight: 600, fontSize: 24 }}>{b}</div>
          ))}
        </div>
      </div>
    </div>
  );
}


function OIntake() {
  const { T, CUES: C } = useComposition();
  const lines = useLines();
  const o = interpolate([0.05, 0.5, C.Screen - 0.2, C.Screen + 0.3], [0, 1, 1, 0], Easing.easeInOutCubic)(T);
  const swap = MOTION.enter(C.IntakePriya - 0.3, 0.6)(T);
  const ts = talkOf(lines, 's', T), tp = talkOf(lines, 'p', T), tm = talkOf(lines, 'm', T);
  let cur = null; for (const l of lines) if (l[4] && l[0] < C.Screen && T >= l[0] - 0.1 && T < l[1] + 0.35) cur = l;
  const subO = cur ? Math.min(1, (T - cur[0] + 0.1) / 0.2, (cur[1] + 0.35 - T) / 0.2) : 0;
  const names = { m: 'Mend', s: 'Sam', p: 'Priya' };
  const base = T < C.IntakePriya ? 0 : C.IntakePriya;
  const ct = Math.max(0, T - base), mm = Math.floor(ct / 60), ss = Math.floor(ct % 60);
  const who = swap < 0.5 ? 'Sam' : 'Priya';
  return (
    <div style={{ ...abs(200, 180, 1520, 770), opacity: o }}>
      <div style={{ position: 'absolute', inset: 0, background: C0.card, borderRadius: 44, boxShadow: '0 24px 60px rgba(42,45,44,0.12)', overflow: 'hidden' }}>
        <div style={{ height: 84, display: 'flex', alignItems: 'center', gap: 16, padding: '0 40px' }}>
          <span style={{ fontFamily: HF, fontSize: 30, color: C0.ink }}>Mend</span>
          <span style={{ fontFamily: BF, fontSize: 26, color: C0.mute }}>{'Private intake · ' + who}</span>
          <span style={{ marginLeft: 'auto', fontFamily: BF, fontSize: 24, fontWeight: 600, color: C0.acc7, background: C0.acc1, borderRadius: 999, padding: '8px 20px' }}>Not recorded</span>
          <span style={{ fontFamily: BF, fontSize: 24, fontWeight: 600, color: C0.mute, fontVariantNumeric: 'tabular-nums' }}>{mm + ':' + String(ss).padStart(2, '0')}</span>
        </div>
        <div style={{ position: 'absolute', left: 60, top: 110, width: 680, height: 440, borderRadius: 36, overflow: 'hidden', background: swap < 0.5 ? C0.blu2 : '#f6e3da', boxShadow: '0 0 0 ' + ((ts > 0.05 || tp > 0.05) ? 6 : 0) + 'px ' + C0.acc }}>
          <div style={{ position: 'absolute', left: 190, top: 60, opacity: 1 - swap }}><Face s={300} bg={C0.blu2} {...SAMF} mood={0.3} talk={ts} /></div>
          <div style={{ position: 'absolute', left: 190, top: 60, opacity: swap }}><Face s={300} bg={'#f6e3da'} {...PRIF} mood={0.35} talk={tp} /></div>
          <div style={{ position: 'absolute', left: 20, bottom: 20, background: 'rgba(253,252,250,0.92)', borderRadius: 999, padding: '8px 18px', fontFamily: BF, fontWeight: 700, fontSize: 24, color: C0.ink }}>{who}</div>
        </div>
        <div style={{ position: 'absolute', left: 780, top: 110, width: 680, height: 440, borderRadius: 36, overflow: 'hidden', background: C0.acc1, boxShadow: '0 0 0 ' + (tm > 0.05 ? 6 : 0) + 'px ' + C0.acc }}>
          <div style={{ position: 'absolute', left: 20, bottom: 20, background: 'rgba(253,252,250,0.92)', borderRadius: 999, padding: '8px 18px', fontFamily: BF, fontWeight: 700, fontSize: 24, color: C0.ink }}>Mend</div>
        </div>
        <div style={{ position: 'absolute', left: 40, right: 40, top: 570, height: 92, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: subO }}>
          {cur && <div style={{ flex: 'none', width: 'max-content', maxWidth: 1300, boxSizing: 'border-box', background: C0.ink, color: C0.card, borderRadius: 24, padding: '14px 28px', fontFamily: BF, fontSize: 30, lineHeight: 1.3, textAlign: 'center' }}><strong style={{ fontWeight: 700, color: C0.acc2 }}>{names[cur[2]] + ': '}</strong>{cur[3]}</div>}
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, display: 'flex', justifyContent: 'center', gap: 16 }}>
          {['Mute', 'Pause', 'Leave'].map((b, i) => (
            <div key={i} style={{ background: i === 2 ? '#f6e3da' : C0.room, color: i === 2 ? C0.pri9 : C0.ink, borderRadius: 999, padding: '14px 28px', fontFamily: BF, fontWeight: 600, fontSize: 24 }}>{b}</div>
          ))}
        </div>
      </div>
    </div>
  );
}

function OScreen() {
  const { T, CUES: C } = useComposition();
  const s = C.Screen;
  const o = Math.min(MOTION.enter(s, 0.5)(T), 1 - MOTION.enter(C.Apart - 0.4, 0.4)(T));
  const dl = MOTION.draw(s + 1.0, 0.7)(T), dr = MOTION.draw(s + 1.2, 0.7)(T);
  const L = MOTION.pop(s + 1.7)(T), R = MOTION.pop(s + 3.6)(T), hi = MOTION.enter(s + 5.6, 0.5)(T);
  const lab = MOTION.enter(s + 0.4, 0.5)(T);
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: o }}>
      <div style={{ position: 'absolute', left: 760, top: 380, width: 400, textAlign: 'center', fontFamily: BF, fontWeight: 700, fontSize: 26, color: C0.acc7, opacity: lab }}>Safety screen</div>
      <svg width="1920" height="1080" style={{ position: 'absolute', left: 0, top: 0 }}>
        <path d="M960 430 C960 500, 540 470, 540 540" fill="none" stroke={C0.line} strokeWidth="8" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - dl}></path>
        <path d="M960 430 C960 500, 1380 470, 1380 540" fill="none" stroke={hi > 0.5 ? C0.acc : C0.line} strokeWidth="8" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - dr}></path>
      </svg>
      <div style={{ ...abs(180, 545, 720, 360), opacity: Math.min(1, L) * (1 - 0.35 * hi), transform: 'translateY(' + ((1 - L) * 30) + 'px)', background: C0.card, borderRadius: 44, padding: '38px 44px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 16, boxShadow: '0 16px 40px rgba(42,45,44,0.08)' }}>
        <span style={{ fontFamily: BF, fontWeight: 700, fontSize: 24, letterSpacing: '0.08em', textTransform: 'uppercase', color: C0.pri9 }}>If something alarming comes up</span>
        <span style={{ fontFamily: HF, fontSize: 38, lineHeight: 1.12, color: C0.ink }}>The process stops at intake and goes to HR.</span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 6 }}>
          <span style={{ background: '#f6e3da', color: C0.pri9, borderRadius: 999, padding: '10px 20px', fontFamily: BF, fontWeight: 600, fontSize: 24 }}>HR gets: category only</span>
          <span style={{ background: C0.room, color: C0.ink, borderRadius: 999, padding: '10px 20px', fontFamily: BF, fontWeight: 600, fontSize: 24 }}>No recording</span>
          <span style={{ background: C0.room, color: C0.ink, borderRadius: 999, padding: '10px 20px', fontFamily: BF, fontWeight: 600, fontSize: 24 }}>No transcript</span>
        </div>
      </div>
      <div style={{ ...abs(1020, 545, 720, 360), opacity: Math.min(1, R), transform: 'translateY(' + ((1 - R) * 30) + 'px) scale(' + (1 + 0.04 * hi) + ')', background: hi > 0.5 ? C0.acc : C0.card, color: hi > 0.5 ? '#fff' : C0.ink, borderRadius: 44, padding: '38px 44px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 16, boxShadow: '0 16px 40px rgba(42,45,44,0.08)' }}>
        <span style={{ fontFamily: BF, fontWeight: 700, fontSize: 24, letterSpacing: '0.08em', textTransform: 'uppercase', color: hi > 0.5 ? C0.acc2 : C0.acc7 }}>If it’s a good-faith conflict</span>
        <span style={{ fontFamily: HF, fontSize: 38, lineHeight: 1.12 }}>A joint session is set up with both people and Mend.</span>
      </div>
    </div>
  );
}

function OApart() {
  const { T, CUES: C } = useComposition();
  const a = C.Apart;
  const o = Math.min(MOTION.enter(a, 0.5)(T), 1 - MOTION.enter(C.Arrive - 0.4, 0.4)(T));
  const l = MOTION.pop(a + 0.5)(T), r = MOTION.pop(a + 0.8)(T), d = MOTION.draw(a + 1.6, 0.9)(T), tag = MOTION.pop(a + 2.5)(T), note = MOTION.enter(a + 3.4, 0.5)(T);
  const room = (x, v, face, bg, title, sub) => (
    <div style={{ ...abs(x, 440, 520, 400), opacity: Math.min(1, v), transform: 'scale(' + (0.9 + 0.1 * v) + ')', background: C0.card, borderRadius: 44, boxShadow: '0 16px 40px rgba(42,45,44,0.08)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14 }}>
      <div style={{ borderRadius: '50%', overflow: 'hidden' }}><Face s={180} bg={bg} {...face} mood={0.5} /></div>
      <span style={{ fontFamily: HF, fontSize: 36, color: C0.ink }}>{title}</span>
      <span style={{ fontFamily: BF, fontSize: 26, color: C0.mute }}>{sub}</span>
    </div>
  );
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: o }}>
      {room(200, l, SAMF, C0.blu2, 'Sam', 'Quiet room, 3rd floor')}
      {room(1200, r, PRIF, '#f6e3da', 'Priya', 'Working from home')}
      <div style={{ position: 'absolute', left: 740, top: 636, width: 440 * d, height: 8, borderRadius: 8, backgroundImage: 'repeating-linear-gradient(90deg, ' + C0.acc + ' 0 18px, transparent 18px 34px)' }}></div>
      <div style={{ position: 'absolute', left: 760, top: 560, width: 400, display: 'flex', justifyContent: 'center', opacity: Math.min(1, tag) }}>
        <div style={{ transform: 'scale(' + (0.8 + 0.2 * tag) + ')', background: C0.acc, color: '#fff', borderRadius: 999, padding: '14px 28px', fontFamily: BF, fontWeight: 700, fontSize: 28, whiteSpace: 'nowrap' }}>100+ ft apart</div>
      </div>
      <div style={{ position: 'absolute', left: 200, right: 200, top: 870, textAlign: 'center', fontFamily: BF, fontSize: 30, color: C0.mute, opacity: note }}>Separate rooms, separate devices. Ideally not even the same floor.</div>
    </div>
  );
}

function OBall() {
  const { T, CUES: C } = useComposition();
  const lines = useLines();
  const ez = Easing.easeInOutCubic;
  const cx = 200 + 730 + 30, cy = 180 + TILE.y - 180 + 200;
  const ix = 200 + 780 + 340, iy = 180 + 110 + 220;
  const keys = [[0, ix, iy, 240], [C.Screen - 0.2, ix, iy, 240], [C.Screen + 0.6, 960, 300, 130], [C.Apart - 0.2, 960, 300, 130], [C.Apart + 0.5, 960, 330, 110], [C.Arrive - 0.3, 960, 330, 110], [C.Arrive + 0.4, cx, cy, 240], [C.Why - 0.2, cx, cy, 240], [C.Why + 0.6, 1740, 112, 110], [C.Ground - 0.5, 1740, 112, 110], [C.Ground + 0.3, cx, cy, 240]];
  const x = kf(keys, T, 1), y = kf(keys, T, 2), s = kf(keys, T, 3);
  const o = MOTION.enter(0.3, 0.5)(T) * (1 - MOTION.enter(C.Close - 0.3, 0.4)(T)) * (1 - win(T, C.Invisible, C.Ground - 0.3, 0.4));
  return (
    <div style={{ position: 'absolute', left: x - s / 2, top: y - s / 2, opacity: o }}>
      <Ball s={s} talk={talkOf(lines, 'm', T)} bob={Math.sin(T * 1.7) * s * 0.04} />
    </div>
  );
}

function OWhy() {
  const { T, CUES: C } = useComposition();
  const w = C.Why;
  const out = 1 - MOTION.enter(C.Invisible - 0.3, 0.5)(T);
  const cards = [
    ['No side to take', 'Mend doesn’t report to your manager, to HR, or to either of you.'],
    ['No institutional bias', 'No office politics, no history, no favorites. Just the conversation in front of it.'],
    ['Nobody above you knows', 'Leadership never learns this conflict happened. That’s what makes honesty safe.'],
  ];
  return (
    <div style={{ position: 'absolute', left: 160, right: 160, top: 300, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32, opacity: out }}>
      {cards.map((c, i) => {
        const a = MOTION.pop(w + 0.8 + i * 1.6)(T);
        const hi = i === 2 ? MOTION.enter(w + 6.2, 0.5)(T) : 0;
        return (
          <div key={i} style={{ opacity: Math.min(1, a), transform: 'translateY(' + ((1 - a) * 40) + 'px) scale(' + (1 + 0.05 * hi) + ')', background: hi > 0.5 ? C0.acc : C0.card, color: hi > 0.5 ? '#fff' : C0.ink, borderRadius: 44, padding: '48px 44px', minHeight: 440, boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 22, boxShadow: '0 16px 40px rgba(42,45,44,0.08)' }}>
            <div style={{ width: 72, height: 72, borderRadius: '50%', background: hi > 0.5 ? '#fff' : C0.acc1, color: C0.acc7, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HF, fontSize: 34 }}>{i + 1}</div>
            <div style={{ fontFamily: HF, fontSize: 46, lineHeight: 1.08 }}>{c[0]}</div>
            <div style={{ fontFamily: BF, fontSize: 30, lineHeight: 1.4, color: hi > 0.5 ? C0.acc1 : C0.mute }}>{c[1]}</div>
          </div>
        );
      })}
    </div>
  );
}

function OInvisible() {
  const { T, CUES: C } = useComposition();
  const v = C.Invisible;
  const o = Math.min(MOTION.enter(v - 0.1, 0.5)(T), 1 - MOTION.enter(C.Ground - 0.4, 0.4)(T));
  const nodes = [['Leadership', 470], ['Your manager', 790], ["Priya’s manager", 1130], ['HR', 1450]];
  const wall = MOTION.draw(v + 1.0, 0.7)(T);
  const sess = MOTION.pop(v + 0.4)(T);
  const seen = MOTION.enter(v + 4.4, 0.5)(T);
  const pulse = T > v + 3.2 ? 1 + 0.06 * Math.sin((T - v - 3.2) * 8) * (1 - MOTION.enter(v + 3.2, 1.2)(T)) : 1;
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: o }}>
      {nodes.map((n, i) => {
        const a = MOTION.pop(v + 0.2 + i * 0.15)(T);
        return (
          <div key={i} style={{ position: 'absolute', left: n[1] - 150, top: 250, width: 300, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, opacity: Math.min(1, a) * (1 - 0.35 * seen) }}>
            <div style={{ background: C0.card, borderRadius: 999, padding: '20px 30px', fontFamily: BF, fontWeight: 700, fontSize: 28, color: C0.ink, boxShadow: '0 8px 24px rgba(42,45,44,0.08)', whiteSpace: 'nowrap' }}>{n[0]}</div>
          </div>
        );
      })}
      {nodes.map((n, i) => (
        <div key={'s' + i} style={{ position: 'absolute', left: n[1] - 150, top: 345, width: 300, textAlign: 'center', fontFamily: BF, fontWeight: 600, fontSize: 26, color: C0.acc7, opacity: seen }}>Sees: nothing</div>
      ))}
      <svg width="1920" height="1080" style={{ position: 'absolute', left: 0, top: 0 }}>
        {nodes.map((n, i) => {
          const d = MOTION.draw(v + 2.0 + i * 0.2, 0.9)(T);
          const x1 = 820 + i * 93, y1 = 640, x2 = n[1], y2 = 500;
          return <line key={i} x1={x1} y1={y1} x2={x1 + (x2 - x1) * d} y2={y1 + (y2 - y1) * d} stroke={C0.blu} strokeWidth="6" strokeLinecap="round" strokeDasharray="4 16"></line>;
        })}
      </svg>
      <div style={{ position: 'absolute', left: 960 - 700 * wall, top: 478, width: 1400 * wall, height: 18, borderRadius: 18, background: C0.acc, transform: 'scaleY(' + pulse + ')' }}></div>
      <div style={{ position: 'absolute', left: 960 - 160, top: 458, width: 320, display: 'flex', justifyContent: 'center', opacity: MOTION.pop(v + 1.6)(T) }}>
        <div style={{ background: C0.acc, color: '#fff', borderRadius: 999, padding: '14px 28px', fontFamily: BF, fontWeight: 700, fontSize: 26, whiteSpace: 'nowrap' }}>Nothing crosses</div>
      </div>
      <div style={{ position: 'absolute', left: 640, top: 630, width: 640, height: 250, opacity: Math.min(1, sess), transform: 'scale(' + (0.85 + 0.15 * sess) + ')', background: C0.card, borderRadius: 999, boxShadow: '0 20px 50px rgba(42,45,44,0.10)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 40 }}>
        <div style={{ borderRadius: '50%', overflow: 'hidden' }}><Face s={130} bg={C0.blu} {...SAMF} mood={0.5} /></div>
        <Ball s={130} talk={0} bob={0} />
        <div style={{ borderRadius: '50%', overflow: 'hidden' }}><Face s={130} bg={C0.pri} {...PRIF} mood={0.5} /></div>
      </div>
    </div>
  );
}

function OClose() {
  const { T, CUES: C } = useComposition();
  const a = MOTION.enter(C.Close + 0.3, 0.8)(T), b = MOTION.enter(C.Close + 1.4, 0.8)(T);
  const cir = MOTION.pop(C.Close + 0.1, 0.9)(T);
  return (
    <React.Fragment>
      <div style={{ position: 'absolute', right: -180, top: -160, width: 760, height: 760, borderRadius: '50%', background: C0.acc2, transform: 'scale(' + cir + ')' }}></div>
      <div style={{ position: 'absolute', right: 420, top: 600, width: 260, height: 260, borderRadius: '50%', background: C0.blu2, transform: 'scale(' + cir + ')' }}></div>
      <div style={{ position: 'absolute', left: 160, top: 300, width: 1300, display: 'flex', flexDirection: 'column', gap: 36 }}>
        <div style={{ opacity: a, transform: 'translateY(' + ((1 - a) * 30) + 'px)', fontFamily: HF, fontSize: 96, lineHeight: 1.02, color: C0.ink }}>A little awkward. Completely private.</div>
        <div style={{ opacity: b, display: 'flex', alignItems: 'center', gap: 18 }}>
          <Ball s={64} talk={0} bob={0} />
          <span style={{ fontFamily: HF, fontSize: 48, color: C0.ink }}>Mend</span>
        </div>
      </div>
    </React.Fragment>
  );
}

function OPiece() {
  const { T, CUES: C } = useComposition();
  const caps = [
    { at: 0.3, text: 'First, Mend meets each person privately.' },
    { at: C.IntakePriya + 0.2, text: 'Priya gets her own intake, too.' },
    { at: C.Screen + 0.2, text: 'Each intake doubles as a safety screen.' },
    { at: C.Apart + 0.2, text: 'Then a joint session, from separate places.' },
    { at: C.Arrive + 0.2, text: 'Mend opens the joint call.' },
    { at: C.Awkward + 0.2, text: 'Mend names the awkwardness up front.' },
    { at: C.Why + 0.2, text: 'The awkwardness is the point. Here’s why.' },
    { at: C.Invisible + 0.2, text: 'What matters most: leadership never knows.' },
    { at: C.Ground + 0.2, text: 'Ground rules, before anyone speaks.' },
    { at: C.Begin + 0.2, text: 'Then the conversation begins.' },
    { at: C.Heat + 0.2, text: 'Sometimes a comment lands hard.' },
    { at: C.Caucus + 0.2, text: 'Mend pauses and checks in privately.' },
    { at: C.Resume + 0.2, text: 'Then the conversation continues, more carefully.', until: C.Close - 0.1 },
  ];
  return (
    <div data-screen-label={'t=' + Math.floor(T) + 's'} style={{ position: 'absolute', inset: 0, background: C0.bg, overflow: 'hidden', fontFamily: BF }}>
      <ORoom />
      <OIntake />
      <OScreen />
      <OApart />
      <OCall />
      <OWhy />
      <OInvisible />
      <OClose />
      <OBall />
      <Captions items={caps} style={{ top: 58, bottom: 'auto', left: 120, right: 260, textAlign: 'left', font: '400 52px ' + HF, color: C0.ink, textShadow: 'none' }} />
    </div>
  );
}

function MendOpening() {
  return (
    <CompositionStage width={1920} height={1080} bg={C0.bg} scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
      <OPiece />
    </CompositionStage>
  );
}
window.MendOpening = MendOpening;
