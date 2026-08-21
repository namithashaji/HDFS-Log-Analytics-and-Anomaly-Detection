# HDFS Log Analytics and Anomaly Detection

## Project Description
This project aims to detect anomalies in HDFS application logs using Deep Learning (LSTM). The system will analyze log sequences, identify abnormal patterns, and predict potential system failures. The system also includes a real-time monitoring dashboard for displaying detected anomalies and resolving active alerts.


## Dataset
LogHub HDFS_v1
https://github.com/logpai/loghub/tree/master/HDFS

## Technologies
- Python
- TensorFlow / Keras
- Pandas
- NumPy
- LSTM
- React
- FastAPI

## Sample Output

============================================================
ANOMALY DETECTED
============================================================
Time:        260821 202102
Block ID:    blk_-3102267849859399193
Component:   dfs.DataNode$PacketResponder
Probability: 1.0000
Sequence:    6 events
Message:     PacketResponder blk_-3102267849859399193 2 Exception java.io.EOFException
============================================================


