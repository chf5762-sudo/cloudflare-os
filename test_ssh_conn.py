import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

host = '192.168.10.3'
password = '@Cyn5762579'

for user in ['root', 'ubuntu']:
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=22, username=user, password=password, timeout=5)
        stdin, stdout, stderr = ssh.exec_command('id && uname -a')
        print(f"SUCCESS for [{user}]: {stdout.read().decode().strip()}")
        ssh.close()
        break
    except Exception as e:
        print(f"FAILED for [{user}]: {e}")
