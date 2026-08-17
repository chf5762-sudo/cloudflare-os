import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

HOST = '192.168.10.3'
USER = 'root'
PASSWORD = '@Cyn5762579'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=22, username=USER, password=PASSWORD, timeout=15)

def run(label, cmd):
    print(f"\n=== {label} ===")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])

# 上传完整补丁到远程
patch_code = """
path = "/root/cloudflare-os/run-dev-server.js"
with open(path, "r") as f:
    content = f.read()

# 1. 注入 --ip 0.0.0.0
target1 = 'args.push("--port", wranglerPort);'
replacement1 = 'args.push("--port", wranglerPort);\\n  args.push("--ip", "0.0.0.0");'
if target1 in content and "--ip" not in content:
    content = content.replace(target1, replacement1, 1)

# 2. 注入非交互模式
target2 = 'const args = configs.flatMap(c => ["-c", c]);'
replacement2 = 'const args = configs.flatMap(c => ["-c", c]);\\n  args.push("--show-interactive-dev-session=false");'
if target2 in content and "--show-interactive-dev-session=false" not in content:
    content = content.replace(target2, replacement2, 1)

# 3. 固定底层端口 8787
target3 = 'process.exit(1);\\n}'
replacement3 = 'process.exit(1);\\n}\\nwranglerPort = 8787;'
if target3 in content and "wranglerPort = 8787;" not in content:
    content = content.replace(target3, replacement3, 1)

with open(path, "w") as f:
    f.write(content)
print("✅ run-dev-server.js 3 处核心补丁修补完成")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/full_patch.py", "w") as f:
    f.write(patch_code)
sftp.close()

run("修补 run-dev-server.js 核心逻辑", "python3 /tmp/full_patch.py")
run("重启 PM2 cloudflare-os", "cd /root/cloudflare-os && pm2 restart cloudflare-os")

print("\n⏳ 等待前端 Vite 构建与 Workerd 启动...")
time.sleep(12)

run("检测 8787 和 8080 端口状态", "ss -tlnp")
ssh.close()
