import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(ssh, label, cmd, timeout=30):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(empty)')
    return out

# VM100 MAC: BC:24:11:7F:6F:40
# 从 PVE（192.168.10.254）扫描 vmbr1 子网，找到 VM100
run(ssh, 'ping 广播激活 ARP', 'ping -c 2 -b 192.168.10.255 -I vmbr1 2>/dev/null; sleep 1', timeout=10)
run(ssh, 'ARP vmbr1 接口', 'ip neigh show dev vmbr1')
run(ssh, '通过MAC查IP (VM100: BC:24:11:7F:6F:40)', 'ip neigh show | grep -i "bc:24:11:7f:6f:40"')

# 如果上面没找到，用 nmap 扫
run(ssh, 'nmap 扫描 192.168.10.0/24', 'nmap -sn 192.168.10.0/24 --exclude 192.168.10.254 2>/dev/null | grep -E "report|MAC"', timeout=30)

# 再次查 ARP
run(ssh, '扫描后 ARP', 'ip neigh show dev vmbr1')

ssh.close()
