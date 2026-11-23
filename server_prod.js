const http = require('http');
const fs = require('fs');
const path = require('path');

const distDir = path.join(__dirname, 'farmai', 'frontend', 'dist');

const server = http.createServer((req, res) => {
  let reqPath = req.url.split('?')[0];
  if (reqPath === '/') reqPath = '/index.html';
  
  // Proxy /api to FastAPI backend on 8000
  if (reqPath.startsWith('/api') || reqPath.startsWith('/health')) {
    const proxyReq = http.request({
      hostname: '127.0.0.1',
      port: 8000,
      path: req.url,
      method: req.method,
      headers: req.headers
    }, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (err) => {
      res.writeHead(502);
      res.end('Backend proxy error: ' + err.message);
    });
    req.pipe(proxyReq);
    return;
  }

  const filePath = path.join(distDir, reqPath);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const mime = ext === '.html' ? 'text/html' : 
                 ext === '.js' ? 'application/javascript' : 
                 ext === '.css' ? 'text/css' : 
                 ext === '.png' ? 'image/png' : 
                 ext === '.svg' ? 'image/svg+xml' : 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': mime, 'Access-Control-Allow-Origin': '*' });
    fs.createReadStream(filePath).pipe(res);
  } else {
    // SPA Fallback to index.html
    const indexPath = path.join(distDir, 'index.html');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    fs.createReadStream(indexPath).pipe(res);
  }
});

server.listen(5173, '127.0.0.1', () => {
  console.log('KrishiNetra Production SPA Server running on http://127.0.0.1:5173');
});
