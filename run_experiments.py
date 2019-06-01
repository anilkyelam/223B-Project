"""
Runs experiments on hdfs+yarn cluster using giraph jobs while collecting resource usage readings.
TODO: Repurpose it to target the AWS Machines!!
"""

import argparse
import datetime
import paramiko
import os
import time
import json
import sys
import traceback
from scp import SCPClient


# Experimental Setup constants
hdfs_nodes = ["giraph1", "giraph2", "giraph3", "giraph4"]
designated_giraph_driver_node = "giraph1"
designated_hdfs_master_node = "giraph1"
padding_in_secs = 5


# Since we are dealing with Windows local machine and Linux remote machines
def path_to_linux_style(path):
    return path.replace('\\', '/')
def path_to_windows_style(path):
    return path.replace('/', '\\')


# Remote node constants
remode_node_user = "ubuntu"
remote_home_folder = '/home/ubuntu/giraph_runs'
remote_scripts_folder = path_to_linux_style(os.path.join(remote_home_folder, "node-scripts"))
remote_results_folder = path_to_linux_style(os.path.join(remote_home_folder, "results"))
etc_folder = "/etc/"
hosts_file_name = "hosts_file"


# Local constants
source_folder = os.path.dirname(os.path.abspath(__file__))
local_node_scripts_folder = os.path.join(source_folder, "node-scripts")
local_results_folder = os.path.join(source_folder, "results")
prepare_for_experiment_file = 'prepare_for_experiment.sh'
start_sar_readings_file = 'start_sar_readings.sh'
stop_sar_readings_file = 'stop_sar_readings.sh'
start_power_readings_file = 'start_power_readings.sh'
stop_power_readings_file = 'stop_power_readings.sh'
cleanup_after_experiment_file = 'cleanup_after_experiment.sh'
run_giraph_job_file = 'run_giraph_job.sh'
log_verbose = True


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
    if log_verbose: print(output)
    return output


# Create remote folder if it does not exist
def create_folder_if_not_exists(ssh_client, remote_folder_path):
    with ssh_client.open_sftp() as ftp_client:
        try:
            ftp_client.listdir(remote_folder_path)
        except IOError:
            ftp_client.mkdir(remote_folder_path)


# Sets up each node - copies hosts file to each node
def set_up_on_each_node():
    for node_name in hdfs_nodes:
        with create_ssh_client(node_name) as ssh_client:    
            print("Setting up hosts file on " + node_name)
            script_file = path_to_linux_style(os.path.join(remote_scripts_folder, hosts_file_name))
            ssh_execute_command(ssh_client, 'cp {0} /etc/hosts'.format(script_file), sudo=True)


# Reverts changes on each node - cleanup to hosts file on all nodes, resets TC, refreshes link interface, etc.
def clean_up_on_each_node():
    for node_name in hdfs_nodes:
        with create_ssh_client(node_name) as ssh_client:
            print("Resetting TC and network interface on " + node_name)
            reset_network_rate_limit(ssh_client)


# Starts HDFS + YARN cluster for spark runs
def start_hdfs_yarn_cluster():
    print("Starting hdfs and yarn cluster")
    master_node_ssh_client = create_ssh_client(designated_hdfs_master_node)
    ssh_execute_command(master_node_ssh_client, "bash hadoop/sbin/start-dfs.sh && bash hadoop/sbin/start-yarn.sh")

    # Check if the cluster is up and running properly i.e., all the data nodes are up
    output = ssh_execute_command(master_node_ssh_client, "hadoop/bin/hdfs dfsadmin -report")
    errors = ["Node {0} not found in the cluster report\n".format(node_name) for node_name in hdfs_nodes 
        if node_name != designated_hdfs_master_node and node_name not in output] 
    if errors.__len__() > 0:
        print(errors)
        raise Exception("Cluster is not configured properly!")
    print ("Cluster is up and running!")


# Starts HDFS + YARN cluster for spark runs
def stop_hdfs_yarn_cluster():
    # Remove cache directives so that when HDFS starts up again, your prepare_env_script doesn't think the file is already in cache
    # TODO: Don't worry about caching for now.
    # print("Removing hdfs cache directives of input files")
    master_node_ssh_client = create_ssh_client(designated_hdfs_master_node)
    # ssh_execute_command(master_node_ssh_client, "hadoop/bin/hdfs cacheadmin -removeDirectives -path '/user/ayelam'")

    print("Stopping hdfs and yarn cluster")
    ssh_execute_command(master_node_ssh_client, "bash hadoop/sbin/stop-yarn.sh && bash hadoop/sbin/stop-dfs.sh")


# Set up environment for each experiment
def prepare_env_for_experiment(ssh_client):
    print("Preparing env for experiment")
    script_file = path_to_linux_style(os.path.join(remote_scripts_folder, prepare_for_experiment_file))
    ssh_execute_command(ssh_client, 'bash {0}'.format(script_file))


