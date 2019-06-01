import multiprocessing as mp

nodes = {}
# print("Number of processors: ", mp.cpu_count())

def readLAWSfile(filename):
    with open(filename) as lawsGraph:
        for line in lawsGraph:
            line = line.rstrip()
            node = line.split()
            nodes[int(node[0])] = len(node[1:])
            # print(line)

def testPartitioning(numWorkers):
    # Use round robin partitioning by hashing the vertices to see how many edges each worker would get
    workers = [0] * numWorkers
    for key in nodes.keys():
        workers[key%numWorkers] += nodes[key]
    print(workers)

readLAWSfile("laws_small.graph-txt")
testPartitioning(4)

# print(nodes)