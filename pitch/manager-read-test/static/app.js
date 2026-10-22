const BASE_PATH = location.pathname.replace(/[^/]*$/, '');
function apiPath(p) {
  return BASE_PATH.replace(/\/$/, '') + '/' + p.replace(/^\//, '');
}

const chatEl = document.getElementById('chat');
const composer = document.getElementById('composer');
const composerInput = document.getElementById('composer-input');

const modalBackdrop = document.getElementById('modal-backdrop');
const modalChat = document.getElementById('modal-chat');
const modalComposer = document.getElementById('modal-composer');
const modalInput = document.getElementById('modal-input');
const modalSend = document.getElementById('modal-send');
const modalClose = document.getElementById('modal-close');
const modalSub = document.getElementById('modal-sub');

const QUESTIONS = [
  { key: 'what', prompt: "What's happening here?" },
  { key: 'why', prompt: 'Why is it happening?' },
  { key: 'do', prompt: 'What do you do about it?' },
];

let state = 'ask_job'; // ask_job -> ready -> answer_<key> -> scoring -> done
let job = '';
let thread = null; // {thread_id, role_a, role_b, messages}
let speakerSide = {}; // name -> 'a' | 'b'
let answers = {};
let questionIndex = 0;

function addBubble(container, kind, text) {
  const div = document.createElement('div');
  div.className = `bubble ${kind}`;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function addThreadBubble(container, name, text, side) {
  const wrap = document.createElement('div');
  wrap.className = `bubble-wrap${side === 'b' ? ' align-right' : ''}`;
  const label = document.createElement('div');
  label.className = 'bubble-name';
  label.textContent = name;
  const bubble = document.createElement('div');
  bubble.className = `bubble them-${side}`;
  bubble.textContent = text;
  wrap.appendChild(label);
  wrap.appendChild(bubble);
  container.appendChild(wrap);
  container.scrollTop = container.scrollHeight;
}

function addCta(container, label, onClick) {
  const btn = document.createElement('button');
  btn.className = 'cta-button';
  btn.type = 'button';
  btn.textContent = label;
  btn.addEventListener('click', onClick, { once: true });
  container.appendChild(btn);
  container.scrollTop = container.scrollHeight;
  return btn;
}

addBubble(chatEl, 'bot', "First: what's your job, or what does your team do?");

composer.addEventListener('submit', async (e) => {
  e.preventDefault();
  const value = composerInput.value.trim();
  if (!value || state !== 'ask_job') return;

  job = value;
  addBubble(chatEl, 'me', value);
  composerInput.value = '';
  composerInput.disabled = true;
  state = 'loading_thread';

  addBubble(chatEl, 'bot', "Pulling up a thread between two people on a team like yours…");

  const res = await fetch(apiPath('/api/thread'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job }),
  });
  thread = await res.json();

  addBubble(chatEl, 'bot', "It's already gone sideways. Open it up and read it for yourself.");
  addCta(chatEl, 'Read the thread', openModal);
  state = 'ready';
});

function openModal() {
  modalBackdrop.classList.remove('hidden');
  modalSub.textContent = `${thread.role_a} · ${thread.role_b}`;
  modalChat.innerHTML = '';
  speakerSide = {};

  thread.messages.forEach((m, i) => {
    if (!(m.from in speakerSide)) {
      speakerSide[m.from] = Object.keys(speakerSide).length === 0 ? 'a' : 'b';
    }
    setTimeout(() => {
      addThreadBubble(modalChat, m.from, m.text, speakerSide[m.from]);
      if (i === thread.messages.length - 1) {
        setTimeout(() => startQuestions(), 500);
      }
    }, i * 400);
  });
}

function closeModal() {
  modalBackdrop.classList.add('hidden');
}

modalClose.addEventListener('click', closeModal);

function startQuestions() {
  questionIndex = 0;
  answers = {};
  modalComposer.classList.remove('hidden');
  askQuestion();
}

function askQuestion() {
  const q = QUESTIONS[questionIndex];
  addBubble(modalChat, 'bot', q.prompt);
  state = `answer_${q.key}`;
  modalInput.disabled = false;
  modalSend.disabled = false;
  modalInput.focus();
}

modalComposer.addEventListener('submit', async (e) => {
  e.preventDefault();
  const value = modalInput.value.trim();
  if (!value || !state.startsWith('answer_')) return;

  const key = state.slice('answer_'.length);
  answers[key] = value;
  addBubble(modalChat, 'me', value);
  modalInput.value = '';
  modalInput.disabled = true;
  modalSend.disabled = true;

  questionIndex += 1;
  if (questionIndex < QUESTIONS.length) {
    askQuestion();
  } else {
    await runScore();
  }
});

async function runScore() {
  state = 'scoring';
  modalComposer.classList.add('hidden');
  addBubble(modalChat, 'bot', 'Reading your diagnosis against the thread…');

  const res = await fetch(apiPath('/api/score'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      thread_id: thread.thread_id,
      messages: thread.messages,
      what: answers.what,
      why: answers.why,
      do: answers.do,
    }),
  });
  const data = await res.json();
  showReadout(data);
}

function showReadout(data) {
  const readoutEl = document.createElement('div');
  readoutEl.className = 'readout';
  const rows = [
    { label: "What's happening", key: 'what' },
    { label: 'Why', key: 'why' },
    { label: 'What to do', key: 'do' },
  ];
  readoutEl.innerHTML = `
    <div class="score-row">
      <div class="score-number">${data.score}</div>
      <div class="score-meta">
        <div class="score-label">${data.archetype_label}</div>
        <div class="score-sub">out of 100, reading the thread</div>
      </div>
    </div>
    <span class="readout-tag">What this shows</span>
    <div>${data.archetype_blurb}</div>
    <div class="readout-norm">${data.norm_note}</div>
    <div class="breakdown">
      ${rows
        .map((r) => {
          const b = data.breakdown[r.key];
          return `<div class="breakdown-row">
            <div class="breakdown-row-head"><span>${r.label}</span><span>${b.band} · ${b.points} pts</span></div>
            <div class="breakdown-note">${b.note}</div>
          </div>`;
        })
        .join('')}
    </div>
    <div class="readout-cta">
      <div class="readout-cta-text">This is a diagnosis. Mend is the tool that helps your team actually fix the seam, without you in the room.</div>
      <a class="cta-button cta-link" href="https://mend-mvp.onrender.com/" target="_blank" rel="noopener">Try Mend for your team</a>
    </div>
  `;
  modalChat.appendChild(readoutEl);
  modalChat.scrollTop = modalChat.scrollHeight;
  state = 'done';
}
