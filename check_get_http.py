import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8787 | head -n 20')
res = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"GET Response:\n{res}")

stdin, stdout, stderr = ssh.exec_command('ss -tulpn | grep 8787')
print(f"Listening Ports:\n{stdout.read().decode('utf-8', errors='ignore').strip()}")

ssh.close()
