import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

stdin, stdout, stderr = ssh.exec_command('pm2 status && curl -I http://127.0.0.1:8787')
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
