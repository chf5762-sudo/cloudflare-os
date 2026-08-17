import paramiko, sys
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

# 修改 run-dev-server.js 添加 --show-interactive-dev-session=false
patch_code = """python3 -c '
path = "/root/cloudflare-os/run-dev-server.js"
with open(path, "r") as f:
    content = f.read()

target = "const args = configs.flatMap(c => [\\"-c\\", c]);"
replacement = "const args = configs.flatMap(c => [\\"-c\\", c]);\\n  args.push(\\"--show-interactive-dev-session=false\\");"

if target in content and "--show-interactive-dev-session=false" not in content:
    with open(path, "w") as f:
        f.write(content.replace(target, replacement, 1))
    print("✅ 成功添加 --show-interactive-dev-session=false 非交互模式")
else:
    print("无需重复修改")
'"""

run('修改 run-dev-server.js 禁用交互模式', patch_code)

# 重启 PM2 cloudflare-os
run('重启 cloudflare-os', 'pm2 restart cloudflare-os')

ssh.close()
