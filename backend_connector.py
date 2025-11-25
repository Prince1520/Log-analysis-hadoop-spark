import requests
import pandas as pd
from typing import Dict, Optional, List
import json

class HadoopSparkConnector:
    """Connector for communicating with Hadoop/Spark cluster backend."""
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize connector to Hadoop/Spark cluster.
        
        Args:
            base_url: Base URL of the Hadoop/Spark REST API (e.g., http://master-node:8080)
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        
        if username and password:
            self.session.auth = (username, password)
    
    def test_connection(self) -> Dict:
        """Test connection to Hadoop/Spark cluster."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return {"status": "connected", "message": "Successfully connected to cluster"}
            else:
                return {"status": "error", "message": f"Cluster returned status {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {str(e)}"}
    
    def submit_spark_job(self, job_name: str, class_path: str, jar_path: str, 
                        args: Optional[List[str]] = None) -> Dict:
        """
        Submit a Spark job to the cluster.
        
        Args:
            job_name: Name of the job
            class_path: Main class path
            jar_path: Path to JAR file in HDFS
            args: Optional arguments to pass to the job
        
        Returns:
            Response with job ID and status
        """
        payload = {
            "job_name": job_name,
            "class": class_path,
            "jar": jar_path,
            "args": args or []
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/spark/submit",
                json=payload,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_hdfs_files(self, path: str) -> Dict:
        """
        List files in HDFS directory.
        
        Args:
            path: HDFS path
        
        Returns:
            List of files in the directory
        """
        try:
            response = self.session.get(
                f"{self.base_url}/hdfs/files",
                params={"path": path},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def read_hdfs_file(self, path: str) -> Optional[str]:
        """
        Read file content from HDFS.
        
        Args:
            path: HDFS file path
        
        Returns:
            File content as string
        """
        try:
            response = self.session.get(
                f"{self.base_url}/hdfs/read",
                params={"path": path},
                timeout=30
            )
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            print(f"Error reading HDFS file: {str(e)}")
            return None
    
    def upload_to_hdfs(self, local_path: str, hdfs_path: str) -> Dict:
        """
        Upload file to HDFS.
        
        Args:
            local_path: Local file path
            hdfs_path: Target HDFS path
        
        Returns:
            Upload status
        """
        try:
            with open(local_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(
                    f"{self.base_url}/hdfs/upload",
                    files=files,
                    data={"path": hdfs_path},
                    timeout=60
                )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def query_hbase(self, table: str, row_key: str, column: Optional[str] = None) -> Dict:
        """
        Query data from HBase table.
        
        Args:
            table: HBase table name
            row_key: Row key to query
            column: Optional specific column
        
        Returns:
            Query results
        """
        try:
            params = {"table": table, "key": row_key}
            if column:
                params["column"] = column
            
            response = self.session.get(
                f"{self.base_url}/hbase/query",
                params=params,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def scan_hbase_table(self, table: str, filter_expr: Optional[str] = None) -> List[Dict]:
        """
        Scan HBase table and return results as list of dictionaries.
        
        Args:
            table: HBase table name
            filter_expr: Optional filter expression
        
        Returns:
            List of rows from HBase table
        """
        try:
            params = {"table": table}
            if filter_expr:
                params["filter"] = filter_expr
            
            response = self.session.get(
                f"{self.base_url}/hbase/scan",
                params=params,
                timeout=60
            )
            data = response.json()
            return data.get("rows", []) if isinstance(data, dict) else data
        except Exception as e:
            print(f"Error scanning HBase: {str(e)}")
            return []
    
    def get_cluster_status(self) -> Dict:
        """Get current cluster status and metrics."""
        try:
            response = self.session.get(
                f"{self.base_url}/status",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get status of a specific job."""
        try:
            response = self.session.get(
                f"{self.base_url}/jobs/{job_id}",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_jobs(self) -> Dict:
        """List all jobs on the cluster."""
        try:
            response = self.session.get(
                f"{self.base_url}/jobs",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