# Starts SAR readings
def start_sar_readings(ssh_client, node_exp_folder_path, granularity_in_secs=1):
    print("Starting SAR readings")
    script_file = path_to_linux_style(os.path.join(remote_scripts_folder, start_sar_readings_file))
    ssh_execute_command(ssh_client, 'bash {0} {1} {2}'.format(script_file, node_exp_folder_path, granularity_in_secs))


# Starts giraph job with specified algorithm (giraph class name) and input graph.
def run_giraph_job(ssh_client, node_exp_folder_path, giraph_class_name, input_graph_name):
    print("Starting giraph job")
    script_file = path_to_linux_style(os.path.join(remote_scripts_folder, run_giraph_job_file))
    ssh_execute_command(ssh_client, 'bash {0} {1} {2} {3} {4}'.format(script_file, remote_scripts_folder, node_exp_folder_path, 
        giraph_class_name, input_graph_name))


# Stops SAR readings
def stop_sar_readings(ssh_client):
    print("Stopping SAR readings")
    script_file = path_to_linux_style(os.path.join(remote_scripts_folder, stop_sar_readings_file))
    ssh_execute_command(ssh_client, 'bash {0}'.format(script_file))


# Cleans up each node after experiment
def cleanup_env_post_experiment(ssh_client):
    print("Cleaning up post environment")
    script_file = path_to_linux_style(os.path.join(remote_scripts_folder, cleanup_after_experiment_file))
    ssh_execute_command(ssh_client, 'bash {0}'.format(script_file))


# Clears all the data from page cache, dentries and inodes. This is to not let one experiment affect the next one due to caching.
def clear_page_inode_dentries_cache(ssh_client):
    print("Clearing all file data caches")
    cache_clear_command = "bash -c 'echo 3 > /proc/sys/vm/drop_caches'"
    ssh_execute_command(ssh_client, cache_clear_command, sudo=True)


# Set rate limit for egress network traffic on each node
def set_network_rate_limit(ssh_client, rate_limit_mbps):

    if rate_limit_mbps == 0:
        print("Not setting any network rate limit")
        return

    # Set the rate limit with TBF qdisc
    print("Setting network rate limit to {0} mbps".format(rate_limit_mbps))
    tc_qdisc_set_tbf_rate_limit = 'tc qdisc add dev eth0 root tbf rate {0}mbit burst 1mbit latency 10ms'
    ssh_execute_command(ssh_client, tc_qdisc_set_tbf_rate_limit.format(rate_limit_mbps), sudo=True)

    # Check if rate limiting is properly set.ec2-54-187-93-140.us-west-2.compute.amazonaws.com
    tc_qdisc_show_command = 'tc qdisc show  dev eth0'
    output = ssh_execute_command(ssh_client, tc_qdisc_show_command)
    token_rate_text = "rate {0}Mbit".format(rate_limit_mbps) if rate_limit_mbps % 1000 != 0 \
        else "rate {0}Gbit".format(int(rate_limit_mbps/1000))
    if "tbf" not in output or token_rate_text not in output:
        raise Exception("Setting link bandwidth failed!")


# Resets any traffic control qdisc set for a node, which then defaults to pfifo.
def reset_network_rate_limit(ssh_client):
    print("Resetting network rate limit, deleting any custom qdisc")
    tc_qdist_reset_command = 'tc qdisc del dev eth0 root'
    ssh_execute_command(ssh_client, tc_qdist_reset_command, sudo=True)


