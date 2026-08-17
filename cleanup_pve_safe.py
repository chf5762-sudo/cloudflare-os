import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=10)

def run(ssh, label, cmd):
    print(f'\n[{label}]')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:300])

# 清理 apt 缓存 (~88MB)
run(ssh, 'apt clean', 'apt-get clean')
run(ssh, 'apt autoremove', 'apt-get autoremove -y 2>&1 | tail -5')

# 清理 journal 日志 (只保留最近3天)
run(ssh, 'journal vacuum', 'journalctl --vacuum-time=3d')

# 清理 PVE 任务历史日志
run(ssh, 'pve task log', 'find /var/log/pve -name "*.log" -mtime +7 -delete && echo cleaned')

# 清理 vzdump 日志文件（不是备份，只是 .log 文件）
run(ssh, 'vzdump logs', 'find /var/lib/vz/dump -name "*.log" -delete && echo logs_cleaned')

# 查看清理后剩余空间
run(ssh, '清理后磁盘空间', 'df -h /')

ssh.close()
print('\n=== 清理完成 ===')
