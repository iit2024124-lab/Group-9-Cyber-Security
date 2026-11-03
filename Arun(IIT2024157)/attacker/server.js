/** Attacker web server (http://127.0.0.1:4000) - only serves attacker.html.
 *  Open it via 127.0.0.1 (not localhost) so the browser treats it as a DIFFERENT site from localhost:3000. */
const http = require('http'), fs = require('fs'), path = require('path');
http.createServer((req, res) => {
  console.log(`[ATTACKER] ${req.method} ${req.url}`);
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(fs.readFileSync(path.join(__dirname, 'attacker.html')));
}).listen(4000, () => console.log('Attacker page: http://127.0.0.1:4000'));
