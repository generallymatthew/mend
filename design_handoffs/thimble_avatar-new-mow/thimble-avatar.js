// Thimble avatar — reference implementation (vanilla JS, no dependencies).
// Usage:
//   const av = new ThimbleAvatar(document.getElementById('host'), { size: 240 });
//   av.setState('listening');   // 'idle' | 'listening' | 'thinking' | 'speaking' | 'muted' | 'paused'
//   av.setLevel(0.6);           // 0..1 audio amplitude — mic RMS while listening, TTS output RMS while speaking
//   av.destroy();

(function (global) {
  const PINK = '#F4849C', CREAM = '#F5F0E8', GREY = '#A9A39A';
  const BREATHE = { idle: 4.5, listening: 3, thinking: 3, speaking: 2.2, muted: 0, paused: 0 };
  const MOUTH = {
    idle:      { w: 30, h: 6, x: 50 },
    listening: { w: 34, h: 4, x: 50 },
    thinking:  { w: 12, h: 7, x: 58 },
    speaking:  { w: 26, h: 3, x: 50 }, // grows with level, see _tick()
    muted:     { w: 26, h: 3, x: 50 },
    paused:    { w: 28, h: 4, x: 50 }
  };

  class ThimbleAvatar {
    constructor(host, opts = {}) {
      this.size = opts.size || 240;
      this.facets = opts.facets || 6;          // sides of the rounded-hexagon wobble
      this.state = 'idle';
      this.level = 0;                          // raw input 0..1
      this.lvl = 0;                            // smoothed
      this.geo = 0;                            // 0 = circle, 1 = full rounded polygon
      this.t0 = performance.now();

      const el = (tag, css) => { const n = document.createElement(tag); Object.assign(n.style, css); return n; };
      this.root = el('div', { position: 'relative', width: this.size + 'px', height: this.size + 'px', transition: 'opacity .4s ease' });
      this.body = el('div', { position: 'absolute', inset: '0', background: PINK, overflow: 'hidden', transition: 'background .6s ease' });
      this.face = el('div', { position: 'absolute', inset: '0', transformOrigin: '50% 40%' });
      this.mouth = el('div', { position: 'absolute', bottom: '24%', borderRadius: '50%', background: CREAM });
      this.face.appendChild(this.mouth);
      this.body.appendChild(this.face);
      this.root.appendChild(this.body);
      host.appendChild(this.root);

      // setInterval rather than rAF so it keeps animating in embedded/background previews.
      this._iv = setInterval(() => this._tick(performance.now()), 1000 / 30);
      this._tick(performance.now());
    }

    setState(s) { if (MOUTH[s]) this.state = s; }
    setLevel(v) { this.level = Math.max(0, Math.min(1, v || 0)); }
    destroy() { clearInterval(this._iv); this.root.remove(); }

    _tick(now) {
      const t = (now - this.t0) / 1000, s = this.state;
      const input = (s === 'listening' || s === 'speaking') ? this.level : 0;
      this.lvl += (input - this.lvl) * (s === 'speaking' ? 0.45 : 0.3);

      if (s === 'listening') {
        // Listening v2: a circle at rest, a soft dome as you start talking,
        // then the base softens and widens the longer you go -- three
        // stages, not a straight blend -- with a small wobble riding on
        // top. Replaces the rounded-hexagon wobble for this state only;
        // every other state is unchanged.
        this.body.style.clipPath = 'none';
        this.body.style.borderRadius = this._domeRadius(t, this.lvl);
      } else {
        // How "geometric" the outline is
        const geoTarget = s === 'speaking' ? 0.8 : s === 'thinking' ? 0.6 : 0;
        this.geo += (geoTarget - this.geo) * 0.12;

        // Outline: circle blended toward a smoothed (rounded-corner) polygon
        const shapeLvl = s === 'thinking' ? 0.15 : this.lvl;
        const spin = s === 'thinking' ? 0.12 : 0.35;
        this.body.style.borderRadius = '';
        this.body.style.clipPath = this._polygon(t, this.geo, shapeLvl, spin);
      }

      // Breathing
      const p = BREATHE[s];
      const breathe = p ? 1 + 0.0175 * (1 - Math.cos((2 * Math.PI * t) / p)) : 1;
      this.body.style.transform = `scale(${breathe.toFixed(4)})`;

      // Color / dim
      this.body.style.background = s === 'paused' ? GREY : PINK;
      this.root.style.opacity = s === 'muted' ? '0.5' : '1';

      // Face motion
      if (s === 'thinking') {
        this.face.style.transform = `rotate(${(-10 + 2 * Math.sin(t * 1.2)).toFixed(2)}deg)`;
      } else {
        this.face.style.transform = 'none';
      }
      this.face.style.transition = 'transform .5s ease-out';
      if (s === 'thinking') this.face.style.transition = 'none';

      // Mouth
      const m = MOUTH[s];
      const sp = s === 'speaking' ? this.lvl : 0;
      this.mouth.style.width = (m.w + sp * 6) + '%';
      this.mouth.style.height = (m.h + sp * 14) + '%';
      this.mouth.style.left = m.x + '%';
      this.mouth.style.transform = s === 'speaking' ? 'translate(-50%, 50%)' : 'translateX(-50%)';
      this.mouth.style.transition = s === 'speaking' ? 'width .07s, height .07s, left .5s' : 'width .3s, height .3s, left .5s';
    }

    _domeRadius(t, l) {
      const ease = x => x * x * (3 - 2 * x);
      const lerp = (a, b, p) => a + (b - a) * p;
      const p1 = ease(Math.min(1, l / 0.5));
      const p2 = ease(Math.min(1, Math.max(0, (l - 0.5) / 0.5)));
      const hBot = l <= 0.5 ? lerp(50, 20, p1) : lerp(20, 82, p2);
      const vBot = l <= 0.5 ? lerp(50, 14, p1) : lerp(14, 26, p2);
      const j = (ph, amp) => Math.sin(t * 1.3 + ph) * amp * l;
      const bl = Math.round(hBot + j(0, 6)), br = Math.round(hBot + j(1.1, 6));
      const tl = Math.round(vBot + j(2.3, 5)), tr = Math.round(vBot + j(3.6, 5));
      return `50% 50% ${bl}% ${br}% / 50% 50% ${tl}% ${tr}%`;
    }

    _polygon(t, g, lvl, spinSpeed) {
      const N = this.facets, M = 120, seg = (2 * Math.PI) / N, pts = [];
      const phi = t * spinSpeed + 0.15 * Math.sin(t * 1.7);
      const poly = th => { const m = (((th - phi) % seg) + seg) % seg; return Math.cos(seg / 2) / Math.cos(m - seg / 2); };
      const depth = g * Math.min(1, 0.55 + lvl * 0.6);
      for (let i = 0; i < M; i++) {
        const th = (i / M) * 2 * Math.PI;
        let sum = 0; for (let w = -6; w <= 6; w++) sum += poly(th + (w / 6) * seg * 0.42); // box filter = rounded corners
        const smooth = sum / 13;
        const jitter = 1 + 0.025 * g * lvl * Math.sin(th * N + t * 5);
        const r = 50 * (1 - depth * (1 - smooth)) * jitter;
        pts.push(`${(50 + r * Math.cos(th)).toFixed(2)}% ${(50 + r * Math.sin(th)).toFixed(2)}%`);
      }
      return `polygon(${pts.join(',')})`;
    }
  }

  global.ThimbleAvatar = ThimbleAvatar;
  if (typeof module !== 'undefined') module.exports = { ThimbleAvatar };
})(typeof window !== 'undefined' ? window : globalThis);
