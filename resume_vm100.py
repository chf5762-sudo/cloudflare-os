import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=10)

def run(ssh, label, cmd, timeout=30):
    print(f'\n[{label}]')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:200])
    return out

# 检查实际磁盘占用（du 才是真实的）
run(ssh, '实际占用 du', 'du -sh /var/lib/vz/images/* 2>/dev/null')
run(ssh, '文件系统（含reserved）', 'df -h / && tune2fs -l /dev/mapper/pve-root 2>/dev/null | grep -E "Block (count|size|Free)"')

# 检查 VM100 当前状态
run(ssh, 'VM100 状态', 'pvesh get /nodes/n150/qemu/100/status/current | grep -E "qmpstatus|status|mem|pid"')

# 尝试 resume VM100（io-error 状态可以通过 resume 恢复）
print('\n=== 尝试 resume VM 100 ===')
run(ssh, 'resume VM100', 'qm resume 100 2>&1', timeout=15)

time.sleep(3)
run(ssh, 'VM100 resume 后状态', 'pvesh get /nodes/n150/qemu/100/status/current | grep -E "qmpstatus|status"')

ssh.close()
