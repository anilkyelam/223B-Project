import math
import os
import sys
import re
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

# input_file = "D:\Scratch\\uk-2007-05\\uk-2007-05.graph-txt"
# input_style = "law"

<<<<<<< HEAD
input_files_dict = {
    # "darwini-50m"               : ["D:\Scratch\\darwini-50m-edges.graph-txt", "darwini", 154549],
    
    "cnr-2000"                  : ["D:\Scratch\\cnr-2000\\cnr-2000.graph-txt", "law"],
    "dblp-2011"                 : ["D:\Scratch\\dblp-2011\\dblp-2011.graph-txt", "law"],
    "enron"                     : ["D:\Scratch\\enron\\enron.graph-txt", "law"],
=======
'''input_files_dict = {
    "darwini-50m"               : ["D:\Scratch\\darwini-50m-edges.graph-txt", "darwini", 154549],
>>>>>>> a71489557b298c8f20c36ef359dfac6c426f87e4
    "wordassociation-2011"      : ["D:\Scratch\\wordassociation-2011\\wordassociation-2011.graph-txt", "law"],
    "enwiki-2015"               : ["D:\Scratch\\enwiki-2015\enwiki-2015.graph-txt", "law"],
<<<<<<< HEAD
    "ljournal-2008"             : ["D:\Scratch\\ljournal-2008\\ljournal-2008.graph-txt", "law"],
    "hollywood-2009"            : ["D:\Scratch\\hollywood-2009\\hollywood-2009.graph-txt", "law"],
    "hollywood-2011"            : ["D:\Scratch\\hollywood-2011\\hollywood-2011.graph-txt", "law"],
    "twitter"                   : ["D:\Scratch\\twitter\\twitter.graph-txt", "law"],
    "uk-2002"                   : ["D:\Scratch\\uk-2002\\uk-2002.graph-txt", "law"],
    "uk-2007-05@1000000"        : ["D:\Scratch\\uk-2007-05@1000000\\uk-2007-05@1000000.graph-txt", "law"],
=======
}'''

input_files_dict = {
    "darwini-50m"               : ["input/darwini-50m-edges.graph-txt", "darwini", 154549],
    "wordassociation-2011"      : ["input/wordassociation-2011.graph-txt", "law"],
    "uk-2007-05"                : ["input/uk-2007-05.graph-txt", "law"],
    "twitter"                   : ["input/twitter.graph-txt", "law"],
    "enwiki-2015"               : ["input/enwiki-2015.graph-txt", "law"],
    "cnr2000"                   : ["cnr-2000.graph-txt", "law"],
    "dblp"                      : ["dblp-2011.graph.txt", "law"],
    "enron"                     : ["enron.graph-txt", "law"],
    "hollywood-2011"            : ["hollywood-2011.graph-txt", "law"],
>>>>>>> a71489557b298c8f20c36ef359dfac6c426f87e4
}


source_folder = os.path.dirname(os.path.abspath(__file__))
graph_plots_folder = os.path.join(source_folder, "graph_plots")

class PartitionStats:
    def __init__(self, input_graph, total_vertices, partition_style, partition_count):
        self.input_graph = input_graph
        self.total_vertices = total_vertices
        self.partition_style = partition_style
        self.partition_count = partition_count 
        self.partition_vtx_counter = Counter() 
        self.partition_edges_counter = Counter() 
        self.partition_local_edges_counter = Counter()
        self.inter_partition_edges_count = 0

    def get_total_edges(self):
        return sum(self.partition_edges_counter.values())

    def get_normalized_edge_range(self):
        edge_count = list(self.partition_edges_counter.values())
        return (max(edge_count) - min(edge_count))*100 / max(edge_count)

    def get_variation_coeff_edge_range(self):
        edge_count = list(self.partition_edges_counter.values())
        return np.std(edge_count)/np.mean(edge_count)

    def get_inter_partition_edge_ratio(self):
        return self.inter_partition_edges_count/self.get_total_edges()

    def __str__(self):
        return "Total Vertices: {0}, Edges: {1}".format(self.total_vertices, self.get_total_edges()) + "\n" \
                "Normalized edge range: " + str(round(self.get_normalized_edge_range(), 2)) + "\n" + \
                "Inter-Partition Edges: " + str(self.inter_partition_edges_count) + "\n" + \
                "Inter-Partition Edges Ratio: " + str(round(self.get_inter_partition_edge_ratio(), 2))
                # "Partition Vertices: " + str(self.partition_vtx_counter) + "\n" + \
                # "Partition Normalized Edges Range: " + str(self.partition_edges_counter) + "\n" + \
                # "Partition Local Edges: " + str(self.partition_local_edges_counter) + "\n" + \
                # "Total Local Edges: " + str(sum(self.partition_local_edges_counter.values())) + "\n" + \
                # "Inter-Partition Edges: " + str(self.inter_partition_edges_count)


# Get partition number
def get_partition(vertex_id, partition_count, partition_style = "modulo", total_vertices=None):
    partition_id = -1
    if partition_style == "modulo":
        partition_id = vertex_id % partition_count
    if partition_style == "range":
        step_size = total_vertices/partition_count
        partition_id = int(vertex_id / step_size)
    
    return partition_id 


def parse_input_get_stats(input_file_name, partition_styles_list, partition_counts_list):
    input_file_path = input_files_dict[input_file_name][0]
    input_style = input_files_dict[input_file_name][1]

    with open(input_file_path) as fp:  
        line = fp.readline()

        # Get total number of vertices. For LAW datasets, it's in the first line of the file. 
        # For darwini, i'm just hardcoding the number for now to avoid two passes of the file
        total_vertices = -1
        if input_style == "law":
            # Ignore first line, it just has number of vertices
            total_vertices = int(line)
            line = fp.readline()
        else:
            total_vertices = input_files_dict[input_file_name][2]
        
        cnt = 0
        vertex_id = -1
        parition_vtx_counter = Counter()
        parition_edge_counter = Counter()
        partition_local_edge_counter = Counter()
        inter_partition_edges = 0
        stats_dict = {}

        while line:
            splits = re.split(",|\t|\n| ", line)
            edges = list(map(int, filter(None, splits)))
            
            if input_style == "darwini":
                vertex_id = edges[0]
                edges.pop()
            else:
                vertex_id = cnt

            if cnt % 1000000 == 0:
                print("Processed {0} million vertices".format(cnt/1000000))
            # print(vertex_id, ": ", edges)

            # For each line, work with all partition styles and counts
            for partition_style in partition_styles_list:
                for partition_count in partition_counts_list:
                    
                    if (partition_style, partition_count) not in stats_dict.keys():
                        stats_dict[(partition_style, partition_count)] = PartitionStats(input_file_name, total_vertices, partition_style, partition_count)

                    partition_id = get_partition(vertex_id, partition_count, partition_style, total_vertices)
                    stats_dict[(partition_style, partition_count)].partition_vtx_counter[partition_id] += 1
                    for edge in edges:
                        stats_dict[(partition_style, partition_count)].partition_edges_counter[partition_id] += 1
                        if get_partition(edge, partition_count, partition_style, total_vertices) == partition_id:
                            stats_dict[(partition_style, partition_count)].partition_local_edges_counter[partition_id] += 1
                        else:
                            stats_dict[(partition_style, partition_count)].inter_partition_edges_count += 1

            line = fp.readline()
            cnt += 1

        for k,v in stats_dict.items():
            print("=========", input_file_name, k, "=========")
            print(v)

        return stats_dict.values()


def plot_partition_stats(input_file, partition_stats):

    # Plot normalized edge range
    fig, ax = plt.subplots(1, 1)
    fig.suptitle("Normalized edge range for graph: " + input_file)
    ax.set_ylabel("Normalized edge count range")
    ax.set_xlabel("Log(Number of partitions)")

    for partition_style in ["modulo", "range"]:
        x = [stats.partition_count for stats in partition_stats if stats.partition_style == partition_style]
        y = [round(stats.get_normalized_edge_range(), 2) for stats in partition_stats if stats.partition_style == partition_style]
        y1 = [round(stats.get_variation_coeff_edge_range(), 2) for stats in partition_stats if stats.partition_style == partition_style]
        print("=== PartitionStyle: {0}, Num of Partitions, CV, Normalized Edge Range === ".format(partition_style))
        for el in list(zip(x, y1, y)):
            print("{:5.2f} {:5.2f} {:5.2f}".format(el[0], el[1], el[2]))
        ax.plot(x, y, label="partition:" + partition_style)

    plt.legend()
    plt.savefig(os.path.join(graph_plots_folder, "plt_edge_{0}.png".format(input_file)))
    # plt.show()
    
    # Plot inter-partition edge count
    fig, ax = plt.subplots(1, 1)
    fig.suptitle("Inter-partition edge for graph: " + input_file)
    ax.set_ylabel("Inter-partition edge ratio")
    ax.set_xlabel("Log(Number of partitions)")

    for partition_style in ["modulo", "range"]:
        x = [stats.partition_count for stats in partition_stats if stats.partition_style == partition_style]
        y = [round(stats.get_inter_partition_edge_ratio(), 2) for stats in partition_stats if stats.partition_style == partition_style]
        print("=== PartitionStyle: {0}, Num of Partitions, Inter-Partition Edge Ratio === ".format(partition_style))
        for el in list(zip(x, y)):
            print("{:5.2f} {:5.2f}".format(el[0], el[1]))
        ax.plot(x, y, label="partition:" + partition_style)

    plt.legend()
    plt.savefig(os.path.join(graph_plots_folder, "plt_ipedges_{0}.png".format(input_file)))
    # plt.show()


def main():

    input_files = ["hollywood-2009", "ljournal-2008", "uk-2007-05@1000000" ]  
    # input_files = ["cnr-2000", "dblp-2011", "enron", "wordassociation-2011", "enwiki-2015", "hollywood-2011", "twitter", "uk-2002" ]  
    partition_counts_list = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    # partition_counts_list = [4, 8]
    partition_styles_list = ["modulo", "range"]
    
    for input_file in input_files:
        print("Analyzing input graph: {0}".format(input_file))
        all_stats = parse_input_get_stats(input_file, partition_styles_list, partition_counts_list)
        plot_partition_stats(input_file, all_stats)


if __name__ == "__main__":
    main()