const chatEl = document.getElementById('chat');
const composer = document.getElementById('composer');
const composerInput = document.getElementById('composer-input');

const modalBackdrop = document.getElementById('modal-backdrop');
const modalChat = document.getElementById('modal-chat');
const modalComposer = document.getElementById('modal-composer');
const modalInput = document.getElementById('modal-input');
const modalSend = document.getElementById('modal-send');
const modalClose = document.getElementById('modal-close');
const modalAvatar = document.getElementById('modal-avatar');
const modalName = document.getElementById('modal-name');
const modalReadout = document.getElementById('modal-readout');

let state = 'ask_role'; // ask_role -> ready -> in_modal -> done
let scenario = null;
let modalHistory = []; // [{from: 'them'|'me', text}]

function addBubble(container, kind, text) {
  const div = document.createElement('div');
  div.className = `bubble ${kind}`;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
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

function initials(name) {
  return name
    .replace(/^(the|a)\s+/i, '')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

addBubble(
  chatEl,
  'bot',
  "Most people think they're pretty good at this. We want to find out, for real, not with a quiz where you can see the right answer."
);
setTimeout(() => {
  addBubble(chatEl, 'bot', "First: what's your job?");
}, 300);

composer.addEventListener('submit', async (e) => {
  e.preventDefault();
  const value = composerInput.value.trim();
  if (!value) return;

  if (state === 'ask_role') {
    addBubble(chatEl, 'me', value);
    composerInput.value = '';
    composerInput.disabled = true;

    const res = await fetch('/api/scenario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: value }),
    });
    const data = await res.json();
    scenario = { role: value, ...data };

    addBubble(chatEl, 'bot', "Got it. Here's the situation.");
    setTimeout(() => {
      addBubble(chatEl, 'bot', data.scenario_text);
      setTimeout(() => {
        addBubble(chatEl, 'bot', `${data.counterpart_name} is about to message you first. Ready?`);
        addCta(chatEl, 'Start the conversation', openModal);
      }, 400);
    }, 400);

    state = 'ready';
  }
});

function openModal() {
  modalBackdrop.classList.remove('hidden');
  modalName.textContent = scenario.counterpart_name;
  modalAvatar.textContent = initials(scenario.counterpart_name);
  modalHistory = [{ from: 'them', text: scenario.opening_line }];
  modalChat.innerHTML = '';
  modalReadout.classList.add('hidden');
  modalComposer.classList.remove('hidden');
  addBubble(modalChat, 'them', scenario.opening_line);
  modalInput.disabled = false;
  modalSend.disabled = false;
  modalInput.focus();
  state = 'in_modal';
}

function closeModal() {
  modalBackdrop.classList.add('hidden');
}

modalClose.addEventListener('click', closeModal);

modalComposer.addEventListener('submit', async (e) => {
  e.preventDefault();
  const value = modalInput.value.trim();
  if (!value) return;

  addBubble(modalChat, 'me', value);
  modalInput.value = '';
  modalInput.disabled = true;
  modalSend.disabled = true;

  const res = await fetch('/api/reply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role: scenario.role, history: modalHistory, message: value }),
  });
  const data = await res.json();

  modalHistory.push({ from: 'me', text: value });
  addBubble(modalChat, 'them', data.reply);
  modalHistory.push({ from: 'them', text: data.reply });

  if (data.done) {
    modalComposer.classList.add('hidden');
    addCta(modalChat, 'See what this shows', showReadout);
  } else {
    modalInput.disabled = false;
    modalSend.disabled = false;
    modalInput.focus();
  }
});

async function showReadout() {
  modalReadout.classList.remove('hidden');
  modalReadout.innerHTML = '<span class="readout-tag">What this shows</span><div>Reading the conversation&hellip;</div>';

  const res = await fetch('/api/readout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role: scenario.role, history: modalHistory }),
  });
  const data = await res.json();
  modalReadout.innerHTML = `<span class="readout-tag">What this shows</span><div>${data.readout.replace(/\n/g, '<br><br>')}</div>`;
  state = 'done';
}
