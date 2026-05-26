/**
 * components.js
 *
 * Add <script src="../components.js"></script> to any quiz page inside a
 * category folder (history/, philosophy/, fiction/). No other HTML changes
 * needed -- this script injects a breadcrumb nav automatically.
 *
 * Theming is fully inherited from the page's --qe-* CSS custom properties,
 * so the nav matches each quiz's visual identity without extra work.
 *
 * To support a new category folder, add its name to LABELS below.
 */
(function () {
  const LABELS = {
    history:    'History',
    philosophy: 'Philosophy',
    fiction:    'Fiction',
  };

  function mount() {
    // Second-to-last path segment is the containing folder.
    // Works for both file:// and http:// origins.
    const segs  = window.location.pathname.split('/').filter(Boolean);
    const dir   = segs.length >= 2 ? segs[segs.length - 2] : '';
    const label = LABELS[dir];
    if (!label) return;

    const nav = document.createElement('nav');
    nav.id = 'qe-breadcrumb';
    nav.innerHTML =
      '<a href="../index.html" class="qe-bc-link">Home</a>' +
      '<span class="qe-bc-sep">/</span>' +
      '<a href="index.html" class="qe-bc-link qe-bc-here">' + label + '</a>';

    // Prepend inside <header> so it sits above the quiz title, inheriting
    // container padding. Falls back to .container or <body>.
    const target = document.querySelector('header') ||
                   document.querySelector('.container') ||
                   document.body;
    target.prepend(nav);

    const style = document.createElement('style');
    style.textContent =
      '#qe-breadcrumb{' +
        'display:flex;align-items:center;gap:0.45rem;margin-bottom:24px;' +
        'font-family:var(--qe-font-label,monospace);font-size:0.64rem;' +
        'letter-spacing:0.2em;text-transform:uppercase;' +
      '}' +
      '.qe-bc-link{' +
        'color:var(--qe-text-muted,#888);text-decoration:none;transition:color 0.15s;' +
      '}' +
      '.qe-bc-link:hover{color:var(--qe-accent,#c8a96e);}' +
      '.qe-bc-here{color:var(--qe-accent,#c8a96e);}' +
      '.qe-bc-sep{color:var(--qe-text-muted,#888);opacity:0.4;user-select:none;}';
    document.head.appendChild(style);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
