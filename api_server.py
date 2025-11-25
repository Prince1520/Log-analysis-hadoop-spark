"""
REST API Server for Hadoop/Spark Cluster
=========================================
Deploy this file on your MASTER NODE to enable communication
between the Streamlit dashboard and your Hadoop/Spark cluster.

Installation:
    pip install flask hdfs pyspark

Usage:
    python api_server.py

The API will run on port 8080 by default.
"""

from flask import Flask, request, jsonify
import os
import subprocess
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HADOOP_HOME = os.environ.get('HADOOP_HOME', '/opt/hadoop')
SPARK_HOME = os.environ.get('SPARK_HOME', '/opt/spark')
HDFS_NAMENODE = os.environ.get('HDFS_NAMENODE', 'localhost:9870')

try:
    from hdfs import InsecureClient
    hdfs_client = InsecureClient(f'http://{HDFS_NAMENODE}')
    HDFS_AVAILABLE = True
except ImportError:
    hdfs_client = None
    HDFS_AVAILABLE = False
    logger.warning("HDFS client not available. Install with: pip install hdfs")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify cluster connectivity."""
    status = {
        'status': 'connected',
        'message': 'Hadoop/Spark cluster is running',
        'hadoop_home': HADOOP_HOME,
        'spark_home': SPARK_HOME,
        'hdfs_available': HDFS_AVAILABLE
    }
    
    try:
        result = subprocess.run(
            [f'{HADOOP_HOME}/bin/hdfs', 'dfsadmin', '-report'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            status['hdfs_status'] = 'running'
        else:
            status['hdfs_status'] = 'error'
    except Exception as e:
        status['hdfs_status'] = f'unknown: {str(e)}'
    
    return jsonify(status)


@app.route('/cluster/info', methods=['GET'])
def cluster_info():
    """Get cluster information and node status."""
    info = {
        'cluster_name': 'Log Analysis Cluster',
        'nodes': [],
        'hdfs_available': HDFS_AVAILABLE
    }
    
    try:
        result = subprocess.run(
            [f'{HADOOP_HOME}/bin/hdfs', 'dfsadmin', '-report'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Live datanodes' in line:
                    info['live_nodes'] = line
                elif 'Name:' in line:
                    info['nodes'].append(line.strip())
    except Exception as e:
        info['error'] = str(e)
    
    return jsonify(info)


@app.route('/hdfs/list', methods=['GET'])
def list_hdfs_directory():
    """List files in HDFS directory."""
    path = request.args.get('path', '/')
    
    if not HDFS_AVAILABLE:
        return jsonify({'error': 'HDFS client not available'}), 500
    
    try:
        files = hdfs_client.list(path, status=True)
        file_list = []
        for name, status in files:
            file_list.append({
                'name': name,
                'path': f"{path.rstrip('/')}/{name}",
                'type': 'directory' if status['type'] == 'DIRECTORY' else 'file',
                'size': status.get('length', 0),
                'modified': status.get('modificationTime', 0)
            })
        return jsonify({'path': path, 'files': file_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/hdfs/read', methods=['GET'])
def read_hdfs_file():
    """Read a file from HDFS."""
    path = request.args.get('path')
    
    if not path:
        return jsonify({'error': 'Path parameter is required'}), 400
    
    if not HDFS_AVAILABLE:
        return jsonify({'error': 'HDFS client not available'}), 500
    
    try:
        with hdfs_client.read(path, encoding='utf-8') as reader:
            content = reader.read()
        return jsonify({
            'path': path,
            'content': content,
            'size': len(content)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/hdfs/upload', methods=['POST'])
def upload_to_hdfs():
    """Upload content to HDFS."""
    data = request.get_json()
    
    if not data or 'path' not in data or 'content' not in data:
        return jsonify({'error': 'Path and content are required'}), 400
    
    if not HDFS_AVAILABLE:
        return jsonify({'error': 'HDFS client not available'}), 500
    
    try:
        path = data['path']
        content = data['content']
        overwrite = data.get('overwrite', False)
        
        with hdfs_client.write(path, overwrite=overwrite, encoding='utf-8') as writer:
            writer.write(content)
        
        return jsonify({
            'status': 'success',
            'message': f'File uploaded to {path}',
            'size': len(content)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/spark/submit', methods=['POST'])
def submit_spark_job():
    """Submit a Spark job for processing."""
    data = request.get_json()
    
    if not data or 'job_file' not in data:
        return jsonify({'error': 'job_file is required'}), 400
    
    try:
        job_file = data['job_file']
        args = data.get('args', [])
        
        cmd = [
            f'{SPARK_HOME}/bin/spark-submit',
            '--master', 'spark://localhost:7077',
            job_file
        ] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return jsonify({
            'status': 'completed' if result.returncode == 0 else 'failed',
            'returncode': result.returncode,
            'stdout': result.stdout[:5000],
            'stderr': result.stderr[:2000]
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Job timed out after 5 minutes'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/spark/analyze', methods=['POST'])
def analyze_logs_with_spark():
    """Analyze log files using Spark."""
    data = request.get_json()
    
    if not data or 'hdfs_path' not in data:
        return jsonify({'error': 'hdfs_path is required'}), 400
    
    try:
        from pyspark.sql import SparkSession
        
        spark = SparkSession.builder \
            .appName("LogAnalysis") \
            .master("spark://localhost:7077") \
            .getOrCreate()
        
        hdfs_path = data['hdfs_path']
        df = spark.read.text(f"hdfs://localhost:9000{hdfs_path}")
        
        total_lines = df.count()
        
        result = {
            'status': 'success',
            'hdfs_path': hdfs_path,
            'total_lines': total_lines,
            'sample_lines': [row.value for row in df.take(10)]
        }
        
        spark.stop()
        return jsonify(result)
        
    except ImportError:
        return jsonify({'error': 'PySpark not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logs/parse', methods=['POST'])
def parse_logs():
    """Parse log content and return structured data."""
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'content is required'}), 400
    
    try:
        import re
        
        content = data['content']
        lines = content.strip().split('\n')
        
        apache_pattern = r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+|-)'
        
        parsed_logs = []
        for line in lines[:1000]:
            match = re.match(apache_pattern, line)
            if match:
                ip, timestamp, method, path, protocol, status, size = match.groups()
                parsed_logs.append({
                    'ip': ip,
                    'timestamp': timestamp,
                    'method': method,
                    'path': path,
                    'status_code': int(status),
                    'size': int(size) if size != '-' else 0
                })
        
        return jsonify({
            'status': 'success',
            'total_lines': len(lines),
            'parsed_count': len(parsed_logs),
            'logs': parsed_logs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("""
    ========================================
    Hadoop/Spark Cluster REST API Server
    ========================================
    
    Endpoints:
    - GET  /health           - Health check
    - GET  /cluster/info     - Cluster information
    - GET  /hdfs/list        - List HDFS directory
    - GET  /hdfs/read        - Read file from HDFS
    - POST /hdfs/upload      - Upload to HDFS
    - POST /spark/submit     - Submit Spark job
    - POST /spark/analyze    - Analyze logs with Spark
    - POST /logs/parse       - Parse log content
    
    Starting server on port 8080...
    ========================================
    """)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
