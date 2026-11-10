// Runs in the head so the saved preference or default Forge theme applies before first paint.
(() => {
  const key = 'ceim-theme';
  const root = document.documentElement;
  let theme = 'forge';
  try { if (localStorage.getItem(key) === 'atlas') theme = 'atlas'; } catch {}
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
    if (event.key === key && document.getElementById('theme-toggle')) apply(event.newValue === 'atlas' ? 'atlas' : 'forge');
  });
})();
