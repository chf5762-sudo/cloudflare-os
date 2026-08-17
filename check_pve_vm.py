import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
pve = paramiko.SSHClient()
pve.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pve.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(label, cmd):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = pve.exec_command(cmd, timeout=5)
    print(stdout.read().decode('utf-8', errors='ignore'))

run('Disk space', 'df -h /')
run('VM 100 status', 'pvesh get /nodes/n150/qemu/100/status/current | grep -E "qmpstatus|status"')

pve.close()
