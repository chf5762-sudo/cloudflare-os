import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

sftp = ssh.open_sftp()
server_code = """import http from 'node:http';

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    let data;
    try {
      data = JSON.parse(body || '{}');
    } catch {
      data = {};
    }

    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Mcp-Session-Id', 'test-session-12345');

    const id = data.id !== undefined ? data.id : null;
    const method = data.method;

    if (method === 'initialize') {
      res.writeHead(200);
      res.end(JSON.stringify({
        jsonrpc: '2.0',
        id: id,
        result: {
          protocolVersion: '2025-06-18',
          capabilities: { tools: {} },
          serverInfo: { name: 'Local Test MCP', version: '1.0.0' }
        }
      }));
    } else if (method === 'notifications/initialized') {
      res.writeHead(200);
      res.end(JSON.stringify({ jsonrpc: '2.0' }));
    } else if (method === 'tools/list') {
      res.writeHead(200);
      res.end(JSON.stringify({
        jsonrpc: '2.0',
        id: id,
        result: {
          tools: [
            {
              name: 'get_current_time',
              description: '获取服务器当前时间',
              inputSchema: { type: 'object', properties: {} }
            }
          ]
        }
      }));
    } else if (method === 'tools/call') {
      const toolName = data.params?.name;
      const nowStr = new Date().toISOString();
      res.writeHead(200);
      res.end(JSON.stringify({
        jsonrpc: '2.0',
        id: id,
        result: {
          content: [
            { type: 'text', text: `当前服务器时间是: ${nowStr}` }
          ]
        }
      }));
    } else {
      res.writeHead(200);
      res.end(JSON.stringify({ jsonrpc: '2.0', id: id, result: {} }));
    }
  });
});

server.listen(3001, '0.0.0.0', () => {
  console.log('✅ MCP Test Server listening on http://0.0.0.0:3001/mcp');
});
"""

with sftp.file('/root/mcp-server.mjs', 'w') as f:
    f.write(server_code.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = ssh.exec_command('pm2 start /root/mcp-server.mjs --name mcp-test-server', timeout=10)
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
