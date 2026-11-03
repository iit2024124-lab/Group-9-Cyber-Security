
 
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { URL } = require('url');

const PORT = 3000;
const COOKIE = 'sid_vuln';

const users = {
  alice: { password: 'alice123', theme: 'light' },
  bob:   { password: 'bob123',   theme: 'light' },
};
const sessions = {}; // sid -> username

const view = (name, vars = {}) => {
  let html = fs.readFileSync(path.join(__dirname, 'views', name), 'utf8');
  for (const [k, v] of Object.entries(vars)) html = html.split(`{{${k}}}`).join(v);
  return html;
};
const parseCookies = (req) =>
  Object.fromEntries((req.headers.cookie || '').split(';').filter(Boolean).map((c) => {
    const i = c.indexOf('='); return [c.slice(0, i).trim(), c.slice(i + 1).trim()];
  }));
const currentUser = (req) => sessions[parseCookies(req)[COOKIE]];
const send = (res, code, body, headers = {}) => {
  res.writeHead(code, { 'Content-Type': 'text/html; charset=utf-8', ...headers });
  res.end(body);
};
const redirect = (res, to, headers = {}) => { res.writeHead(302, { Location: to, ...headers }); res.end(); };
const readBody = (req) => new Promise((resolve) => {
  let data = ''; req.on('data', (c) => (data += c)); req.on('end', () => resolve(new URLSearchParams(data)));
});

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const user = currentUser(req);
  console.log(`[VULN] ${req.method} ${url.pathname}${url.search}  user=${user || '-'}  referer=${req.headers.referer || '-'}`);



  if (req.method === 'GET' && url.pathname === '/') return redirect(res, user ? '/profile' : '/login');

  if (req.method === 'GET' && url.pathname === '/login') return send(res, 200, view('login.html', { error: '' }));

  if (req.method === 'POST' && url.pathname === '/login') {
    const body = await readBody(req);
    const u = body.get('username'), p = body.get('password');
    if (users[u] && users[u].password === p) {
      const sid = crypto.randomBytes(24).toString('hex');
      sessions[sid] = u;
    
      return redirect(res, '/profile', { 'Set-Cookie': `${COOKIE}=${sid}; HttpOnly; Path=/` });
    }
    return send(res, 401, view('login.html', { error: 'Invalid username or password' }));
  }

  if (req.method === 'GET' && url.pathname === '/profile') {
    if (!user) return redirect(res, '/login');
    return send(res, 200, view('profile.html', { user, theme: users[user].theme }));
  }


  if (req.method === 'GET' && url.pathname === '/profile/theme') {
    if (!user) return redirect(res, '/login');
    const value = url.searchParams.get('value');
    if (value === 'light' || value === 'dark') {
      users[user].theme = value;
      console.log(`[VULN] >>> theme of "${user}" changed to "${value}"`);
    }
    return redirect(res, '/profile');
  }



  if (req.method === 'GET' && url.pathname === '/logout') {
    delete sessions[parseCookies(req)[COOKIE]];
    return redirect(res, '/login', { 'Set-Cookie': `${COOKIE}=; Max-Age=0; Path=/` });
  }

  send(res, 404, '<h1>404</h1>');
}).listen(PORT, () => console.log(`Vulnerable app running on http://localhost:${PORT}`));
