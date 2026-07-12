import { createReadStream } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('./dist', import.meta.url)));
const port = Number.parseInt(process.env.PORT || '4173', 10);
const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error('PORT must be an integer between 1 and 65535');
}
await access(join(root, 'index.html'));

const server = createServer(async (request, response) => {
  if (!['GET', 'HEAD'].includes(request.method)) {
    response.writeHead(405, { Allow: 'GET, HEAD' });
    response.end();
    return;
  }

  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    const relative = normalize(pathname).replace(/^[/\\]+/, '');
    let filePath = resolve(root, relative);
    if (filePath !== root && !filePath.startsWith(`${root}\\`) && !filePath.startsWith(`${root}/`)) {
      response.writeHead(400);
      response.end('Bad request');
      return;
    }

    let fileStats = await stat(filePath).catch(() => null);
    if (fileStats?.isDirectory()) {
      filePath = join(filePath, 'index.html');
      fileStats = await stat(filePath).catch(() => null);
    }
    if (!fileStats?.isFile()) {
      filePath = join(root, 'index.html');
      fileStats = await stat(filePath);
    }

    const extension = extname(filePath).toLowerCase();
    const immutable = filePath.includes(`${join(root, 'assets')}\\`) || filePath.includes(`${join(root, 'assets')}/`);
    response.writeHead(200, {
      'Content-Type': contentTypes[extension] || 'application/octet-stream',
      'Content-Length': fileStats.size,
      'Cache-Control': immutable ? 'public, max-age=31536000, immutable' : 'no-cache',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    });
    if (request.method === 'HEAD') {
      response.end();
      return;
    }
    createReadStream(filePath).pipe(response);
  } catch {
    response.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    response.end('Unable to serve application');
  }
});

server.listen(port, '0.0.0.0');
