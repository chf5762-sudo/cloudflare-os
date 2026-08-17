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

# 1. 物理修改 /root/cloudflare-os/run-dev-server.js 加上 --ip 0.0.0.0
cmd_patch = """python3 -c '
with open("/root/cloudflare-os/run-dev-server.js", "r") as f:
    content = f.read()
target = "args.push(\\"--port\\", wranglerPort);"
replacement = "args.push(\\"--port\\", wranglerPort);\\n  args.push(\\"--ip\\", \\"0.0.0.0\\");"
if target in content and "--ip" not in content:
    new_content = content.replace(target, replacement, 1)
    with open("/root/cloudflare-os/run-dev-server.js", "w") as f:
        f.write(new_content)
    print("PATCHED run-dev-server.js successfully")
else:
    print("ALREADY PATCHED OR TARGET NOT FOUND")
'"""
run('修改 run-dev-server.js 支持 --ip 0.0.0.0', cmd_patch)

# 2. 更新 ecosystem.config.cjs 指向 192.168.10.3:8787
new_ecosystem = """module.exports = {
  apps: [
    {
      name: 'cloudflare-os',
      script: 'scripts/run-local.mjs',
      interpreter: 'node',
      cwd: '/root/cloudflare-os',
      env: {
        NODE_ENV: 'development',
        VITE_BACKEND_HOST: '192.168.10.3:8787'
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
    f.write(new_ecosystem)
sftp.close()
print('✅ ecosystem.config.cjs 更新完成')

# 3. 清理前端构建缓存并用 PM2 重新启动
run('清理 dist 与 stamp 缓存', 'rm -rf /root/cloudflare-os/packages/workshop-frontend/dist && find /root/cloudflare-os -name "*.stamp" -delete && echo done')
run('删除旧 PM2 任务', 'pm2 delete cloudflare-os || true')
run('重新启动 PM2 任务', 'cd /root/cloudflare-os && pm2 start ecosystem.config.cjs')

ssh.close()
print('\n🎉 已重载，等待前端重新构建与 workerd 在 0.0.0.0:8787 监听...')
