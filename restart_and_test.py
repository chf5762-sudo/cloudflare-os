import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(label, cmd, timeout=15):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])

run('重启 PM2', 'pm2 restart cloudflare-os')
time.sleep(3)
run('8787 端口', 'ss -tlnp | grep 8787')
run('curl 测试', 'curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8787/ || echo FAIL')

ssh.close()
