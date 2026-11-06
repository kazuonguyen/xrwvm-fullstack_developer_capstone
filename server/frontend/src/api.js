export async function api(path, options = {}) {
  const session = await fetch('/djangoapp/session', {credentials:'same-origin'}).then(r => r.json());
  const response = await fetch('/djangoapp/' + path, {
    credentials:'same-origin', ...options,
    headers:{'Content-Type':'application/json', 'X-CSRFToken':session.csrfToken, ...options.headers}
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'The request could not be completed.');
  return data;
}
