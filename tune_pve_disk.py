import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(label, cmd):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8', errors='ignore'))

run('调整保留块为 0.5%', 'tune2fs -m 0.5 /dev/mapper/pve-root')
run('调整后 df -h /', 'df -h /')

ssh.close()
