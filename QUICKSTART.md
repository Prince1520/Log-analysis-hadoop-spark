# Quick Start Guide

## 30-Second Setup (Local Testing)

```bash
# 1. Start the app
streamlit run app.py

# 2. Open browser to http://localhost:5000

# 3. Upload sample_logs.log from sidebar

# 4. Explore the dashboard!
```

## Key Features Overview

### 📈 Traffic Patterns Tab
- Time-series graph of requests over time
- Peak traffic hours identified
- Hourly distribution breakdown

### ⚠️ Error Analysis Tab
- Error frequency by type
- Status code distribution (pie chart)
- Error trends over time

### 📊 Statistics Tab
- HTTP methods breakdown
- Top requested paths
- Most active IP addresses

### 📋 Raw Data Tab
- Search through all log entries
- Sort by any column
- Download filtered data as CSV

## Connecting to Hadoop/Spark

### Step 1: Switch Data Source
In sidebar, select "Hadoop/Spark Cluster" instead of "Local File Upload"

### Step 2: Enter Cluster Details
```
Cluster URL: http://your-master-node-ip:8080
Username: (optional)
Password: (optional)
```

### Step 3: Connect
Click "Connect to Cluster" button

### Step 4: Load Data
Enter HDFS path (e.g., `/user/logs/my-logs.log`) and click "Load from HDFS"

## Supported Log Formats

✅ **Apache Combined Log**
```
192.168.1.100 - - [23/Nov/2025:08:15:23 +0000] "GET /index.html HTTP/1.1" 200 1234
```

✅ **Nginx Log**
```
192.168.1.100 - - [23/Nov/2025:08:15:23 +0000] "GET /index.html HTTP/1.1" 200 1234
```

✅ **Generic Error Log**
```
[23/Nov/2025:08:15:23] [ERROR] Something went wrong
```

✅ **Any timestamp-based format**

## Common Tasks

### 1. Analyze a Specific Date Range
1. Upload or load data
2. Use "Date Range" filter in sidebar
3. Select start and end dates
4. Dashboard updates automatically

### 2. Find Errors Only
1. In "Error Levels" filter, uncheck non-error types
2. In "Status Codes" filter, select 4xx and 5xx codes
3. View filtered error analysis

### 3. Export Results
1. Filter data as needed
2. Go to "Raw Data" tab
3. Click "📥 Download Filtered Data (CSV)"
4. Opens in Excel/spreadsheet

### 4. Monitor Top IPs
1. Scroll to "Statistics" tab
2. See "Top IP Addresses" bar chart
3. Identify suspicious or heavy traffic sources

### 5. Identify Peak Hours
1. Go to "Traffic Patterns" tab
2. Check "Peak Traffic Times" table
3. Review hourly distribution graph

## Sample Workflow

```
1. Start app: streamlit run app.py
2. Upload: sample_logs.log
3. Observe: Auto-generated visualizations
4. Filter: Select date range or error types
5. Analyze: Review statistics and trends
6. Export: Download filtered CSV for reporting
7. Scale: Connect to Hadoop/Spark cluster when ready
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Refresh | R or F5 |
| Search data | Ctrl+F (in Raw Data tab) |
| Download CSV | Click button in Raw Data |

## Useful Commands (Cluster Setup)

```bash
# Check Hadoop status
jps

# View HDFS files
hdfs dfs -ls /user/logs/

# Upload log file to HDFS
hdfs dfs -put local-file.log /user/logs/

# Check Spark master status
curl http://master-node:8080/api/v1/applications

# Monitor jobs
$SPARK_HOME/bin/spark-shell --master spark://master-node:7077
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not parse log file" | Check log format, use standard Apache/Nginx format |
| "Connection failed to cluster" | Verify cluster URL, check firewall, ensure REST API is running |
| "HDFS file not found" | Check path with `hdfs dfs -ls /path/`, ensure file exists |
| "App won't start" | Run `pip install -r requirements.txt`, then restart |
| "Visualizations not showing" | Try refreshing browser, check console for errors |

## File References

- **app.py** - Main application
- **log_parser.py** - Log parsing engine
- **backend_connector.py** - Cluster API client
- **sample_logs.log** - Test data
- **BACKEND_SETUP.md** - Cluster installation guide
- **README.md** - Full project documentation
- **GITHUB_SETUP.md** - GitHub submission guide

## Next Steps

1. **Test Locally** → Run with sample_logs.log
2. **Understand Logs** → Explore the dashboard with sample data
3. **Set Up Cluster** → Follow BACKEND_SETUP.md when ready
4. **Scale to Production** → Connect to your Hadoop/Spark cluster
5. **Submit** → Push to GitHub following GITHUB_SETUP.md

## Command Cheat Sheet

```bash
# Start app
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Update packages
uv add [package_name]

# Check cluster status
curl http://cluster-url:8080/health

# Upload to HDFS
hdfs dfs -put file.log /user/logs/

# List HDFS directory
hdfs dfs -ls /user/logs/

# View Hadoop config
hdfs dfs -put file.log /user/logs/
```

## Need Help?

1. Check **README.md** for detailed documentation
2. Read **BACKEND_SETUP.md** for cluster configuration
3. Review **GITHUB_SETUP.md** for submission details
4. See troubleshooting sections in each guide

---

**That's it! You're ready to analyze logs.** 🚀

Start with `streamlit run app.py` and explore the dashboard!
