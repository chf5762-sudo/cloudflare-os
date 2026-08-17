import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.10.3', port=22, username='root', password='@Cyn5762579', timeout=10)

def run(label, cmd, timeout=60):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])

# 修改 ai-models.ts 支持第三方 OpenAI 兼容 API (/v1/chat/completions)
patch_code = """python3 -c '
path = "/root/cloudflare-os/packages/workshop-backend/src/ai-models.ts"
with open(path, "r") as f:
    content = f.read()

target = "api: \\"openai-responses\\","
replacement = "api: (config.apiUrl && !config.apiUrl.includes(\\"api.openai.com\\")) ? \\"openai-completions\\" : \\"openai-responses\\","

if target in content:
    with open(path, "w") as f:
        f.write(content.replace(target, replacement, 1))
    print("✅ PATCHED ai-models.ts for custom OpenAI compatible endpoints!")
else:
    print("ALREADY PATCHED OR TARGET NOT FOUND")
'"""

run('修改 ai-models.ts 支持 OpenAI 兼容 API', patch_code)

# 删除构建缓存
run('清理 validate 缓存', 'rm -rf /root/cloudflare-os/packages/workshop-backend/.wrangler/validate && echo done')

# 重启 PM2 触发展发
run('重启 cloudflare-os', 'pm2 restart cloudflare-os')

ssh.close()
print('\n🎉 已修复并重启 PM2 服务！')
