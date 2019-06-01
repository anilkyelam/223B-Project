import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt

# print("Number of processors: ", mp.cpu_count())

def readLAWSfile(filename):
    nodes = []
    with open(filename) as lawsGraph:
        for i, line in enumerate(lawsGraph):
            line = line.rstrip()
            node = line.split()
            nodes.append(len(node))
            # print(line)
    return nodes
        
def testPartitioning(numWorkers, nodes):
    # Use round robin partitioning by hashing the vertices to see how many edges each worker would get
    workers = [0] * numWorkers
    for i, numEdges in enumerate(nodes):
        workers[i%numWorkers] += numEdges
    mx = max(workers)
    mn = min(workers)
    return (mx - mn)/float(mx)*100

def varyNumPartitions(nodes, lo=3, hi=1000, step=1):
    percentDiffs = []
    for i in np.arange(lo, hi, step):
        percentDiffs.append(testPartitioning(i, nodes))
    return percentDiffs

def plotDiffsVsPartitions(lo, hi, step=1):
    files = ["enwiki-2015.graph-txt", "twitter.graph-txt", "uk-2007-05.graph-txt", "wordassociation-2011.graph-txt"]
    for f in files:
        filename = "inputs/" + f
        print("Reading ", f, "...")
        nodes = readLAWSfile(filename)
        print("Plotting ", f, "...")
        percentDiffs = varyNumPartitions(nodes, lo, hi, step)
        plt.plot(np.arange(lo, hi, step), percentDiffs, label=f.split('.')[0])

    plt.xlabel("Partitions")
    plt.ylabel("Range of number of edges/node (%)")
    plt.title("Range of edges/node vs. number of partitions\n for various graphs")
    plt.legend()
    plt.savefig("test_small.png")
    plt.show()

# readLAWSfile("inputs/enwiki-2015.graph-txt")
plotDiffsVsPartitions(3, 100, 20)
# print(nodes)
