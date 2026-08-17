import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

caddyfile = """# Caddy Gateway for Cloudflare OS
:8080 {
    reverse_proxy 127.0.0.1:8787
}
"""

sftp = ssh.open_sftp()
with sftp.file('/etc/caddy/Caddyfile', 'w') as f:
    f.write(caddyfile)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('systemctl reload caddy; ss -tlnp | grep 8080')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
print('✅ Caddyfile 简化成功，支持原生 WebSocket 反代！')
