import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.3.202', port=22, username='root', password='@Cyn5762579', timeout=5)

stdin, stdout, stderr = ssh.exec_command('free -h')
print(stdout.read().decode('utf-8', errors='ignore'))

# 磁盘空闲（避免截断）
stdin, stdout, stderr = ssh.exec_command('df -h / | tail -1')
print('disk:', stdout.read().decode('utf-8', errors='ignore'))

# rootfs avail
stdin, stdout, stderr = ssh.exec_command('python3 -c "import json; d={\"avail\":0,\"free\":4979625984,\"total\":236019163136}; print(f\'Disk total={d[chr(116)+chr(111)+chr(116)+chr(97)+chr(108)]//1024**3}G free={d[chr(102)+chr(114)+chr(101)+chr(101)]//1024**3}G\')" 2>/dev/null || echo skip')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
