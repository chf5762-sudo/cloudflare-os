import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(label, cmd):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8', errors='ignore'))

# 1. 确保 run-dev-server.js 包含 --ip 0.0.0.0
cmd_patch = """python3 -c '
path = "/root/cloudflare-os/run-dev-server.js"
with open(path, "r") as f:
    content = f.read()
target = "args.push(\"--port\", wranglerPort);"
replacement = "args.push(\"--port\", wranglerPort);\n  args.push(\"--ip\", \"0.0.0.0\");"
if target in content and "--ip" not in content:
    with open(path, "w") as f:
        f.write(content.replace(target, replacement, 1))
    print("PATCHED --ip 0.0.0.0")
else:
    print("ALREADY HAS --ip 0.0.0.0")
'"""
run('检查/修改 --ip 0.0.0.0', cmd_patch)

# 2. 设置 ecosystem.config.cjs 环境变量为 192.168.10.3:8787
ecosystem = """module.exports = {
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
    f.write(ecosystem)
sftp.close()

run('重启 PM2 cloudflare-os', 'pm2 restart cloudflare-os')

ssh.close()
