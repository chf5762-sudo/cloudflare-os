import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=10)

cmds = [
    ('根目录各子目录', 'du -sh /* 2>/dev/null | sort -rh | head -20'),
    ('apt缓存', 'du -sh /var/cache/apt/'),
    ('docker', 'docker system df 2>/dev/null || echo no_docker'),
    ('npm/pip缓存', 'du -sh ~/.npm 2>/dev/null; du -sh ~/.cache 2>/dev/null; du -sh /root/.npm 2>/dev/null; du -sh /root/.cache 2>/dev/null'),
    ('大文件(>100M,排除VM镜像)', 'find / -xdev -size +100M -not -path "/var/lib/vz/*" -not -path "/proc/*" 2>/dev/null | xargs ls -lh 2>/dev/null'),
    ('old kernels', 'dpkg --list | grep linux-image | awk "{print $1,$2,$3}"'),
]
for label, c in cmds:
    print(f'\n=== {label} ===')
    print(f'CMD: {c}')
    stdin, stdout, stderr = ssh.exec_command(c, timeout=20)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(out or '(empty)')
    if err.strip():
        print('STDERR:', err[:200])

ssh.close()
print('\n=== DONE ===')
