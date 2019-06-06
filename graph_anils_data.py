import matplotlib.pyplot as plt


graph_names = {}

def readFile():
    with open("anils_data.txt") as f:
        for line in f:
            line = line.lstrip().rstrip()
            # plot_style = "mod_cv"
            if "=========" in line:
                current_graph = line.split(" ")[1]
                graph_names[current_graph] = {}
                print(current_graph)
                continue
            if "=== PartitionStyle:" in line:
                # Strip the == and spaces
                fields = line.replace("=", "").replace(" ", "").split(",")
                partition_style = fields[0].split(":")[1]
                columns = fields[1:]
                
                if partition_style == "modulo" and len(columns) == 3:
                    plot_style = "mod_cv"
                elif partition_style == "modulo" and len(columns) == 2:
                    plot_style = "mod_lvr"
                elif partition_style == "range" and len(columns) == 3:
                    plot_style = "range_cv"
                elif partition_style == "range" and len(columns) == 2:
                    plot_style = "range_lvr"
                else:
                    print("ERROR: Unknown plot style")
                    exit()

                graph_names[current_graph][plot_style] = {}
                for c in columns:
                    graph_names[current_graph][plot_style][c] = []
                continue
            if "Total Vertices" in line:
                continue

            # If we've reached this point, the line contains data. columns tells us what the column headers are
            col_idxs_cv = ["NumPartitions", "CV", "NormalizedEdgeRange"]
            col_idxs_lvr = ["NumPartitions", "Inter-PartitionEdgeRatio"]

            line = line.lstrip().replace("  ", " ").split(" ")
            for i, num in enumerate(line):
                if num == '':
                    continue
                num = float(num)
                if len(line) == 3:
                    graph_names[current_graph][plot_style][col_idxs_cv[i]].append(num)
                else:
                    graph_names[current_graph][plot_style][col_idxs_lvr[i]].append(num)
            
def graph_stuff():
    plot_styles = ["mod_cv", "mod_lvr", "range_cv", "range_lvr"]
    titles = {"mod_cv":"Variation in Number of Edges per Node (modulo partitioning)",
            "mod_lvr":"Ratio of Remote Edges to All Edges",
            }
    xvals = [2,4,6,8,10,12,14,16,18,20]
    for style in plot_styles:
        if "cv" in style:
            ycol = "CV"
            ylabel = "Coefficient of Variation"
        elif "lvr" in style:
            ycol = "Inter-PartitionEdgeRatio"
            ylabel = "Ratio of Remote Edges to All Edges"
        for graph in graph_names.keys():
            yvals = graph_names[graph][style][ycol]
            plt.plot(xvals, yvals, label=graph)
        # plt.title(title)
        plt.legend()
        plt.xticks(xvals)
        plt.xlabel("Number of Partitions")
        plt.ylabel(ylabel)
        plt.show()

readFile()
graph_stuff()