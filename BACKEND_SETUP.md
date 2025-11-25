# Backend Setup Guide: Hadoop/Spark Cluster Integration

## Overview
This UI connects to your real Hadoop/Spark cluster via REST API. The application can load log files from HDFS, submit Spark jobs, and query HBase tables.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit UI (This Application)                            │
│  - File Upload & Analysis                                   │
│  - Interactive Visualizations                               │
│  - Filter & Export Data                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API Calls
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Hadoop/Spark Cluster (Your Infrastructure)                │
│  ┌──────────┐  ┌───────┐  ┌─────────┐  ┌─────────┐         │
│  │  HDFS    │  │ Spark │  │ HBase   │  │  Jobs   │         │
│  │ (Storage)│  │(Engine)│  │ (NoSQL) │  │(Runners)│         │
│  └──────────┘  └───────┘  └─────────┘  └─────────┘         │
└─────────────────────────────────────────────────────────────┘
```
This dashboard can run in two modes:

1. **Local mode** – logs are uploaded from the user’s machine.
2. **Cluster mode** – logs are stored in **HDFS**, processed with **Spark**, and results are sent back to the UI via a small REST API.

In cluster mode, the architecture is:

- **HDFS** → stores raw server log files  
- **Spark** → parses logs and calculates aggregates (traffic, errors, peaks)  
- **Flask API (`api_server.py`)** → provides simple HTTP endpoints for the UI  
- **Streamlit UI (`app.py`)** → calls the API and visualizes the metrics  

---

## 1. Minimal Cluster Requirements

- 1 master node + 2 worker nodes (Linux – Ubuntu/CentOS)
- Java 8+ installed on all nodes
- Passwordless SSH between master and workers
- Hadoop and Spark installed in `/opt/hadoop` and `/opt/spark` (or similar paths)


```bash
# On the Hadoop/Spark master node

# Start HDFS (NameNode + DataNodes)
$HADOOP_HOME/sbin/start-dfs.sh

# Start YARN (ResourceManager + NodeManagers)
$HADOOP_HOME/sbin/start-yarn.sh

# Start Spark master and workers
$SPARK_HOME/sbin/start-master.sh
$SPARK_HOME/sbin/start-slaves.sh spark://master-node:7077

## Support

For more information:
- Hadoop: https://hadoop.apache.org/docs/
- Spark: https://spark.apache.org/docs/latest/
- HBase: https://hbase.apache.org/
- Kafka: https://kafka.apache.org/documentation/
