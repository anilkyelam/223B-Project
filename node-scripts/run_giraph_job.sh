SRC_DIR_FULL_PATH=$1
RESULTS_DIR_FULL_PATH=$2
GIRAPH_CLASS_NAME=$3
INPUT_GRAPH_NAME=$4

# Run giraph job
source ~/.profile
# giraph /home/ubuntu/giraph/giraph-examples/target/giraph-examples-1.3.0-SNAPSHOT-for-hadoop-2.5.1-jar-with-dependencies.jar \
#         org.apache.giraph.examples.SimplePageRankComputation -vif org.apache.giraph.io.formats.LongDoubleFloatTextInputFormat -vof org.apache.giraph.io.formats.IdWithValueTextOutputFormat \
#         -vip /user/ubuntu/graph_inputs/${INPUT_GRAPH_NAME}  -op /user/ubuntu/graph_outputs/${INPUT_GRAPH_NAME} -w 3 2>&1


giraph giraph-examples-1.3.0-SNAPSHOT-for-hadoop-2.5.1-jar-with-dependencies.jar org.apache.giraph.examples.SimplePageRankComputation -vif org.apache.giraph.io.formats.LongDoubleFloatTextInputFormat -vof org.apache.giraph.io.formats.IdWithValueTextOutputFormat -vip /user/ubuntu/graph_inputs/darwini-50m-edges  -op /user/ubuntu/graph_outputs/darwini-50m-edges -w 3 > ${RESULTS_DIR_FULL_PATH}/giraph.log 2>&1


# giraph /home/ubuntu/giraph/giraph-examples/target/giraph-examples-1.3.0-SNAPSHOT-for-hadoop-2.5.1-jar-with-dependencies.jar org.apache.giraph.examples.SimplePageRankComputation -vif org.apache.giraph.io.formats.LongDoubleFloatTextInputFormat -vof org.apache.giraph.io.formats.IdWithValueTextOutputFormat -vip /user/ubuntu/graph_inputs/darwini-50m-edges  -op /user/ubuntu/giraph_outputs/darwini-50m-edges -w 3