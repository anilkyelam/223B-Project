"""
Utility script to run a custom command on all nodes (like pssh)
"""

import os
import sys
import paramiko
from datetime import datetime
import time

giraph_nodes = ["giraph1", "giraph2", "giraph3", "giraph4"]


# Creates SSH client from ssh config, using paramiko lib.
def create_ssh_client(server_name, port=22, user_config_file_path="~/.ssh/config"):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser(user_config_file_path)
    try:
        with open(user_config_file) as f:
            ssh_config.parse(f)
    except FileNotFoundError:
        print("SSH config file not found at {0}. Aborting.".format(user_config_file))
        sys.exit(1)

    cfg = {}
    user_config = ssh_config.lookup(server_name)
    cfg['hostname'] = user_config['hostname']
    cfg['username'] = user_config['user']
    cfg['port'] = 22
    cfg['key_filename'] = user_config['identityfile']
    client.connect(**cfg)
    return client


# Executes command with ssh client and reads from out and err buffers so it does not block.
def ssh_execute_command(ssh_client, command, sudo=False): 
    if sudo:
        command = "sudo " + command

    _, stdout, stderr = ssh_client.exec_command(command)
    output = str(stdout.read() + stderr.read())
    print(output)
    return output


# Utility to run a custom script on all the spark nodes
def run_script():
    for node_name in giraph_nodes:
        ssh_client = create_ssh_client(node_name)

        ssh_execute_command(ssh_client, "echo '======== {0} ('$HOSTNAME')=========='".format(node_name))
        # Setup steps
        # ssh_execute_command(ssh_client, "sudo add-apt-repository ppa:openjdk-r/ppa")
        # ssh_execute_command(ssh_client, "sudo apt-get update")
        # ssh_execute_command(ssh_client, "sudo apt-get -y install openjdk-8-jdk")
        # ssh_execute_command(ssh_client, "java -version")
        
        # ssh_execute_command(ssh_client, "cp giraph_runs/node-scripts/.profile .")
        # ssh_execute_command(ssh_client, "source .profile")
        
        # ssh_execute_command(ssh_client, "tar -xvf hadoop-ver.tar")
        # ssh_execute_command(ssh_client, "rm hadoop-ver.tar")
        # ssh_execute_command(ssh_client, "source .profile")


if __name__ == '__main__':
    run_script()

