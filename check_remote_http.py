import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

for i in range(5):
    stdin, stdout, stderr = ssh.exec_command('curl -s -I http://127.0.0.1:8787 | head -n 5')
    res = stdout.read().decode('utf-8', errors='ignore').strip()
    if res:
        print(f"✅ Attempt {i+1} Response:\n{res}")
        break
    print(f"⏳ Waiting for server to finish initializing... ({i+1}/5)")
    time.sleep(2)

ssh.close()
