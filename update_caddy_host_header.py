import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

caddyfile_content = """:8080 {
    reverse_proxy 127.0.0.1:8787
}
"""

sftp = ssh.open_sftp()
with sftp.file('/etc/caddy/Caddyfile', 'w') as f:
    f.write(caddyfile_content.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = ssh.exec_command('systemctl reload caddy', timeout=10)
print(stdout.read().decode('utf-8', errors='ignore'))
print('✅ Caddyfile 已还原为标准 reverse_proxy 127.0.0.1:8787')

ssh.close()
