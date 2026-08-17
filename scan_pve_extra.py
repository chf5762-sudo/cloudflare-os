import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=5)

def run(label, cmd):
    print(f'\n=== {label} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    print(stdout.read().decode('utf-8', errors='ignore'))

run('Log files in /var/log', 'du -sh /var/log/* 2>/dev/null | sort -h | tail -10')
run('Dump / Backup files', 'ls -lh /var/lib/vz/dump/ 2>/dev/null || echo no_dumps')
run('ISO / Templates', 'ls -lh /var/lib/vz/template/iso/ 2>/dev/null || echo no_isos')
run('apt cache', 'du -sh /var/cache/apt 2>/dev/null')

ssh.close()
