# Cloudflare OS Ubuntu (192.168.10.3) 一键极速部署、源码修复与 MCP 避坑指南

本指南详细记录了在 Ubuntu 虚拟机（如 `192.168.10.3`）中部署 `cloudflare-os` 的完整指令、3 处关键源码/配置修复（OpenAI 兼容性、WebSocket 端口匹配、MCP HTTP 限制解除）以及 Caddy 反向代理守护方案。

---

## ⚡ 1. 环境准备 (Prerequisites)

在 Ubuntu VM 终端执行，安装 Node.js 20+、pnpm 和 PM2：

```bash
# 1.1 安装 Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 1.2 全局安装 pnpm 与 pm2
sudo npm install -g pnpm pm2
```

---

## 📥 2. 克隆代码与依赖安装 (Clone & Install)

```bash
# 2.1 进入主目录并克隆项目
cd ~
git clone https://github.com/cloudflare/cloudflare-os.git
cd cloudflare-os

# 2.2 安装依赖
pnpm install

# 2.3 预编译核心模块 (避免首次启动卡顿)
pnpm --filter @gadgets/typed-storage build
pnpm --filter @gadgets/workshop-frontend exec vite build
```

---

## ⚙️ 3. 核心源码修复与配置 (关键步骤)

官方原版存在 3 个针对私有化/第三方代理部署的限制与 Bug，必须进行以下 3 处修正：

### 3.1 局域网与非交互适配 (`run-dev-server.js`)

**修改原因**：官方默认只监听 `127.0.0.1` 且会启动交互式控制台（后台运行时会挂起）。需注入 `--ip 0.0.0.0`、`--show-interactive-dev-session=false` 并将后端端口固定为 `8787`：

```bash
python3 -c '
path = "run-dev-server.js"
with open(path, "r") as f:
    content = f.read()

# 1. 注入 --ip 0.0.0.0
target1 = "args.push(\"--port\", wranglerPort);"
replacement1 = "args.push(\"--port\", wranglerPort);\n  args.push(\"--ip\", \"0.0.0.0\");"
if target1 in content and "--ip" not in content:
    content = content.replace(target1, replacement1, 1)

# 2. 注入非交互模式
target2 = "const args = configs.flatMap(c => [\"-c\", c]);"
replacement2 = "const args = configs.flatMap(c => [\"-c\", c]);\n  args.push(\"--show-interactive-dev-session=false\");"
if target2 in content and "--show-interactive-dev-session=false" not in content:
    content = content.replace(target2, replacement2, 1)

# 3. 固定底层端口为 8787 (供 Caddy 代理)
target3 = "process.exit(1);\n}"
replacement3 = "process.exit(1);\n}\nwranglerPort = 8787;"
if target3 in content and "wranglerPort = 8787;" not in content:
    content = content.replace(target3, replacement3, 1)

with open(path, "w") as f:
    f.write(content)
print("✅ run-dev-server.js 适配完成")
'
```

---

### 3.2 第三方 OpenAI/OpenRouter 兼容性修复 (`packages/workshop-backend/src/ai-models.ts`)

**修改原因**：官方代码写死 `api: "openai-responses"` 请求 OpenAI 独占的 `/v1/responses` 路径。第三方网关（OpenRouter、OneAPI、DeepSeek）只支持标准的 `/v1/chat/completions`。不修改会报 `401 Unauthorized` / `404 Not Found`。

```bash
# 修改前后对比：
# 修改前：api: "openai-responses",
# 修改后：api: (config.apiUrl && !config.apiUrl.includes("api.openai.com")) ? "openai-completions" : "openai-responses",

python3 -c '
path = "packages/workshop-backend/src/ai-models.ts"
with open(path, "r") as f:
    content = f.read()

target = "api: \"openai-responses\","
replacement = "api: (config.apiUrl && !config.apiUrl.includes(\"api.openai.com\")) ? \"openai-completions\" : \"openai-responses\","

if target in content:
    with open(path, "w") as f:
        f.write(content.replace(target, replacement, 1))
    print("✅ ai-models.ts 兼容适配完成")
'
```

---

### 3.3 解除 MCP HTTP/内网连接限制与 PM2 配置 (`ecosystem.config.cjs`)

**修改原因**：Cloudflare 默认要求 MCP 必须是 HTTPS 且禁止连局域网 IP。配置 `MCP_ALLOW_INSECURE: 'true'` 即可解锁 HTTP 和内网 MCP 连接；配置 `VITE_BACKEND_HOST: '192.168.10.3:8080'` 修复前端 WebSocket 断连问题：

在根目录下创建 `ecosystem.config.cjs`：

```javascript
module.exports = {
  apps: [
    {
      name: 'cloudflare-os',
      script: 'scripts/run-local.mjs',
      interpreter: 'node',
      cwd: '/root/cloudflare-os',
      env: {
        NODE_ENV: 'development',
        VITE_BACKEND_HOST: '192.168.10.3:8080',
        MCP_ALLOW_INSECURE: 'true'  // 解除 HTTP 与局域网 IP 的 MCP 连接限制
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
```

