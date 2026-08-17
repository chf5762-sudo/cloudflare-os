import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

def run(label, cmd, timeout=30):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])
    return out or ''

# 1. 还原 run-dev-server.js (移除 --ip 0.0.0.0)
revert_code = """python3 -c '
path = "/root/cloudflare-os/run-dev-server.js"
with open(path, "r") as f:
    content = f.read()
target = "  args.push(\\"--ip\\", \\"0.0.0.0\\");\\n"
if target in content:
    with open(path, "w") as f:
        f.write(content.replace(target, "", 1))
    print("✅ 还原 run-dev-server.js 成功")
else:
    print("无需还原")
'"""
run('还原 run-dev-server.js', revert_code)

# 2. 设置 ecosystem.config.cjs 为 192.168.10.3:8080
ecosystem = """module.exports = {
  apps: [
    {
      name: 'cloudflare-os',
      script: 'scripts/run-local.mjs',
      interpreter: 'node',
      cwd: '/root/cloudflare-os',
      env: {
        NODE_ENV: 'development',
        VITE_BACKEND_HOST: '192.168.10.3:8080'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
"""
sftp = ssh.open_sftp()
with sftp.file('/root/cloudflare-os/ecosystem.config.cjs', 'w') as f:
    f.write(ecosystem)
sftp.close()
print('✅ ecosystem.config.cjs 已设为 192.168.10.3:8080')

# 3. 检查并充实 Caddyfile
caddyfile_text = run('检查 Caddyfile', 'cat /etc/caddy/Caddyfile')
if ':8080' not in caddyfile_text:
    append_block = "\n:8080 {\n    reverse_proxy 127.0.0.1:8787 {\n        header_up Host {upstream_hostport}\n        flush_interval -1\n    }\n}\n"
    run('添加 :8080 到 Caddyfile', f"cat >> /etc/caddy/Caddyfile << 'EOF'\n{append_block}\nEOF")

run('重启 Caddy', 'systemctl restart caddy')
time.sleep(1)
run('验证 Caddy 8080 端口', 'ss -tlnp | grep 8080')

# 4. 重启 PM2 cloudflare-os
run('重启 cloudflare-os', 'pm2 restart cloudflare-os')

ssh.close()
print('\n🎉 已配置 Caddy (:8080) -> Wrangler (127.0.0.1:8787)')
