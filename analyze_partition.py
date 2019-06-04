import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp

# print("Number of processors: ", mp.cpu_count())
sumLocalVsRemote = np.zeros(20)
pool = mp.Pool(mp.cpu_count())

def analyzeGraph(filename):
    local_edges = np.zeros(num_partitions)
    remote_edges = np.zeros(num_partitions)
    workers = np.zeros(num_partitions)
    ratios = [20]
    with open(filename, "r") as lawsGraph:
        linesEvaluated = 0
        for i, line in enumerate(lawsGraph):
            # do parallel line processing w/ getLocalVsRemoteRatioPerLine() or getRangeResults
            if (i%10000) == 0:
                pool.apply_async(getLocalVsRemoteRatioPerLine, args=(line, i), callback=collectLVRResults)
                linesEvaluated += 1
        pool.close()
        pool.join()
        np.divide(sumLocalVsRemote, linesEvaluated, out=ratios)
        resultsFile = "results/"+ filename.split()[0] + "_results.txt"
        with open(resultsFile) as res:
            for r in ratios:
                res.write("%f\n" % r)
            res.close()
        lawsGraph.close()
        return ratios


def collectLVRResults(ratios):
    # sum the ratios preparatory to averaging them
    np.add(sumLocalVsRemote, ratios, out=sumLocalVsRemote)

def getLocalVsRemoteRatioPerLine(line, i):
    # i is the line number, line is the string
    line = line.rstrip()
    # ratios contains the ratio of local to remote edges FOR THIS LINE
    # for each of the 20 different partition numbers.
    ratios = [20]
    if 'darwini' in filename:
        edges = line.split(',')
        edges[0] = edges[0].split()[1]
    else:
        edges = line.split(' ')
    for num_partitions in range(1, 21):
        worker = i%num_partitions
        local_edges = 0
        remote_edges = 0
        for e in edges:
            e = int(e)
            if e%num_partitions == worker:
                local_edges += 1
            else:
                remote_edges += 1
        ratios.append(local_edges/(remote_edges+1))
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

def plotDiffsVsPartitions(lo, hi, step=1):
    files = ["enwiki-2015.graph-txt",
            "wordassociation-2011.graph-txt",
            "cnr-2000.graph-txt",
            # "darwini-50m-edges.graph-txt",
            "dblp-2011.graph-txt",
            "enron.graph-txt",
            "hollywood-2011.graph-txt",
            "twitter.graph-txt",
            "uk-2007-05.graph-txt",
           ]
    mode = 'local_v_remote'
    for f in files:
        filename = "small_inputs/" + f
        print("Reading " + f + "...")
        ratios = analyzeGraph(filename)
        plt.plot(np.arange(1, 21), ratios, label=f.split('.')[0])

    plt.xlabel("Partitions")
    if mode == 'range':
        plt.ylabel("Range of edges/node as % of max. edges/node")
       # plt.title("Range of edges/node vs. number of partitions\n for various graphs")
    else:
        plt.ylabel("Ratio of local to remote edges")
    plt.xticks(np.arange(1, 20, 2))
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
    plotDiffsVsPartitions(1, 21)

main()