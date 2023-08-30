import paramiko
import re

# Remote host details
hostname = '192.168.135.11'
port = 22
username = 'abacus'
password = 'abacus'  # or use key-based authentication

# Command to run
command = 'sudo docker ps'

# Create an SSH client
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Connect to the remote host
    client.connect(hostname, port, username, password)

    # Execute the command
    stdin, stdout, stderr = client.exec_command(command)


    container_names = []
    output_lines = stdout.read().decode().split('\n')
    for line in output_lines[1:]:
        parts = re.split(r'\s+', line.strip())
        if len(parts) > 7:
            container_names.append(parts[-1])

    # Print the extracted container names
    print("Container Names:")
    for name in container_names:
        print(name)

    # Print the output
    # print("Command output:")
    # print(stdout.read().decode())

    # Close the SSH connection
    client.close()

except paramiko.AuthenticationException:
    print("Authentication failed, please verify your credentials.")
except paramiko.SSHException as e:
    print("SSH connection error:", str(e))
except Exception as e:
    print("An error occurred:", str(e))
