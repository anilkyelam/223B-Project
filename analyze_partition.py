import matplotlib
#matplotlib.use('Agg')

import sys
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
from os import listdir

def analyzeGraph(filename):
    ratios = np.zeros(20)
    sumLocalVsRemote = np.zeros(20)

    with open(filename, "r") as lawsGraph:
        linesEvaluated = 0
        for i, line in enumerate(lawsGraph):
            if (i%10) == 0:
                if 'darwini' in filename:
                    res = getLocalVsRemoteDarwini(line, i)
                else:
                    res = getLocalVsRemoteRatioPerLine(line, i)
                np.add(sumLocalVsRemote, res, out=sumLocalVsRemote)
                linesEvaluated += 1
        np.divide(sumLocalVsRemote, np.repeat(linesEvaluated, 20), out=ratios)
        print("sumLocalVsRemote: ", sumLocalVsRemote)
        resultsFile = "lvr_results_mod/"+ filename.split('.')[0] + "_results.txt"
        with open(resultsFile, "w") as res:
            for r in ratios:
                res.write("%f\n" % r)
            res.close()
        lawsGraph.close()
        return ratios

def analyzeGraphForRange(filename):
    ranges = np.zeros(20)
    nodes_per_worker = {}
    for num_partitions in range(1, 21):
        nodes_per_worker[num_partitions] = np.zeros(num_partitions)

    with open(filename, "r") as lawsGraph:
        for i, line in enumerate(lawsGraph):
            if 'darwini' in filename:
                numEdges = len(line.split(','))
            else:
                numEdges = len(line.split(' '))
            for num_partitions in nodes_per_worker.keys():
                nodes_per_worker[num_partitions][i%num_partitions] += numEdges
        
        for num_partitions in nodes_per_worker.keys():
            ranges[num_partitions-1] = max(nodes_per_worker[num_partitions]) - min(nodes_per_worker[num_partitions])
        print("Ranges: ", ranges)

        resultsFile = "range_results_mod/"+ filename.split('.')[0] + "_results.txt"
        with open(resultsFile, "w") as res:
            for r in ranges:
                res.write("%f\n" % r)
            res.close()
        lawsGraph.close()
        return ratios

def collectLVRResults(ratios):
    # sum the ratios preparatory to averaging them
    print("Ratios: ", ratios)
    np.add(sumLocalVsRemote, ratios, out=sumLocalVsRemote)

def getLocalVsRemoteRatioPerLine(line, i):
    # i is the line number, line is the string
    line = line.rstrip()
    # ratios contains the ratio of local to remote edges FOR THIS LINE
    # for each of the 20 different partition numbers.
    ratios = []
    edges = line.split(' ')
    for num_partitions in range(1, 21):
        worker = i%num_partitions
        local_edges = 0
        remote_edges = 0
        for e in edges:
            if e == '':
                continue
            e = int(e)
            if e%num_partitions == worker:
                local_edges += 1
            else:
                remote_edges += 1
        ratio = float(local_edges)/float(local_edges + remote_edges + 1)
        ratios.append(ratio)
    return ratios

# Chunks is a dictionary of 20 arrays which represent the vertex indices
# that bound the partitions for each number of partitions. For example,
# if the graph had 11 nodes:
# 1: [0, 9]
# 2: [0, 4, 9]
# 3: [0, 2, 5, 9]
# and so on
def getLocalVsRemoteChunked(line, i, chunks):
    # i is the line number, line is the string
    line = line.rstrip()
    # ratios contains the ratio of local to remote edges FOR THIS LINE
    # for each of the 20 different partition numbers.
    ratios = []
    edges = line.split(' ')
    for num_partitions in range(1, 21):
        local_edges = 0
        remote_edges = 0
        for e in edges:
            if e == '':
                continue
            e = int(e)
            workerForThisEdge = maxVertices/num_partitions #not it
            if partitioning == 'modulo' and e%num_partitions == worker:
                local_edges += 1
            elif partitioning == 'chunk' and chunkMin <= e < chunkMax:
                local_edges += 1
            else:
                remote_edges += 1
        ratio = float(local_edges)/float(local_edges + remote_edges + 1)
        ratios.append(ratio)
    return ratios

def getLocalVsRemoteDarwini(line, i):
        # i is the line number, line is the string
        line = line.rstrip()
        # ratios contains the ratio of local to remote edges FOR THIS LINE
        # for each of the 20 different partition numbers.
        ratios = []
        edges = line.split(',')
        edges[0] = edges[0].split()[1]
        for num_partitions in range(1, 21):
            worker = i%num_partitions
            local_edges = 0
            remote_edges = 0
            for e in edges:
                if e == '':
                    continue
                e = int(e)
                if e%num_partitions == worker:
                    local_edges += 1
                else:
                    remote_edges += 1
            ratio = float(local_edges)/float(remote_edges + 1)
            ratios.append(ratio)
            return ratios

def getRangeResults(filename, num_partitions):
    workers = np.zeros(num_partitions)
    with open(filename) as lawsGraph:
        for i, line in enumerate(lawsGraph):
            line = line.rstrip()
            if 'darwini' in filename:
                workers[i%num_partitions] += (line.count(',') + 1)
            else:
                workers[i%num_partitions] += (line.count(' ') + 1)
        return workers
        
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

def getAllData(files):
    mode = 'local_v_remote'
    for f in files:
        filename = f
        print("Reading " + f + "...")
        ratios = analyzeGraph(filename)

def plotAll(path, mode='lvr'):
    for filename in listdir(path):
        if 'darwini' in filename:
            continue
        ratios = []
        fullName = path + "/" + filename
        with open(fullName) as f:
            for n in f:
                ratios.append(float(n))
        print(filename, ": ", ratios)
        label = filename.split('.')[0].split('_')[0]
        plt.plot(np.arange(2, 21), ratios[1:], label=label)

    plt.xlabel("Partitions")
    if mode == 'range':
        plt.ylabel("Range of edges/node as % of max. edges/node")
       # plt.title("Range of edges/node vs. number of partitions\n for various graphs")
    else:
        plt.ylabel("Ratio of local to remote edges")
    plt.xticks(np.arange(2, 21, 2))
    plt.legend()
    plt.savefig("local_remote.png")
    plt.show()

def testFiles():
    files = ["enwiki-2015.graph-txt",
                "twitter.graph-txt",
                "uk-2007-05.graph-txt",
                "wordassociation-2011.graph-txt",
                "cnr-2000.graph-txt",
                "darwini-50m-edges.graph-txt",
                "dblp-2011.graph-txt",
                "enron.graph-txt",
                "hollywood-2011.graph-txt"]
    for f in files:
        ff = open("inputs/" + f)

def main():
    #getAllData(sys.argv[1:])
    plotAll("range_results_mod", mode='range')
    #analyzeGraphForRange("small_inputs/enwiki-2015.graph-txt")
main()