# Runs a single experiment with specific configurations like input graph and network rate
def run_experiment(exp_run_id, exp_run_desc, giraph_class_name, input_graph_name, link_bandwidth_mbps, cache_hdfs_file):
    experiment_start_time = datetime.datetime.now()
    experiment_id = "Exp-" + experiment_start_time.strftime("%Y-%m-%d-%H-%M-%S")

    try:
        experiment_folder_name = experiment_id
        print("Starting experiment: ", experiment_id)

        # Prepare for experiment, run one-time prepare script on the driver node
        experiment_folder_path = path_to_linux_style(os.path.join(remote_results_folder, experiment_folder_name))
        driver_ssh_client = create_ssh_client(designated_giraph_driver_node)
        prepare_env_for_experiment(driver_ssh_client)

        # Prepare environment and start collecting readings on each node
        for node_name in hdfs_nodes:
            with create_ssh_client(node_name) as ssh_client:
                print("Setting up for giraph job on node " + node_name)
                
                # Make sure directory structure exists driver node
                create_folder_if_not_exists(ssh_client, experiment_folder_path)

                node_exp_folder_path = path_to_linux_style(os.path.join(experiment_folder_path, node_name))
                create_folder_if_not_exists(ssh_client, node_exp_folder_path)

                # Clear all kinds of file data from caches
                clear_page_inode_dentries_cache(ssh_client)

                # Delete any non-default qdisc and set required network rate.
                reset_network_rate_limit(ssh_client)
                set_network_rate_limit(ssh_client, link_bandwidth_mbps)

                start_sar_readings(ssh_client, node_exp_folder_path)

        # Wait a bit before the run
        time.sleep(padding_in_secs)

        # Kick off the run
        giraph_job_start_time = datetime.datetime.now()
        driver_exp_folder_path = path_to_linux_style(os.path.join(experiment_folder_path, designated_giraph_driver_node))
        
        with create_ssh_client(designated_giraph_driver_node) as ssh_client:
            run_giraph_job(ssh_client, driver_exp_folder_path, giraph_class_name, input_graph_name)
        # input("Press [Enter] to continue.")

        giraph_job_end_time = datetime.datetime.now()

        # Wait a bit after the run
        time.sleep(padding_in_secs)

        # Stop collecting SAR readings on each node, and copy results from each node to local machine
        for node_name in hdfs_nodes:
            with create_ssh_client(node_name) as ssh_client:
                stop_sar_readings(ssh_client)

                with SCPClient(ssh_client.get_transport()) as scp:
                    scp.get(experiment_folder_path, local_results_folder, recursive=True)

        # Record experiment setup details for later use
        local_experiment_folder = os.path.join(local_results_folder, experiment_folder_name)
        setup_file = open(os.path.join(local_experiment_folder, "setup_details.txt"), "w")
        json.dump(
            {
                "ExperimentGroup": exp_run_id,
                "ExperimentGroupDesc": exp_run_desc,
                "GiraphClassName": giraph_class_name,
                "InputHdfsCached": cache_hdfs_file,
                
                "ExperimentId": experiment_id,
                "ExperimentStartTime": experiment_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "GiraphJobStartTime": giraph_job_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "GiraphJobEndTime": giraph_job_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "HdfsNodes": hdfs_nodes,
                "HdfsMasterNode": designated_hdfs_master_node,
                "GiraphDriverNode": designated_giraph_driver_node,
                "InputGraphFile": input_graph_name,
                "LinkBandwidthMbps": link_bandwidth_mbps,
                "PaddingInSecs": padding_in_secs,
                "Comments": ""
            }, setup_file, indent=4, sort_keys=True)

        # Run one-time cleanup script on driver node 
        cleanup_env_post_experiment(driver_ssh_client)
        driver_ssh_client.close()

        print("Experiment: {0} done!!".format(experiment_id))
        return experiment_id
    except:
        print("Experiment: {0} failed!!".format(experiment_id))
        print(traceback.format_exc())
        return None


def copy_src_files():
    for node_name in hdfs_nodes:
        print("Copying source files to node: " + node_name)
        with create_ssh_client(node_name) as ssh_client:
            # Make sure the directory structure exists on driver node
            create_folder_if_not_exists(ssh_client, remote_home_folder)
            create_folder_if_not_exists(ssh_client, remote_results_folder)

            # Copy source files to driver node
            with SCPClient(ssh_client.get_transport()) as scp:
                scp.put(local_node_scripts_folder, remote_home_folder, recursive=True)


# Set up environment for experiments
def setup_env():
    set_up_on_each_node()
    start_hdfs_yarn_cluster()


# Run experiments
def run(exp_run_desc):
    giraph_class_name = "SimplePageRankComputation"

    input_graph_files = [ "uk-2002.graph-txt" ] # "uk-2007-05.graph-txt", "twitter.graph-txt", "darwini-2b-edges", "darwini-5b-edges" ]
    link_bandwidth_mbps = [1000]   # [200, 500, 1000, 2000, 3000, 5000, 8000, 10000]
    iterations = range(1, 2)
    cache_hdfs_input = False

    # Command line arguments
    exp_run_id = "Run-" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Run all experiments
    for iter_ in iterations:
        for link_bandwidth in link_bandwidth_mbps:
            for input_graph_name in input_graph_files:
                print("Running experiment: {0}, {1}, {2}".format(iter_, input_graph_name, link_bandwidth))
                run_experiment(exp_run_id, exp_run_desc, giraph_class_name, input_graph_name, link_bandwidth, cache_hdfs_file=cache_hdfs_input)
                # time.sleep(1*60)


def teardown_env():  
    print("Tearing down the environment...")      
    stop_hdfs_yarn_cluster()
    clean_up_on_each_node()


def main():
    # Parse args and call relevant action
    parser = argparse.ArgumentParser("Runs experiments on hdfs+yarn cluster using giraph jobs")
    parser.add_argument('--setup', action='store_true', help='sets up environment, including bringing up hadoop cluster')
    parser.add_argument('--teardown', action='store_true', help='clean up environment, including stopping the hadoop cluster')
    parser.add_argument('--refresh', action='store_true', help='copy updated source scripts to driver node')
    parser.add_argument('--run', action='store_true', help='runs experiments')
    parser.add_argument('--desc', action='store', help='description for the current runs')
    parser.add_argument('-v', '--verbose', action='store', help='print verbose logs for debugging')
    args = parser.parse_args()

    if args.verbose:
        log_verbose = True

    if args.setup:
        copy_src_files()
        setup_env()

    if args.refresh:
        copy_src_files()

    if args.run:
        assert args.desc is not None, 'Provide description with --desc parameter for this run!'
        run(args.desc)

    if args.teardown:
        teardown_env()


if __name__ == '__main__':
    main()
