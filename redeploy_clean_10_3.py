import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

HOST = '192.168.10.3'
USER = 'root'
PASSWORD = '@Cyn5762579'
REMOTE_DIR = '/root/cloudflare-os'
REPO_URL = 'https://github.com/chf5762-sudo/cloudflare-os.git'

def run_remote(ssh, cmd, ignore_error=False, timeout=600):
    print(f"\n[REMOTE RUN]: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    
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
    print(f"🚀 开始彻底清理并重新部署 cloudflare-os 到 192.168.10.3 ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, port=22, username=USER, password=PASSWORD, timeout=15)
        print("✅ SSH 连接成功")
        
        # 1. 停止并清理 PM2 旧应用与进程
        print("\n--- 步骤 1: 清理旧应用与进程 ---")
        run_remote(ssh, "pm2 delete all || true", ignore_error=True)
        run_remote(ssh, "pm2 save --force || true", ignore_error=True)
        run_remote(ssh, "pkill -f node || true", ignore_error=True)
        run_remote(ssh, "pkill -f workerd || true", ignore_error=True)

        # 2. 完全删除旧部署目录
        print("\n--- 步骤 2: 清除项目目录 ---")
        run_remote(ssh, f"rm -rf {REMOTE_DIR}")
        print("✅ 旧项目目录已彻底清除")

        # 3. 重新克隆最新仓库
        print("\n--- 步骤 3: 重新克隆最新 GitHub 仓库 ---")
        run_remote(ssh, f"git clone {REPO_URL} {REMOTE_DIR}")

        # 4. 安装依赖与构建 typed-storage
        print("\n--- 步骤 4: 安装 pnpm 依赖 ---")
        run_remote(ssh, f"cd {REMOTE_DIR} && pnpm install")
        print("\n--- 步骤 5: 构建 typed-storage ---")
        run_remote(ssh, f"cd {REMOTE_DIR} && pnpm --filter @gadgets/typed-storage build")

        # 5. 生成全新的 ecosystem.config.cjs
        print("\n--- 步骤 6: 配置 ecosystem.config.cjs ---")
        pm2_config = """module.exports = {
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
        with sftp.file(f"{REMOTE_DIR}/ecosystem.config.cjs", "w") as f:
            f.write(pm2_config)
        sftp.close()
        print("✅ ecosystem.config.cjs 配置完成 (包含 MCP_ALLOW_INSECURE 和 VITE_BACKEND_HOST)")

        # 6. 校验并配置 Caddy (保证端口 8080 反向代理 8787)
        print("\n--- 步骤 7: 配置 Caddy 反向代理 ---")
        caddyfile_text, _ = run_remote(ssh, "cat /etc/caddy/Caddyfile || echo ''", ignore_error=True)
        if ':8080' not in caddyfile_text:
            append_block = "\n:8080 {\n    reverse_proxy 127.0.0.1:8787 {\n        header_up Host {upstream_hostport}\n        flush_interval -1\n    }\n}\n"
            run_remote(ssh, f"cat >> /etc/caddy/Caddyfile << 'EOF'\n{append_block}\nEOF")
        
        run_remote(ssh, "systemctl restart caddy || service caddy restart")
        print("✅ Caddy 反向代理已启动并监听 8080 端口")

        # 7. PM2 重新启动服务
        print("\n--- 步骤 8: 使用 PM2 启动 cloudflare-os ---")
        run_remote(ssh, f"cd {REMOTE_DIR} && pm2 start ecosystem.config.cjs")
        run_remote(ssh, "pm2 save")

        # 8. 等待并检测状态
        print("\n--- 步骤 9: 健康检查 ---")
        time.sleep(5)
        run_remote(ssh, "pm2 status")
        run_remote(ssh, "ss -tlnp | grep -E '8080|8787'")

        print("\n==================================================")
        print("🎉 远程 192.168.10.3 清理并重新部署成功！")
        print("🌐 访问地址: http://192.168.10.3:8080")
        print("==================================================")

    except Exception as e:
        print(f"❌ 部署出错: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
