import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

ecosystem = """module.exports = {
  apps: [
    {
      name: 'cloudflare-os',
      script: 'scripts/run-local.mjs',
      interpreter: 'node',
      cwd: '/root/cloudflare-os',
      env: {
        NODE_ENV: 'development',
        VITE_BACKEND_HOST: '192.168.10.3:8080',
        MCP_ALLOW_INSECURE: 'true'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
"""

sftp = ssh.open_sftp()
with sftp.file('/root/cloudflare-os/ecosystem.config.cjs', 'w') as f:
    f.write(ecosystem)
sftp.close()
print('✅ ecosystem.config.cjs 已更新 MCP_ALLOW_INSECURE=true')

stdin, stdout, stderr = ssh.exec_command('pm2 restart cloudflare-os', timeout=10)
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
