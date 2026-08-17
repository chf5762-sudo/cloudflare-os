import paramiko, sys, time
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=10)

def run(ssh, label, cmd, timeout=60):
    print(f'\n[{label}]')
    print(f'CMD: {cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(ok)')
    if err.strip():
        print('ERR:', err[:300])
    return out, err

print('=== 删除旧快照，释放磁盘空间 ===\n')

# 1. 先删 VM 100 最旧快照 tailscale-chrom20260717（它是 ubntu0815 的父节点，先合并）
run(ssh, '删 VM100 旧快照 tailscale-chrom20260717', 'qm delsnapshot 100 tailscale-chrom20260717', timeout=120)

# 2. 再删 VM 100 快照 ubntu0815 → 释放 vm-100-state-ubntu0815.raw (4.17G)
run(ssh, '删 VM100 快照 ubntu0815 (释放4.17G)', 'qm delsnapshot 100 ubntu0815', timeout=120)

# 3. 删 VM 102 旧快照 ok → 释放 vm-102-state-ok.raw (467MB)
run(ssh, '删 VM102 快照 ok (释放467MB)', 'qm delsnapshot 102 ok', timeout=60)

# 4. 验证结果
run(ssh, '剩余快照 VM100', 'pvesh get /nodes/n150/qemu/100/snapshot')
run(ssh, '剩余快照 VM102', 'pvesh get /nodes/n150/qemu/102/snapshot')
run(ssh, '清理后磁盘空间', 'df -h /')
run(ssh, 'local存储文件', 'ls -lh /var/lib/vz/images/100/ && ls -lh /var/lib/vz/images/102/')

ssh.close()
print('\n=== 完成 ===')
