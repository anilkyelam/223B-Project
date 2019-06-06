"""
Aggregates Power and other metrics across multiple experiments and generates plots
"""

import argparse
import os
import re
import math
import shutil
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import plot_one_experiment
from plot_one_experiment import ExperimentSetup
import run_experiments
import numpy as np
from pprint import pprint


class ExperimentMetrics:
    experiment_id = None
    experiment_setup = None
    is_success = None
    gc_time_ms = None
    total_edges = None
    total_vertices = None
    time_load_input_ms = None
    time_sstep_total_ms = None
    time_total_ms = None

    def __init__(self, experiment_id, experiment_setup):
        self.experiment_id = experiment_id
        self.experiment_setup = experiment_setup
        self.parse_log_file()

    def parse_log_file(self):
        experiment_dir_path = os.path.join(plot_one_experiment.results_base_dir, self.experiment_id)
        print("Parsing experiment {0}".format(self.experiment_id))

        # Parse giraph log file to get job completion metrics
        all_timestamp_list = []
        stages_start_end_times = {}
        giraph_log_full_path = os.path.join(experiment_dir_path, run_experiments.designated_giraph_driver_node,
                                        plot_one_experiment.giraph_log_file_name)
        with open(giraph_log_full_path, "r") as file_:
            content = file_.read()

            matches = re.search("Job (.+) completed successfully", content)
            if matches:
                self.is_success = True
            else:
                return

            self.total_map_tasks = search_get_number("Launched map tasks=([0-9]+)", content)
            self.gc_time_ms = search_get_number("GC time elapsed \(ms\)=([0-9]+)", content)
            self.total_edges = search_get_number("Aggregate edges=([0-9]+)", content)
            self.total_vertices = search_get_number("Aggregate vertices=([0-9]+)", content)
            self.time_initialize_ms = search_get_number("Initialize \(ms\)=([0-9]+)", content)
            self.time_load_input_ms = search_get_number("Input superstep \(ms\)=([0-9]+)", content)
            self.time_sstep_0 = search_get_number("Superstep 0 SimplePageRankComputation \(ms\)=([0-9]+)", content)
            self.time_sstep_1 = search_get_number("Superstep 1 SimplePageRankComputation \(ms\)=([0-9]+)", content)
            self.time_sstep_2 = search_get_number("Superstep 2 SimplePageRankComputation \(ms\)=([0-9]+)", content)
            self.time_sstep_3 = search_get_number("Superstep 3 SimplePageRankComputation \(ms\)=([0-9]+)", content)
            self.time_sstep_4 = search_get_number("Superstep 4 SimplePageRankComputation \(ms\)=([0-9]+)", content)
            self.time_total_ms = search_get_number("Total \(ms\)=([0-9]+)", content)
            self.time_sstep_total_ms = self.time_sstep_0 + self.time_sstep_1 + self.time_sstep_2 + self.time_sstep_3 + self.time_sstep_4


def search_get_number(pattern, content):
    matches = re.search(pattern, content)
    if matches:
        return int(matches.group(1))
    else:
        return None



# Loads all experiment results
def load_all_experiments(start_time, end_time):
    experiments = []

    all_experiment_folders = [os.path.join(plot_one_experiment.results_base_dir, item)
                       for item in os.listdir(plot_one_experiment.results_base_dir)
                       if item.startswith("Exp-")
                       and os.path.isdir(os.path.join(plot_one_experiment.results_base_dir, item))]

    for experiment_dir_path in all_experiment_folders:
        experiment_time = datetime.fromtimestamp(os.path.getctime(experiment_dir_path))
        if start_time < experiment_time < end_time:
            experiment_id = os.path.basename(experiment_dir_path)
            # print("Loading " + experiment_id)
            setup_file_path = os.path.join(experiment_dir_path, "setup_details.txt")
            experiment_setup = ExperimentSetup(setup_file_path)
            experiment_setup.experiment_id = experiment_id
            if start_time < experiment_setup.experiment_start_time < end_time:
                experiments.append(experiment_setup)

    return sorted(experiments, key=lambda x: x.experiment_start_time, reverse=True)


