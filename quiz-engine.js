/**
 * quiz-engine.js
 *
 * Shared quiz logic. Each quiz page defines window.QUIZ before loading this
 * script, then places <div id="quiz-root"></div> where the quiz should appear.
 *
 * window.QUIZ shape:
 *   {
 *     questions: [{ tag?, tagLabel?, text|q, opts|options, ans|answer, exp|explanation|fb|explain }],
 *     verdicts:  [{ min: 0.0–1.0, v: "title", n: "note" }],   // sorted descending by min
 *     config?: {
 *       questionWord?:  "Question"       (label prefix)
 *       nextLabel?:     "Next →"
 *       finishLabel?:   "See Results →"
 *       restartLabel?:  "Retake Quiz"
 *       bdTitle?:       "Question breakdown"
 *       denomText?:     "correct answers out of N"  (auto if omitted)
 *       scorePreamble?: ""               (text above score number)
 *       shuffle?:       false
 *     }
 *   }
 */
(function () {
  const Q = window.QUIZ;
  if (!Q) { console.error('quiz-engine: window.QUIZ not defined'); return; }

  const cfg = Q.config || {};
  const qword      = cfg.questionWord  || 'Question';
  const nextLabel  = cfg.nextLabel     || 'Next →';
  const finishLabel= cfg.finishLabel   || 'See Results →';
  const restartLbl = cfg.restartLabel  || 'Retake Quiz';
  const bdTitle    = cfg.bdTitle       || 'Question breakdown';
  const scorePre   = cfg.scorePreamble || '';

  let qs = Q.questions || [];
  if (cfg.shuffle) qs = [...qs].sort(() => Math.random() - 0.5);

  const denomText = cfg.denomText !== undefined
    ? cfg.denomText
    : ('correct answers out of ' + qs.length);

  let cur = 0, score = 0, answered = [], userAns = [];

// Initialize the quiz
  function init() {
    const root = document.getElementById('quiz-root');
    if (!root) { console.error('quiz-engine: #quiz-root not found'); return; }

    root.innerHTML = `
      <div id="qe-quiz-section">
        <div class="meta-bar">
          <span class="meta-label" id="qe-label"></span>
          <span class="meta-label" id="qe-tally">- / -</span>
        </div>
        <div class="progress-track"><div class="progress-fill" id="qe-prog" style="width:0%"></div></div>
        <div id="qe-q-area"></div>
        <div class="nav">
          <span class="running-score" id="qe-live"></span>
          <button class="btn primary" id="qe-next" disabled></button>
        </div>
      </div>
      <div class="score-screen" id="qe-score-screen">
        <div class="score-hero">
          ${scorePre ? `<div class="score-pre">${scorePre}</div>` : ''}
          <div class="score-num" id="qe-final"></div>
          <div class="score-denom">${denomText}</div>
          <div class="verdict" id="qe-verdict"></div>
          <div class="verdict-note" id="qe-vnote"></div>
        </div>
        <div class="breakdown">
          <div class="bd-title">${bdTitle}</div>
          <div id="qe-bdlist"></div>
        </div>
        <button class="btn primary" id="qe-restart">${restartLbl}</button>
      </div>`;

    document.getElementById('qe-next').addEventListener('click', next);
    document.getElementById('qe-restart').addEventListener('click', restart);
    render();
  }

// Render the quiz
  function render() {
    const q     = qs[cur];
    const total = qs.length;

    document.getElementById('qe-label').textContent =
      qword + ' ' + (cur + 1) + ' of ' + total;
    document.getElementById('qe-tally').textContent =
      cur > 0 ? score + ' / ' + cur : '- / -';
    document.getElementById('qe-prog').style.width =
      (cur / total * 100) + '%';
    document.getElementById('qe-live').textContent = '';

    const btn = document.getElementById('qe-next');
    btn.disabled = true;
    btn.textContent = cur === total - 1 ? finishLabel : nextLabel;

    const tagLabel = q.tagLabel || q.tag || q.category || '';
    const tagKey   = (q.tag || q.category || '').toLowerCase().replace(/\s+/g, '-');
    const text     = q.text || q.q || '';
    const opts     = q.opts || q.options || [];
    const diff     = q.diff || '';

    document.getElementById('qe-q-area').innerHTML = `
      <div class="question-card" data-num="${cur + 1}">
        ${tagLabel
          ? `<div class="q-tag${tagKey ? ' tag-' + tagKey : ''}">${tagLabel}</div>`
          : ''}
        ${diff ? `<span class="diff-badge diff-${diff}">${diff}</span>` : ''}
        <div class="q-text">${text}</div>
        <div class="options">
          ${opts.map((o, i) => `
            <button class="option" onclick="window.__qe.pick(${i})" data-i="${i}">
              <span class="opt-letter">${String.fromCharCode(65 + i)}.</span>
              <span class="opt-text">${o}</span>
            </button>`).join('')}
        </div>
        <div class="explanation" id="qe-exp"></div>
      </div>`;
  }

    // Pick asnwer
  function pick(idx) {
    if (document.querySelector('.option.correct')) return;
    const q   = qs[cur];
    const ans = q.ans ?? q.answer ?? 0;
    const exp = q.exp || q.explanation || q.fb || q.explain || '';
    const els = document.querySelectorAll('.option');

    els.forEach(o => o.classList.add('disabled'));
    if (idx === ans) { els[idx].classList.add('correct'); score++; }
    else             { els[idx].classList.add('wrong');   els[ans].classList.add('correct'); }

    userAns[cur]  = idx;
    answered[cur] = idx === ans;

    const expEl = document.getElementById('qe-exp');
    expEl.innerHTML = exp;
    expEl.classList.add('show');

    document.getElementById('qe-next').disabled = false;
    document.getElementById('qe-tally').textContent = score + ' / ' + (cur + 1);
  }

 // Next question
  function next() {
    cur++;
    if (cur >= qs.length) finish();
    else { render(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  }

// Finish processing
  function finish() {
    document.getElementById('qe-quiz-section').style.display = 'none';
    document.getElementById('qe-score-screen').classList.add('show');

    const pct = score / qs.length;
    document.getElementById('qe-final').textContent = score + '/' + qs.length;

    const verdicts = Q.verdicts || [];
    let v = '', n = '';
    for (const entry of verdicts) {
      if (pct >= entry.min) { v = entry.v; n = entry.n; break; }
    }
    document.getElementById('qe-verdict').textContent = v;
    document.getElementById('qe-vnote').textContent   = n;

    document.getElementById('qe-bdlist').innerHTML = qs.map((q, i) => {
      const t = q.text || q.q || '';
      return `<div class="bd-row">
        <span class="bd-q">${i + 1}. ${t.length > 72 ? t.slice(0, 72) + '…' : t}</span>
        <span class="bd-mark ${answered[i] ? 'tick' : 'cross'}">${answered[i] ? '✓' : '✗'}</span>
      </div>`;
    }).join('');

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

// Restart quiz
  function restart() {
    cur = 0; score = 0; answered = []; userAns = [];
    document.getElementById('qe-score-screen').classList.remove('show');
    document.getElementById('qe-quiz-section').style.display = '';
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  window.__qe = { pick };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
