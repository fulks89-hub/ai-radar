import { createReadStream } from 'node:fs';
import { access } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
import { brainStatus, stageTrend } from './scripts/brain-capture.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), 'dist');
const port = Number(process.env.PORT || 4174);
const host = process.env.HOST || '127.0.0.1';
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
const securityHeaders = {
  'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  'referrer-policy': 'no-referrer',
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY',
};
const headers = (extra = {}) => ({ ...securityHeaders, ...extra });

function replyJson(response, status, body) {
  response.writeHead(status, headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }));
  response.end(JSON.stringify(body));
}

async function jsonBody(request) {
  if (!String(request.headers['content-type'] || '').startsWith('application/json')) throw new Error('JSON content type required.');
  let body = '';
  for await (const chunk of request) {
    body += chunk;
    if (body.length > 2048) throw new Error('Request too large.');
  }
  return JSON.parse(body || '{}');
}

function sameOrigin(request) {
  const origin = request.headers.origin;
  if (!origin) return true;
  try {
    const parsed = new URL(origin);
    return parsed.host === request.headers.host && ['http:', 'https:'].includes(parsed.protocol);
  } catch { return false; }
}

const server = createServer(async (request, response) => {
  const route = (request.url || '/').split('?')[0];
  if (route === '/api/brain/status' && request.method === 'GET') {
    replyJson(response, 200, await brainStatus());
    return;
  }
  if (route === '/api/brain/candidates' && request.method === 'POST') {
    if (!sameOrigin(request)) { replyJson(response, 403, { error: 'Cross-origin writes are not allowed.' }); return; }
    try {
      replyJson(response, 201, await stageTrend(await jsonBody(request)));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to stage candidate.';
      replyJson(response, message.includes('configured') || message.includes('disabled') ? 409 : 400, { error: message });
    }
    return;
  }
  if (!['GET', 'HEAD'].includes(request.method || '')) { response.writeHead(405, headers()); response.end('Method not allowed'); return; }
  const urlPath = decodeURIComponent(route);
  const safePath = normalize(urlPath).replace(/^(\.\.(\/|\\|$))+/, '');
  let filePath = resolve(root, `.${safePath}`);
  if (!filePath.startsWith(root)) { response.writeHead(403, headers()); response.end('Forbidden'); return; }
  try {
    if (urlPath === '/' || !(await access(filePath).then(() => true).catch(() => false))) filePath = join(root, 'index.html');
    response.writeHead(200, headers({ 'content-type': types[extname(filePath)] || 'application/octet-stream', 'cache-control': extname(filePath) === '.html' || extname(filePath) === '.json' ? 'no-store' : 'public, max-age=31536000, immutable' }));
    if (request.method === 'HEAD') response.end(); else createReadStream(filePath).pipe(response);
  } catch { response.writeHead(404, headers()); response.end('Not found'); }
});

server.listen(port, host, () => console.log(`AI Radar is running on http://${host}:${port}`));
