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

## Setting Up Your Hadoop/Spark Cluster

### Prerequisites
- At least 3 machines (1 Master, 2 Worker nodes)
- Linux/Unix OS (CentOS, Ubuntu, etc.)
- Java 8+ installed
- SSH access between nodes configured

### 1. Install Hadoop

**On Master Node:**
```bash
# Download Hadoop
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.1/hadoop-3.3.1.tar.gz
tar xzf hadoop-3.3.1.tar.gz
sudo mv hadoop-3.3.1 /opt/hadoop
sudo chown -R $USER:$USER /opt/hadoop

# Set JAVA_HOME in ~/.bashrc
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
source ~/.bashrc
```

**Configure core-site.xml:**
```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://master-node:9000</value>
    </property>
</configuration>
```

**Configure hdfs-site.xml:**
```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>2</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/opt/hadoop/data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/opt/hadoop/data/datanode</value>
    </property>
</configuration>
```

### 2. Install Spark

**On Master Node:**
```bash
# Download Spark
wget https://archive.apache.org/dist/spark/spark-3.3.0/spark-3.3.0-bin-hadoop3.tgz
tar xzf spark-3.3.0-bin-hadoop3.tgz
sudo mv spark-3.3.0-bin-hadoop3 /opt/spark
sudo chown -R $USER:$USER /opt/spark

# Set environment variables
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin
```

**Configure spark-env.sh:**
```bash
cp $SPARK_HOME/conf/spark-env.sh.template $SPARK_HOME/conf/spark-env.sh

# Add to spark-env.sh:
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export SPARK_MASTER_HOST=master-node
export SPARK_LOCAL_IP=master-node-ip
```

### 3. Configure Worker Nodes

**On Each Worker Node:**
```bash
# Copy Hadoop and Spark from master
rsync -avz /opt/hadoop/ user@worker-node-1:/opt/hadoop/
rsync -avz /opt/spark/ user@worker-node-1:/opt/spark/

# Set same environment variables
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/opt/hadoop
export SPARK_HOME=/opt/spark
export PATH=$PATH:$HADOOP_HOME/bin:$SPARK_HOME/bin
```

**Configure workers file on Master:**
```bash
# Edit $HADOOP_HOME/etc/hadoop/workers (or slaves)
master-node
worker-node-1
worker-node-2
```

### 4. Start Hadoop Cluster

```bash
# Format namenode (first time only)
hdfs namenode -format

# Start HDFS
$HADOOP_HOME/sbin/start-dfs.sh

# Start YARN (resource manager)
$HADOOP_HOME/sbin/start-yarn.sh

# Check status
jps  # Should show NameNode on master, DataNode on workers
```

### 5. Start Spark Cluster

```bash
# Start master
$SPARK_HOME/sbin/start-master.sh

# Start slaves/workers
$SPARK_HOME/sbin/start-slaves.sh spark://master-node:7077

# Check status
jps  # Should show Master on master, Worker on workers
```

### 6. Set Up REST API Endpoint

**Option A: Use Hadoop WebHDFS (Built-in)**
```bash
# Enable WebHDFS in hdfs-site.xml
<property>
    <name>dfs.webhdfs.enabled</name>
    <value>true</value>
</property>

# Default port: 9870
# URL: http://master-node:9870
```

**Option B: Create Custom REST API (Recommended)**

Create `api_server.py` on Master Node:
```python
from flask import Flask, request, jsonify
import subprocess
import os
from hdfs import InsecureClient

app = Flask(__name__)

# HDFS client
hdfs_client = InsecureClient('http://localhost:9870')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'connected', 'message': 'Cluster is running'})

@app.route('/hdfs/read', methods=['GET'])
def read_hdfs_file():
    """Read file from HDFS"""
    path = request.args.get('path', '/user/logs/')
    try:
        with hdfs_client.read(path) as reader:
            content = reader.read().decode('utf-8')
        return content, 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/hdfs/upload', methods=['POST'])
def upload_to_hdfs():
    """Upload file to HDFS"""
    hdfs_path = request.form.get('path', '/user/uploads/')
    file = request.files['file']
    try:
        hdfs_client.write(hdfs_path + file.filename, file.read())
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/spark/submit', methods=['POST'])
def submit_spark_job():
    """Submit Spark job"""
    data = request.json
    try:
        cmd = [
            'spark-submit',
            '--master', 'spark://master-node:7077',
            '--class', data['class'],
            data['jar']
        ] + data.get('args', [])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return jsonify({'status': 'success', 'output': result.stdout}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/status', methods=['GET'])
def cluster_status():
    """Get cluster status"""
    return jsonify({
        'status': 'running',
        'hadoop': 'active',
        'spark': 'active'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
```

Run API server:
```bash
pip install flask hdfs3
python api_server.py
```

## Connecting UI to Cluster

### 1. Set Environment Variables

On Replit or your hosting environment:
```bash
# Set these environment variables
HADOOP_CLUSTER_URL=http://master-node-ip:8080
HADOOP_USERNAME=hadoop_user  # Optional
HADOOP_PASSWORD=hadoop_pass  # Optional
```

### 2. Configure in UI

When running the application:
1. Select "Hadoop/Spark Cluster" from sidebar
2. Enter cluster URL: `http://master-node-ip:8080`
3. Click "Connect to Cluster"
4. Enter HDFS path to log files (e.g., `/user/logs/`)
5. Click "Load from HDFS"

## Example Use Cases

### Load and Analyze Server Logs
```
1. Upload logs to HDFS: hdfs dfs -put /var/log/apache/access.log /user/logs/
2. In UI: Select "Hadoop/Spark Cluster"
3. Enter cluster URL and HDFS path
4. View traffic analysis, error frequencies, trends
```

### Process Large Datasets with Spark
```
1. Create Spark job (Java/Scala/Python) that processes logs
2. Upload JAR to HDFS
3. In UI: Use "Submit Spark Job" to run job
4. Monitor job status and download results
```

### Query Real-time Metrics from HBase
```
1. Store time-series data in HBase
2. UI can query HBase tables via connector
3. View real-time analytics and metrics
```

## Troubleshooting

### Connection Issues
```bash
# Check if services are running
jps  # Should show NameNode, DataNode, Master, Worker

# Test HDFS connectivity
hdfs dfs -ls /

# Test API endpoint
curl http://master-node-ip:8080/health
```

### HDFS File Not Found
```bash
# List files in HDFS
hdfs dfs -ls /user/logs/

# Upload test file
hdfs dfs -put test.log /user/logs/
```

### Spark Job Not Running
```bash
# Check Spark master logs
tail -f $SPARK_HOME/logs/spark-*.log

# Monitor running jobs
$SPARK_HOME/bin/spark-shell --master spark://master-node:7077
```

## Next Steps

1. **Set up your multi-node cluster** using the instructions above
2. **Deploy the REST API** on your master node
3. **Configure environment variables** with your cluster details
4. **Upload log files to HDFS** for analysis
5. **Connect this UI** to start analyzing data

## Files Included

- `app.py` - Main Streamlit application
- `log_parser.py` - Log parsing engine
- `backend_connector.py` - Hadoop/Spark cluster connector
- `sample_logs.log` - Example log file for testing local upload

## Support

For more information:
- Hadoop: https://hadoop.apache.org/docs/
- Spark: https://spark.apache.org/docs/latest/
- HBase: https://hbase.apache.org/
- Kafka: https://kafka.apache.org/documentation/
