import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

sftp = ssh.open_sftp()
with sftp.file('/root/cloudflare-os/run-dev-server.js', 'r') as f:
    content = f.read().decode('utf-8')

# 在 catch (err) { ... } 后强制将 wranglerPort 设为 8787
target = "process.exit(1);\n}"
replacement = "process.exit(1);\n}\nwranglerPort = 8787;"

if target in content and "wranglerPort = 8787;" not in content:
    content = content.replace(target, replacement, 1)
    with sftp.file('/root/cloudflare-os/run-dev-server.js', 'w') as f:
        f.write(content.encode('utf-8'))
    print("✅ 成功修改 run-dev-server.js: 强制 wranglerPort = 8787")
else:
    print("已包含 wranglerPort = 8787")

sftp.close()

def run(label, cmd):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(stdout.read().decode('utf-8', errors='ignore'))

# 重启 PM2
run('重启 PM2 cloudflare-os', 'pm2 restart cloudflare-os')

ssh.close()
