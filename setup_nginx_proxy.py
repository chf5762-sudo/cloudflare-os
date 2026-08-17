import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(label, cmd, timeout=15):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])
    return out

# 在 Caddyfile 末尾追加 cloudflare-os 监听块（端口 8080）
# 用独立的 :8080 server block，不干扰现有 :7079 配置
append_block = """
# ==============================================================================
# Cloudflare OS 反代（端口 8080 → wrangler 127.0.0.1:8787）
# ==============================================================================
:8080 {
    reverse_proxy 127.0.0.1:8787 {
        header_up Host {upstream_hostport}
        flush_interval -1
    }
}
"""

# 检查是否已经有 8080 块
current = run('当前Caddyfile末尾', 'tail -5 /etc/caddy/Caddyfile')
if '8080' in current:
    print('\n[已有8080配置，跳过追加]')
else:
    # 追加到 Caddyfile
    run('追加cloudflare-os配置', f"cat >> /etc/caddy/Caddyfile << 'CADDYEOF'\n{append_block}\nCADDYEOF")
    run('验证Caddyfile语法', 'caddy validate --config /etc/caddy/Caddyfile')
    run('重载Caddy', 'systemctl reload caddy')
    import time
    time.sleep(2)
    run('验证8080端口 (Caddy)', 'ss -tlnp | grep 8080')
    run('测试curl', 'curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080')
    # 停用多余的 nginx
    run('停用nginx(不再需要)', 'systemctl stop nginx && systemctl disable nginx')
    print('\n✅ 已迁移到 Caddy，nginx 已停用')

ssh.close()
