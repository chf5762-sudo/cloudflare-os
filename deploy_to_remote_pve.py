import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

HOST = '192.168.10.3'
USER = 'root'
PASSWORD = '@Cyn5762579'
REMOTE_DIR = '/root/cloudflare-os'

def run_remote(ssh, cmd, ignore_error=False):
    print(f"\n[REMOTE RUN]: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    
    output = ""
    while True:
        line = stdout.readline()
        if not line:
            break
        output += line
        print(line.rstrip())
        
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0 and not ignore_error:
        print(f"❌ Error (status {exit_status})")
    return output, exit_status

def main():
    print(f"🚀 开始部署 cloudflare-os 到远程 192.168.10.3 ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, port=22, username=USER, password=PASSWORD, timeout=10)
        print("✅ SSH 连接成功")
        
        # 1. 检查 Node.js / pnpm / pm2
        run_remote(ssh, "node -v || (curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs)")
        run_remote(ssh, "command -v pnpm || npm install -g pnpm")
        run_remote(ssh, "command -v pm2 || npm install -g pm2")

        # 2. 克隆或更新代码
        run_remote(ssh, f"if [ -d '{REMOTE_DIR}' ]; then cd {REMOTE_DIR} && git pull; else git clone https://github.com/cloudflare/cloudflare-os.git {REMOTE_DIR}; fi")

        # 3. 安装依赖与构建
        run_remote(ssh, f"cd {REMOTE_DIR} && pnpm install")
        run_remote(ssh, f"cd {REMOTE_DIR} && pnpm --filter @gadgets/typed-storage build")
        run_remote(ssh, f"cd {REMOTE_DIR} && pnpm --filter @gadgets/workshop-frontend exec vite build")

        # 4. 生成 PM2 配置文件
        pm2_config = """module.exports = {
  apps: [
    {
      name: 'cloudflare-os',
      script: 'scripts/run-local.mjs',
      interpreter: 'node',
      cwd: '/root/cloudflare-os',
      env: {
        NODE_ENV: 'development',
        VITE_BACKEND_HOST: '0.0.0.0:8787'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
"""
        sftp = ssh.open_sftp()
        with sftp.file(f"{REMOTE_DIR}/ecosystem.config.cjs", "w") as f:
            f.write(pm2_config)
        sftp.close()
        print("✅ 远程 ecosystem.config.cjs 生成成功")

        # 5. 使用 PM2 启动服务
        run_remote(ssh, f"cd {REMOTE_DIR} && pm2 delete cloudflare-os || true", ignore_error=True)
        run_remote(ssh, f"cd {REMOTE_DIR} && pm2 start ecosystem.config.cjs")
        run_remote(ssh, "pm2 save")

        # 6. 健康检测
        time.sleep(3)
        stdout, status = run_remote(ssh, "curl -s -I http://127.0.0.1:8787 || echo 'FAIL'")
        print("\n==================================================")
        print("🎉 远程 192.168.10.3 部署并启动完成！")
        print("🌐 访问地址: http://192.168.10.3:8787")
        print("==================================================")

    except Exception as e:
        print(f"❌ 部署失败: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
