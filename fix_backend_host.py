import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

def run(label, cmd, timeout=60):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])
    return out

# 1. 删除 stamp 文件，强制下次启动重新构建
run('找stamp文件', 'find /root/cloudflare-os -name "*.stamp" -o -name ".build-stamp" 2>/dev/null | head -5')
run('删除dist缓存', 'rm -rf /root/cloudflare-os/packages/workshop-frontend/dist 2>/dev/null; echo done')
run('删stamp文件', 'find /root/cloudflare-os -name "*.stamp" -delete 2>/dev/null; echo done')

# 2. 用 delete + start 完全重载（应用新 env var）
run('pm2 delete', 'pm2 delete cloudflare-os')
run('pm2 start 新配置', 'cd /root/cloudflare-os && pm2 start ecosystem.config.cjs')

print('\n⏳ 前端正在重新构建，需要约1-2分钟...')
print('构建完成后访问: http://192.168.10.3:8080')

ssh.close()
