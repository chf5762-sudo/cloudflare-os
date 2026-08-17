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

# 写入纯净的补丁脚本并上传
remote_patch_code = """
path = "/root/cloudflare-os/run-dev-server.js"
with open(path, "r") as f:
    content = f.read()

target = "process.exit(1);"
replacement = "process.exit(1);\\nwranglerPort = 8787;"
if "wranglerPort = 8787;" not in content and target in content:
    content = content.replace(target, replacement, 1)
    with open(path, "w") as f:
        f.write(content)
    print("✅ 固定 wranglerPort = 8787 成功")
else:
    print("已存在或处理完毕")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/fix_port.py", "w") as f:
    f.write(remote_patch_code)
sftp.close()

run("修改 run-dev-server.js 固定端口 8787", "python3 /tmp/fix_port.py")
run("重启 PM2 部署应用", "cd /root/cloudflare-os && pm2 restart cloudflare-os")

print("\n⏳ 等待后端端口 8787 启动...")
time.sleep(8)

run("检查 8787 与 8080 监听端口", "ss -tlnp")
ssh.close()
