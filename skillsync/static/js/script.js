/* SkillSync front-end logic. One file, two pages: landing (data-page="landing") and dashboard. */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ---------- API helper ---------- */
  async function api(path, { method = 'GET', body } = {}) {
    const res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'same-origin',
    });
    let data = {};
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (res.status === 401 && document.body.dataset.page === 'dashboard') {
      location.href = '/';
      throw new Error('Please log in again.');
    }
    if (!res.ok) {
      const err = new Error(data.error || 'Something went wrong. Please try again.');
      err.status = res.status;
      throw err;
    }
    return data;
  }

  /* ---------- Toast ---------- */
  let toastTimer;
  function toast(title, msg = '') {
    const el = $('#toast');
    if (!el) return;
    el.innerHTML = `<b class="disp text-xl block">${esc(title)}</b>${msg ? `<span class="ser text-xl leading-tight block">${esc(msg)}</span>` : ''}`;
    el.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('on'), 3800);
  }

  const CHEERS = [
    'Small steps add up.', 'Done beats perfect.', 'That is how it starts.',
    'You are not behind. You are moving.', 'One more box ticked.', 'Future you says thanks.',
  ];
  const cheer = () => CHEERS[Math.floor(Math.random() * CHEERS.length)];

  /* =====================================================================
     LANDING PAGE
     ===================================================================== */
  function initLanding() {
    const d = new Date();
    const stamp = $('#stamp-date');
    if (stamp) {
      stamp.textContent = [d.getDate(), d.getMonth() + 1, String(d.getFullYear()).slice(2)]
        .map((n) => String(n).padStart(2, '0')).join(' ');
    }

    const tabs = { signup: $('#tab-signup'), login: $('#tab-login') };
    const forms = { signup: $('#form-signup'), login: $('#form-login') };

    function show(which) {
      for (const key of ['signup', 'login']) {
        const on = key === which;
        forms[key].classList.toggle('hidden', !on);
        tabs[key].setAttribute('aria-selected', on);
        tabs[key].classList.toggle('opacity-50', !on);
        tabs[key].style.borderColor = on ? 'var(--red)' : 'transparent';
      }
    }
    tabs.signup.addEventListener('click', () => show('signup'));
    tabs.login.addEventListener('click', () => show('login'));
    $('#open-login').addEventListener('click', () => {
      show('login');
      $('#join').scrollIntoView({ behavior: 'smooth' });
      setTimeout(() => $('#li-email').focus(), 400);
    });

    async function submit(form, path, errorEl) {
      const btn = $('button[type="submit"]', form);
      errorEl.textContent = '';
      btn.disabled = true;
      try {
        const data = Object.fromEntries(new FormData(form).entries());
        await api(path, { method: 'POST', body: data });
        location.href = '/dashboard';
      } catch (err) {
        errorEl.textContent = err.message;
        btn.disabled = false;
      }
    }
    forms.signup.addEventListener('submit', (e) => { e.preventDefault(); submit(forms.signup, '/api/register', $('#su-error')); });
    forms.login.addEventListener('submit', (e) => { e.preventDefault(); submit(forms.login, '/api/login', $('#li-error')); });
  }

  /* =====================================================================
     DASHBOARD
     ===================================================================== */
  const state = {
    me: null,
    tab: 'home',
    questions: null,
    levels: [],
    answers: {},
    qIndex: 0,
    retaking: false,
    boardScope: 'all',
    glossQ: '',
    learnBuilt: false,
  };

  async function loadMe() {
    state.me = await api('/api/me');
    $('#chip-streak').textContent = state.me.streak;
    $('#chip-xp').textContent = state.me.xp;
  }

  function firstName() { return (state.me.user.name || 'there').split(' ')[0]; }

  function emptyState(title, text, buttonLabel, goto) {
    return `<div class="panel p-6 mt-4"><h2 class="disp text-3xl mb-2">${esc(title)}</h2>
      <p class="mut mb-4">${esc(text)}</p>
      ${buttonLabel ? `<button class="btn" data-goto="${goto}" type="button">${esc(buttonLabel)}</button>` : ''}</div>`;
  }

  /* ---------- Home ---------- */
  function renderHome() {
    const me = state.me;
    const lv = me.level;
    const a = me.analysis;
    let mission;
    if (!me.user.assessed) {
      mission = `<div class="panel-inv p-5 mt-4"><div class="font-bold text-sm">Start here</div>
        <h2 class="disp text-4xl my-2">Take the skill check</h2>
        <p>13 quick questions, about 3 minutes. You get a score, a plan and 50 XP.</p>
        <button class="btn mt-4 w-full" data-goto="check" type="button">Start the check</button></div>`;
    } else if (me.mission) {
      const m = me.mission;
      mission = `<div class="panel-inv p-5 mt-4"><div class="font-bold text-sm">Today's mission · ${esc(m.skill)} · ${m.minutes} min</div>
        <h2 class="disp text-4xl my-2">${esc(m.title)}</h2>
        <p class="mb-2">${esc(m.detail)}</p>
        <p class="ser text-xl border-t pt-2 mt-3" style="border-color:rgba(74,13,19,.35)">${esc(m.analogy)}</p>
        <button class="btn mt-4 w-full" data-task="${esc(m.id)}" type="button">I did it. Give me ${m.xp} XP</button></div>`;
    } else {
      mission = `<div class="panel-inv p-5 mt-4"><h2 class="disp text-4xl mb-2">Every task done.</h2>
        <p>Retake the skill check to see how far you have come, then help a peer.</p></div>`;
    }

    const focus = a ? a.top_gaps.map((id) => a.skills.find((s) => s.id === id)).filter(Boolean) : [];
    const focusHtml = focus.length ? `<h3 class="disp text-2xl mt-8 mb-2">Focus first</h3>
      <div class="border rule">${focus.map((s) => `<div class="p-3 border-b rule last:border-b-0 flex justify-between gap-3">
        <span class="font-bold">${esc(s.name)}</span><span class="mut text-sm">${esc(s.label)}</span></div>`).join('')}</div>` : '';

    const readiness = a ? `<div class="panel p-4 mt-4"><div class="flex justify-between items-baseline">
        <span class="disp text-2xl">${esc(a.stage)}</span><span class="disp text-3xl">${a.readiness}%</span></div>
        <div class="bar mt-2"><i style="width:${a.readiness}%"></i></div></div>` : '';

    $('#view-home').innerHTML = `
      <h1 class="disp text-5xl mt-2">Hey ${esc(firstName())}.</h1>
      <p class="mut mt-1">${esc(me.user.college)} · ${esc(me.user.course)} · Year ${me.user.year}</p>

      <div class="panel p-4 mt-4">
        <div class="flex justify-between items-baseline">
          <span class="disp text-3xl">Level ${lv.number}: ${esc(lv.name)}</span>
          <span class="mut text-sm">${me.xp}${lv.next_xp ? ' / ' + lv.next_xp : ''} XP</span>
        </div>
        <div class="bar red mt-2"><i style="width:${lv.progress}%"></i></div>
      </div>

      <div class="quote mt-6"><p class="ser text-3xl leading-tight">${esc(me.quote)}</p></div>
      ${mission}
      ${readiness}
      ${focusHtml}

      <h3 class="disp text-2xl mt-8 mb-2">Badges <span class="mut text-base">${me.badges.filter((b) => b.earned).length}/${me.badges.length}</span></h3>
      <div class="grid grid-cols-3 gap-2">
        ${me.badges.map((b) => `<div class="badge ${b.earned ? 'on' : ''}" title="${esc(b.desc)}">
          <div class="disp text-lg">${esc(b.name)}</div><div class="text-xs mt-1">${esc(b.desc)}</div></div>`).join('')}
      </div>`;
  }

  /* ---------- Skill check ---------- */
  async function ensureQuestions() {
    if (state.questions) return;
    const data = await api('/api/questions');
    state.questions = data.questions;
    state.levels = data.levels;
  }

  async function renderCheck() {
    const view = $('#view-check');
    if (state.me.user.assessed && !state.retaking) { return renderResults(view); }
    view.innerHTML = '<p class="mut py-10 text-center">Loading questions...</p>';
    try { await ensureQuestions(); } catch (err) { view.innerHTML = emptyState('Could not load', err.message); return; }

    // pre-fill from the previous attempt so retaking is quick
    if (state.me.analysis && !Object.keys(state.answers).length) {
      state.me.analysis.skills.forEach((s) => { state.answers[s.id] = s.level; });
    }

    const qs = state.questions;
    const q = qs[state.qIndex];
    const pct = Math.round((state.qIndex / qs.length) * 100);
    view.innerHTML = `
      <div class="mt-3 flex justify-between mut text-sm"><span>Question ${state.qIndex + 1} of ${qs.length}</span><span>${esc(q.area)}</span></div>
      <div class="bar red mt-2"><i style="width:${pct}%"></i></div>
      <h2 class="disp text-4xl mt-6 mb-3">${esc(q.text)}</h2>
      <p class="ser text-xl mut mb-5">Quick idea: ${esc(q.analogy)}</p>
      <div role="group" aria-label="Your level">
        ${state.levels.map((l) => `<button class="opt" data-answer="${l.value}" aria-pressed="${state.answers[q.id] === l.value}" type="button">${esc(l.label)}</button>`).join('')}
      </div>
      <div class="mt-3 flex gap-3">
        <button class="btn btn-ghost" data-prev type="button" ${state.qIndex === 0 ? 'disabled' : ''}>Back</button>
        ${state.retaking ? '<button class="btn btn-ghost" data-cancel-retake type="button">Cancel</button>' : ''}
      </div>`;
  }

  async function answerQuestion(value) {
    const q = state.questions[state.qIndex];
    state.answers[q.id] = value;
    if (state.qIndex < state.questions.length - 1) {
      state.qIndex += 1;
      return renderCheck();
    }
    try {
      const before = state.me.level.number;
      await api('/api/assessment', { method: 'POST', body: { answers: state.answers } });
      state.retaking = false;
      state.qIndex = 0;
      await loadMe();
      toast(before === state.me.level.number ? 'Skill check done' : 'Level up!', 'Your roadmap is ready. +50 XP');
      renderCheck();
    } catch (err) {
      toast('Could not save', err.message);
    }
  }

  function renderResults(view) {
    const a = state.me.analysis;
    view.innerHTML = `
      <p class="mut mt-3 text-sm">Your result</p>
      <h1 class="disp mt-1" style="font-size:clamp(3.4rem,16vw,6rem)">${esc(a.stage)}</h1>
      <div class="flex items-baseline gap-3 mt-2"><span class="disp text-5xl">${a.readiness}%</span><span class="mut">ready for a tech career</span></div>
      <div class="bar red mt-2"><i style="width:${a.readiness}%"></i></div>

      <h3 class="disp text-2xl mt-8 mb-2">By area</h3>
      <div class="space-y-3">${a.areas.map((x) => `<div><div class="flex justify-between text-sm"><span class="font-bold">${esc(x.area)}</span><span class="mut">${x.percent}%</span></div>
        <div class="bar"><i style="width:${x.percent}%"></i></div></div>`).join('')}</div>

      <h3 class="disp text-2xl mt-8 mb-2">Biggest gaps first</h3>
      <div class="border rule">${a.skills.map((s) => `<div class="p-3 border-b rule last:border-b-0">
        <div class="flex justify-between gap-3"><span class="font-bold">${esc(s.name)}</span><span class="mut text-sm whitespace-nowrap">${esc(s.label)}</span></div>
        <div class="bar mt-2"><i style="width:${Math.round(s.level / 3 * 100)}%"></i></div></div>`).join('')}</div>

      <div class="mt-6 flex flex-wrap gap-3">
        <button class="btn" data-goto="roadmap" type="button">See my 4-week plan</button>
        <button class="btn btn-ghost" data-retake type="button">Retake the check</button>
      </div>`;
  }

  /* ---------- Roadmap ---------- */
  function renderRoadmap() {
    const view = $('#view-roadmap');
    const me = state.me;
    if (!me.user.assessed) {
      view.innerHTML = emptyState('No plan yet', 'Take the skill check and we will build your 4-week roadmap.', 'Start the check', 'check');
      return;
    }
    if (!me.roadmap.length) {
      view.innerHTML = emptyState('Nothing left to learn here', 'You rated yourself confident in every skill. Help a peer, or build a bigger project.', 'Find peers', 'peers');
      return;
    }
    const openKeys = new Set($$('#view-roadmap details[open]').map((d) => d.dataset.week));
    view.innerHTML = `<h1 class="disp text-5xl mt-2">Your 4-week plan</h1>
      <p class="mut mt-1 mb-4">Built from your gaps. Prerequisites come first. Tap a task when you finish it.</p>` +
      me.roadmap.map((w) => {
        const tasks = w.skills.flatMap((s) => s.tasks);
        const done = tasks.filter((t) => t.done).length;
        const open = openKeys.size ? openKeys.has(String(w.week)) : w.week === 1;
        return `<details class="panel mb-3" data-week="${w.week}" ${open ? 'open' : ''}>
          <summary class="p-4 flex justify-between items-center gap-3">
            <span><span class="disp text-3xl block">Week ${w.week}</span><span class="mut text-sm">${esc(w.focus)}</span></span>
            <span class="disp text-2xl whitespace-nowrap">${done}/${tasks.length}</span>
          </summary>
          <div class="px-4 pb-4">
            ${w.skills.map((s) => `<div class="mt-4">
              <h3 class="disp text-2xl">${esc(s.name)}</h3>
              <p class="ser text-xl mut my-1">${esc(s.analogy)}</p>
              <p class="text-sm mb-3">${esc(s.why)}</p>
              ${s.tasks.map((t) => `<button class="task" data-task="${esc(t.id)}" aria-pressed="${t.done}" type="button">
                <span class="box">${t.done ? '✓' : ''}</span>
                <span class="pr-14"><b>${esc(t.title)}</b><span class="block text-sm opacity-80">${esc(t.detail)}</span>
                <span class="block text-xs mt-1 opacity-70">${t.minutes} min · ${t.xp} XP</span></span></button>`).join('')}
            </div>`).join('')}
          </div></details>`;
      }).join('');
  }

  async function toggleTask(id) {
    const before = { level: state.me.level.number, badges: state.me.badges.filter((b) => b.earned).length };
    try {
      const res = await api(`/api/tasks/${encodeURIComponent(id)}/toggle`, { method: 'POST' });
      await loadMe();
      const earned = state.me.badges.filter((b) => b.earned);
      if (res.done && state.me.level.number > before.level) {
        toast('Level up!', `You are now level ${state.me.level.number}: ${state.me.level.name}`);
      } else if (res.done && earned.length > before.badges) {
        toast('New badge', earned[earned.length - 1].name);
      } else if (res.done) {
        toast('+20 XP', cheer());
      }
      renderCurrent();
    } catch (err) {
      toast('Could not save', err.message);
    }
  }

  /* ---------- Learn (glossary + weekly pulse) ---------- */
  function buildLearn() {
    $('#view-learn').innerHTML = `
      <h1 class="disp text-5xl mt-2">Learn the words</h1>
      <p class="mut mt-1 mb-3">Every term, explained with an everyday analogy. Search anything you heard in class.</p>
      <label class="field" for="gloss-q">Search a term</label>
      <input id="gloss-q" type="search" placeholder="git, API, deploy..." autocomplete="off">
      <div id="gloss-list" class="mt-3"></div>
      <h2 class="disp text-4xl mt-10 mb-1">Weekly pulse</h2>
      <p class="mut mb-3">What is happening in tech, in plain language, and what to do about it.</p>
      <div id="pulse-list"></div>`;
    let timer;
    $('#gloss-q').addEventListener('input', (e) => {
      clearTimeout(timer);
      timer = setTimeout(() => { state.glossQ = e.target.value; loadGlossary(); }, 220);
    });
    state.learnBuilt = true;
    loadGlossary();
    loadPulse();
  }

  async function loadGlossary() {
    const box = $('#gloss-list');
    try {
      const { items } = await api('/api/glossary?q=' + encodeURIComponent(state.glossQ));
      box.innerHTML = items.length ? items.map((g) => `<details class="panel mb-2">
        <summary class="p-3 flex justify-between gap-3"><b class="disp text-xl">${esc(g.term)}</b><span class="mut text-sm">${esc(g.tag)}</span></summary>
        <div class="px-3 pb-3"><p class="ser text-2xl leading-tight">${esc(g.analogy)}</p>
        <p class="mut text-sm mt-2">Example: ${esc(g.example)}</p></div></details>`).join('')
        : '<p class="mut py-4">No match. Try another word, like "commit" or "cloud".</p>';
    } catch (err) { box.innerHTML = `<p class="mut">${esc(err.message)}</p>`; }
  }

  async function loadPulse() {
    const box = $('#pulse-list');
    try {
      const { items } = await api('/api/pulse');
      box.innerHTML = items.map((p) => `<div class="panel-inv p-4 mb-3">
        <div class="text-xs font-bold">${esc(p.tag)}</div>
        <h3 class="disp text-3xl my-1">${esc(p.title)}</h3>
        <p>${esc(p.body)}</p>
        <p class="mt-2 text-sm"><b>Why it matters:</b> ${esc(p.why)}</p>
        <p class="mt-1 text-sm"><b>Try this:</b> ${esc(p.action)}</p></div>`).join('');
    } catch (err) { box.innerHTML = `<p class="mut">${esc(err.message)}</p>`; }
  }

  function renderLearn() { if (!state.learnBuilt) buildLearn(); }

  /* ---------- Peers ---------- */
  async function renderPeers() {
    const view = $('#view-peers');
    if (!state.me.user.assessed) {
      view.innerHTML = emptyState('Peers need your skill check', 'We match you with students who are strong where you are weak, and the other way round.', 'Start the check', 'check');
      return;
    }
    view.innerHTML = '<p class="mut py-10 text-center">Finding your matches...</p>';
    let items = [];
    try { items = (await api('/api/peers')).items; } catch (err) { view.innerHTML = emptyState('Could not load peers', err.message); return; }

    const cards = items.length ? items.map((p) => {
      let action;
      if (p.status === 'mutual') {
        action = p.contact
          ? `<div class="panel-inv p-3 mt-3 text-sm"><b>You are connected.</b> Reach them at: ${esc(p.contact)}</div>`
          : '<div class="panel-inv p-3 mt-3 text-sm"><b>You are connected.</b> They have not added contact details yet.</div>';
      } else if (p.status === 'sent') {
        action = '<button class="btn btn-ghost mt-3 w-full" disabled type="button">Request sent</button>';
      } else if (p.status === 'incoming') {
        action = `<button class="btn mt-3 w-full" data-connect="${p.id}" type="button">They want to connect. Accept</button>`;
      } else {
        action = `<button class="btn mt-3 w-full" data-connect="${p.id}" type="button">Connect</button>`;
      }
      return `<div class="panel p-4 mb-3"><div class="flex justify-between gap-3">
          <h3 class="disp text-3xl">${esc(p.name)}</h3><span class="mut text-sm whitespace-nowrap">Match ${p.score}</span></div>
        <p class="mut text-sm">${esc(p.college)} · ${esc(p.course)} · Year ${p.year}</p>
        <ul class="mt-2 text-sm list-disc pl-5">${p.reasons.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>${action}</div>`;
    }).join('') : `<div class="panel p-5"><h3 class="disp text-3xl mb-2">No matches yet</h3>
      <p class="mut mb-3">You are early. Invite classmates so there is someone to match with.</p>
      <button class="btn" data-share type="button">Share SkillSync</button></div>`;

    view.innerHTML = `<h1 class="disp text-5xl mt-2">Your peers</h1>
      <p class="mut mt-1 mb-4">Matched on skills: who can help you, who you can help, and who is starting out like you.</p>
      <div class="panel p-4 mb-5"><label class="field" for="contact">Your contact (shown only after you both connect)</label>
        <div class="flex gap-2"><input id="contact" maxlength="80" placeholder="WhatsApp, Instagram or LinkedIn" value="${esc(state.me.user.contact)}">
        <button class="btn" data-save-contact type="button">Save</button></div></div>
      ${cards}`;
  }

  /* ---------- Leaderboard ---------- */
  async function renderBoard() {
    const view = $('#view-board');
    view.innerHTML = '<p class="mut py-10 text-center">Loading the board...</p>';
    let data;
    try { data = await api('/api/leaderboard?scope=' + state.boardScope); } catch (err) { view.innerHTML = emptyState('Could not load', err.message); return; }
    view.innerHTML = `<h1 class="disp text-5xl mt-2">Leaderboard</h1>
      <p class="mut mt-1 mb-3">${data.my_rank ? `You are #${data.my_rank} of ${data.total}.` : ''} XP comes from the skill check and finished tasks.</p>
      <div class="flex gap-2 mb-3">
        <button class="btn ${state.boardScope === 'all' ? '' : 'btn-ghost'}" data-scope="all" type="button">Everyone</button>
        <button class="btn ${state.boardScope === 'college' ? '' : 'btn-ghost'}" data-scope="college" type="button">My college</button>
      </div>
      <div class="border rule">${data.items.map((r) => `<div class="p-3 border-b rule last:border-b-0 flex items-center gap-3 ${r.me ? 'panel-inv' : ''}">
        <span class="disp text-2xl w-10">${r.rank}</span>
        <span class="flex-1"><b>${esc(r.name)}</b><span class="block text-xs ${r.me ? '' : 'mut'}">${esc(r.college)}</span></span>
        <span class="disp text-2xl">${r.xp}</span></div>`).join('')}</div>`;
  }

  /* ---------- Router ---------- */
  const TABS = ['home', 'check', 'roadmap', 'learn', 'peers', 'board'];
  const RENDERERS = { home: renderHome, check: renderCheck, roadmap: renderRoadmap, learn: renderLearn, peers: renderPeers, board: renderBoard };

  function renderCurrent() { RENDERERS[state.tab](); }

  function setTab(name) {
    if (!TABS.includes(name)) name = 'home';
    state.tab = name;
    history.replaceState(null, '', '#' + name);
    $$('.view').forEach((v) => v.classList.add('hidden'));
    $('#view-' + name).classList.remove('hidden');
    $$('.tab').forEach((t) => (t.dataset.tab === name ? t.setAttribute('aria-current', 'page') : t.removeAttribute('aria-current')));
    window.scrollTo({ top: 0 });
    renderCurrent();
  }

  /* ---------- Events ---------- */
  document.addEventListener('click', async (e) => {
    if (document.body.dataset.page !== 'dashboard') return;
    const t = e.target.closest('button');
    if (!t) return;

    if (t.dataset.tab) return setTab(t.dataset.tab);
    if (t.dataset.goto) return setTab(t.dataset.goto);
    if (t.dataset.task) return toggleTask(t.dataset.task);
    if (t.dataset.answer !== undefined) return answerQuestion(Number(t.dataset.answer));
    if (t.hasAttribute('data-prev')) { state.qIndex = Math.max(0, state.qIndex - 1); return renderCheck(); }
    if (t.hasAttribute('data-retake')) { state.retaking = true; state.qIndex = 0; state.answers = {}; return renderCheck(); }
    if (t.hasAttribute('data-cancel-retake')) { state.retaking = false; state.qIndex = 0; return renderCheck(); }
    if (t.dataset.scope) { state.boardScope = t.dataset.scope; return renderBoard(); }

    if (t.dataset.connect) {
      try {
        const res = await api('/api/connect/' + t.dataset.connect, { method: 'POST' });
        toast(res.status === 'mutual' ? 'Connected!' : 'Request sent', res.status === 'mutual' ? 'You can now see their contact.' : 'They will see it when they open Peers.');
        renderPeers();
      } catch (err) { toast('Could not connect', err.message); }
      return;
    }
    if (t.hasAttribute('data-save-contact')) {
      try {
        await api('/api/profile', { method: 'POST', body: { contact: $('#contact').value } });
        await loadMe();
        toast('Saved', 'Matches see this only after you both connect.');
      } catch (err) { toast('Could not save', err.message); }
      return;
    }
    if (t.hasAttribute('data-share')) {
      const url = location.origin;
      if (navigator.share) { try { await navigator.share({ title: 'SkillSync', text: 'Learn tech basics with analogies and a weekly plan.', url }); } catch (_) { /* cancelled */ } }
      else { try { await navigator.clipboard.writeText(url); toast('Link copied', 'Paste it in your class group.'); } catch (_) { toast('Share this link', url); } }
      return;
    }
    if (t.id === 'logout') {
      await api('/api/logout', { method: 'POST' }).catch(() => {});
      location.href = '/';
    }
  });

  async function initDashboard() {
    try {
      await loadMe();
    } catch (err) {
      $('#loading').classList.add('hidden');
      const box = $('#load-error');
      box.classList.remove('hidden');
      box.innerHTML = `<h2 class="disp text-3xl mb-2">Could not load</h2><p class="mut">${esc(err.message)}</p>`;
      return;
    }
    $('#loading').classList.add('hidden');
    window.addEventListener('hashchange', () => setTab(location.hash.slice(1)));
    const start = location.hash.slice(1) || (state.me.user.assessed ? 'home' : 'check');
    setTab(start);
  }

  if (document.body.dataset.page === 'landing') initLanding();
  else initDashboard();
})();
