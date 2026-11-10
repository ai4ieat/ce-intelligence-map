// Runs in the head so a saved theme is applied before the first paint.
(() => {
  const key = 'ceim-theme';
  const root = document.documentElement;
  let theme = 'atlas';
  try { if (['forge','farm'].includes(localStorage.getItem(key))) theme = 'forge'; } catch {}
  root.dataset.theme = theme;
  function apply(next) {
    theme = next;
    root.dataset.theme = theme;
    const button = document.getElementById('theme-toggle');
    const forge = theme === 'forge';
    button.setAttribute('aria-pressed', String(forge));
    button.setAttribute('aria-label', forge ? 'ธีม Forge เปิดอยู่ — สลับเป็น Formal' : 'ธีม Formal เปิดอยู่ — สลับเป็น Forge');
    button.title = forge ? 'สลับเป็น Formal' : 'สลับเป็น Forge';
    button.querySelector('.theme-label').textContent = forge ? 'Forge' : 'Formal';
    button.querySelector('.theme-icon').textContent = forge ? '◈' : '◐';
    try { localStorage.setItem(key, theme); } catch {}
    document.dispatchEvent(new CustomEvent('aim-theme-change', {detail: theme}));
  }
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('theme-toggle').addEventListener('click', () => apply(theme === 'forge' ? 'atlas' : 'forge'));
    apply(theme);
  });
  window.addEventListener('storage', event => {
    if (event.key === key && document.getElementById('theme-toggle')) apply(['forge','farm'].includes(event.newValue) ? 'forge' : 'atlas');
  });
})();
