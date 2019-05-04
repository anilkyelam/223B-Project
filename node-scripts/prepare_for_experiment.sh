source ~/.profile

echo "Deleting any previous outputs saved on hdfs"
hdfs dfs -rm -r -skipTrash /user/ubuntu/graph_outputs/*

# Kill any leftover processes from a previous operation
pkill sar
# pkill python3

