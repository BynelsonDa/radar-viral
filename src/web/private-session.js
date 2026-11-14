// Logged-in account toolbar, available only in private Flask deployment.
(async () => {
  try {
    const response = await fetch('/api/session', {cache:'no-store'});
    if (!response.ok) return;
    const {username, csrf_token} = await response.json();
    if (!username || !csrf_token) return;
    const header = document.querySelector('header');
    if (!header) return;
    const form = document.createElement('form');
    form.method = 'post';
    form.action = '/logout';
    form.style.cssText = 'display:flex;gap:10px;align-items:center;margin-left:auto';
    const hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = 'csrf_token';
    hidden.value = csrf_token;
    const user = document.createElement('span');
    user.textContent = username;
    user.style.cssText = 'font-size:12px;color:#a7bcd3';
    const button = document.createElement('button');
    button.type = 'submit';
    button.textContent = 'Salir';
    button.style.cssText = 'border:1px solid #3569a1;border-radius:8px;background:#122b4b;color:#fff;padding:8px;cursor:pointer';
    form.append(hidden, user, button);
    header.append(form);
  } catch { /* The page remains usable if the header cannot be rendered. */ }
})();
