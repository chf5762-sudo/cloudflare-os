import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

for i in range(12):
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8787')
    code = stdout.read().decode('utf-8', errors='ignore').strip()
    if code in ['200', '302', '301', '404']:
        print(f"🎉 8787 端口就绪！HTTP Code: {code}")
        break
    else:
        print(f"⏳ Gatekeepers 正在完成最终打包 ({i+1}/12)...")
        time.sleep(5)

ssh.close()