---

### 3.4 配置 Caddy 反向代理网关 (`/etc/caddy/Caddyfile`)

Caddy 监听公网 `8080` 端口并将请求和 WebSocket 代理给内部 `8787`：

```bash
# 安装 Caddy
sudo apt-get install -y caddy

# 配置 /etc/caddy/Caddyfile
sudo bash -c 'cat << "EOF" > /etc/caddy/Caddyfile
:8080 {
    reverse_proxy 127.0.0.1:8787
}
EOF'

# 重载 Caddy
sudo systemctl reload caddy
```

---

## 🚀 4. 启动与后台守护 (Start Service)

```bash
# 4.1 使用 PM2 启动服务
pm2 start ecosystem.config.cjs

# 4.2 保存 PM2 进程表 (开机自启)
pm2 save
pm2 startup
```

---

## 🤖 5. 访问与模型配置指南

在浏览器中打开：👉 **http://192.168.10.3:8080**

### 5.1 初始管理员账号
* **Username**: `admin`
* **Password**: `admin123456`

### 5.2 添加 OpenRouter / 自定义 OpenAI 兼容模型
点击 **Add AI Model**：
1. **Select Model**：选择 `Other OpenAI...`
2. **Model ID**：填写 `aistudio/gemini-2.5-flash`
3. **Display Name**：填写 `Gemini 2.5 Flash`
4. **API Token**：填写你的 API Key（例如 `sk-SMd1Jw3...`）
5. ⚠️ **必须展开 `Advanced Settings`（高级设置）**：
   * 在 **`API URL`** 中填写：`https://open-router.beundredig.eu.org/v1`
6. 点击 **Add Model** 提交保存。

---

## 🌐 6. 创建本地测试 MCP 服务 (可选)

如需测试本地 MCP 服务，可在服务器启动一个简单的 HTTP/SSE MCP 服务器：

创建 `/root/mcp-server.mjs`：
```javascript
import http from 'node:http';

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    let data;
    try { data = JSON.parse(body || '{}'); } catch { data = {}; }
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Mcp-Session-Id', 'test-session-12345');
    const id = data.id !== undefined ? data.id : null;
    const method = data.method;

    if (method === 'initialize') {
      res.writeHead(200);
      res.end(JSON.stringify({
        jsonrpc: '2.0', id: id,
        result: { protocolVersion: '2025-06-18', capabilities: { tools: {} }, serverInfo: { name: 'Local Test MCP', version: '1.0.0' } }
      }));
    } else if (method === 'tools/list') {
      res.writeHead(200);
      res.end(JSON.stringify({
        jsonrpc: '2.0', id: id,
        result: { tools: [{ name: 'get_current_time', description: '获取服务器当前时间', inputSchema: { type: 'object', properties: {} } }] }
      }));
    } else if (method === 'tools/call') {
      res.writeHead(200);
      res.end(JSON.stringify({
        jsonrpc: '2.0', id: id,
        result: { content: [{ type: 'text', text: `当前服务器时间是: ${new Date().toISOString()}` }] }
      }));
    } else {
      res.writeHead(200);
      res.end(JSON.stringify({ jsonrpc: '2.0', id: id, result: {} }));
    }
  });
});

server.listen(3001, '0.0.0.0', () => {
  console.log('✅ MCP Test Server running on http://0.0.0.0:3001/mcp');
});
```

启动命令：
```bash
pm2 start /root/mcp-server.mjs --name mcp-test-server
```
然后在 Cloudflare OS 的 MCP 界面输入 `http://127.0.0.1:3001/mcp` 即可直接连接！

---

## 🔍 7. 常见故障根因分析与避坑总结 (Troubleshooting)

### Q1: 发送消息一直提示 `Reconnecting...`
* **根因**：前端编译的 `VITE_BACKEND_HOST` 端口与反向代理端口不匹配，导致 WebSocket 连接被拒。
* **解决**：确保 `ecosystem.config.cjs` 中 `VITE_BACKEND_HOST: '192.168.10.3:8080'` 且 `run-dev-server.js` 中 `wranglerPort = 8787`。

### Q2: 提示 `Failed to add model`
* **根因**：主键冲突。说明该 Model ID（如 `aistudio/gemini-2.5-flash`）在此之前**已经添加成功**了。
* **解决**：无需重复添加，直接在聊天界面右下角下拉菜单中选择使用。

### Q3: MCP 连接提示 `The endpoint must use https://` 或被拦截
* **根因**：Cloudflare 默认要求 HTTPS 且禁止私有 IP。
* **解决**：在 `ecosystem.config.cjs` 环境变量中加入 `MCP_ALLOW_INSECURE: 'true'` 并重启 PM2。

### Q4: 还原官方初始源码
如果需要清除所有本地修改：
```bash
cd ~/cloudflare-os
git checkout .
```