# Filters
global_start_time = datetime.strptime('2019-05-30 00:00:00', "%Y-%m-%d %H:%M:%S")
global_end_time = datetime.now()
filter_experiments = True
experiments_filter = [
    # "Run-2019-06-03-10-36-31",        # WordAssociation graph
    # "Run-2019-06-03-12-44-30",        # en wiki graph
    # "Run-2019-06-03-13-50-42",        # hollywood graph
    # "Run-2019-06-03-14-21-09"           # hollywood graph 3 runs
    # "Run-2019-06-03-15-27-03"
    # "Run-2019-06-03-16-28-35"           # enwiki 10 runs each
    # "Run-2019-06-03-19-42-19"           # enwiki two partitioners, from 4 to 20 workers
    # "Run-2019-06-03-22-36-42"           # hollywood two partitioners, from 10 to 20 workers
    # "Run-2019-06-04-17-17-37", "Run-2019-06-04-22-11-38",           # All graphs, two partitioners, from 2 to 18 workers
    "Run-2019-06-05-15-12-48"
]
link_rates_filter = [0]


# The results directory is full of folders corresponding to all the experiments ever performed.
# This one filters relevant experiments to parse and plot.
def filter_experiments_to_consider(all_experiments):
    experiments_to_consider = []

    for experiment in all_experiments:
        print(experiment.experiment_id,  experiment.experiment_group)
        if (not filter_experiments) or experiment.experiment_id in experiments_filter \
            or experiment.experiment_group in experiments_filter:
                if experiment.link_bandwidth_mbps in link_rates_filter:
                    # print(experiment.input_size_gb, experiment.link_bandwidth_mbps)
                    experiments_to_consider.append(experiment)

    return experiments_to_consider


# Print some relevant stats from collected metrics
def print_stats(exp_metrics):
    for exp in exp_metrics:
        exp_setup = exp.experiment_setup
        if exp.is_success:
            print("{:<40s} {:<20s} {:2d} {:<5s} V:{:6d} E:{:8d} L:{:6d} E:{:6d} T:{:6d}".format(exp_setup.input_graph_file, str(exp_setup.partitioner), exp_setup.num_workers, "Success", 
                exp.total_vertices, exp.total_edges, exp.time_load_input_ms, exp.time_sstep_total_ms, exp.time_total_ms))
        else:
            print("{:<40s} {:<20s} {:2d} {:<5s}".format(exp_setup.input_graph_file, str(exp_setup.partitioner), exp_setup.num_workers, "Failed"))
        pass

    # exp_confs = sorted(set([(e.experiment_setup.input_graph_file, e.experiment_setup.partitioner, e.experiment_setup.num_workers) for e in exp_metrics]))
    # for exp_conf in exp_confs:
    #     current_conf_exps = [e for e in exp_metrics if e.is_success and e.experiment_setup.input_graph_file == exp_conf[0] 
    #                             and e.experiment_setup.num_workers == exp_conf[2] 
    #                             and e.experiment_setup.partitioner == exp_conf[1]]
    #     mean_load_time = np.mean([e.time_load_input_ms for e in current_conf_exps])
    #     std_load_time = np.std([e.time_load_input_ms for e in current_conf_exps])
    #     mean_exec_time = np.mean([e.time_sstep_total_ms for e in current_conf_exps])
    #     std_exec_time = np.std([e.time_sstep_total_ms for e in current_conf_exps])
    #     mean_total_time = np.mean([e.time_total_ms for e in current_conf_exps])
    #     std_total_time = np.std([e.time_total_ms for e in current_conf_exps])

    #     print("{:<25s} {:<20s} {:2d} L:{:6.0f} ({:6.0f}) E:{:6.0f} ({:6.0f}) T:{:6.0f} ({:6.0f})".format(exp_conf[0], exp_conf[1], exp_conf[2], 
    #               mean_load_time, std_load_time, mean_exec_time, std_exec_time, mean_total_time, std_total_time))


def main():

    # Parse results
    all_experiments = load_all_experiments(global_start_time, global_end_time)
    relevant_experiments = filter_experiments_to_consider(all_experiments)
    exp_metrics = [ExperimentMetrics(e.experiment_id, e) for e in relevant_experiments]

    # Parse args and call relevant action
    parser = argparse.ArgumentParser("Generates different kinds of plots from results across different experiments")
    parser.add_argument('--printstats', action='store_true', help='Prints exp statistics collected from logs')
    args = parser.parse_args()

    # Print any stats we might want to look at
    if args.printstats:
        print_stats(exp_metrics)


if __name__ == "__main__":
    main()

