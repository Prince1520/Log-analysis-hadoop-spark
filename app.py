import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time
from log_parser import LogParser
from backend_connector import HadoopSparkConnector

st.set_page_config(
    page_title="Log File Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .corporate-header {
        background: #ffffff;
        padding: 40px 0;
        margin-bottom: 30px;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .header-content {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .brand-title {
        font-size: 32px;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    
    .brand-subtitle {
        font-size: 16px;
        color: #718096;
        font-weight: 400;
        line-height: 1.5;
    }
    
    .quick-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 30px 0;
    }
    
    .stat-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .stat-card:hover {
        border-color: #cbd5e0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    .stat-icon {
        width: 48px;
        height: 48px;
        background: #f7fafc;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 16px;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 4px;
    }
    
    .stat-label {
        font-size: 14px;
        color: #718096;
        font-weight: 500;
    }
    
    .info-banner {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 20px 0;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .info-icon {
        font-size: 24px;
        flex-shrink: 0;
    }
    
    .info-text {
        font-size: 14px;
        color: #4a5568;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="corporate-header">
    <div class="header-content">
        <h1 class="brand-title">📊 Log File Analysis Dashboard</h1>
        <p class="brand-subtitle">
            Analyze server logs with real-time monitoring and enterprise-grade data processing
        </p>
    </div>
</div>

<div class="info-banner">
    <div class="info-icon">ℹ️</div>
    <div class="info-text">
        <strong>Getting Started:</strong> Upload your log files from the sidebar or connect to your Hadoop/Spark cluster for distributed processing.
    </div>
</div>
""", unsafe_allow_html=True)

parser = LogParser()

if 'df' not in st.session_state:
    st.session_state.df = None

if 'connector' not in st.session_state:
    st.session_state.connector = None

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

if 'last_error_count' not in st.session_state:
    st.session_state.last_error_count = 0

if 'new_errors' not in st.session_state:
    st.session_state.new_errors = []

if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = None

if 'seen_error_ids' not in st.session_state:
    st.session_state.seen_error_ids = set()

if 'ai_insights' not in st.session_state:
    st.session_state.ai_insights = None

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'chat_widget_open' not in st.session_state:
    st.session_state.chat_widget_open = False

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

with st.sidebar:
    st.header("⚙️ Settings")
    
    st.session_state.auto_refresh = st.checkbox(
        "🔄 Auto-Refresh (5 seconds)",
        value=st.session_state.auto_refresh,
        help="Automatically refresh data every 5 seconds"
    )
    
    if st.session_state.auto_refresh:
        st.info("⏱️ Auto-refresh is ON")
    
    st.markdown("---")
    st.header("Data Source")
    
    data_source = st.radio(
        "Choose data source:",
        options=["Local File Upload", "Hadoop/Spark Cluster"],
        help="Upload local files or connect to your Hadoop/Spark cluster"
    )
    
    if data_source == "Local File Upload":
        uploaded_file = st.file_uploader(
            "Choose a log file",
            type=['log', 'txt'],
            help="Supports Apache, Nginx, and generic log formats"
        )
        
        if uploaded_file is not None:
            with st.spinner("Parsing log file..."):
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                df = parser.parse_file(content)
                
                if not df.empty:
                    st.session_state.df = df
                    st.success(f"✅ Parsed {len(df)} log entries")
                else:
                    st.error("❌ Could not parse log file. Please check the format.")
    
    else:  # Hadoop/Spark Cluster
        st.subheader("Cluster Configuration")
        
        cluster_url = st.text_input(
            "Cluster URL",
            value=os.getenv('HADOOP_CLUSTER_URL', 'http://localhost:8080'),
            help="Base URL of your Hadoop/Spark REST API (e.g., http://master-node:8080)"
        )
        
        cluster_username = st.text_input(
            "Username (optional)",
            value=os.getenv('HADOOP_USERNAME', ''),
            type="password"
        )
        
        cluster_password = st.text_input(
            "Password (optional)",
            value=os.getenv('HADOOP_PASSWORD', ''),
            type="password"
        )
        
        if st.button("Connect to Cluster"):
            with st.spinner("Connecting to cluster..."):
                connector = HadoopSparkConnector(
                    cluster_url,
                    username=cluster_username if cluster_username else None,
                    password=cluster_password if cluster_password else None
                )
                
                status = connector.test_connection()
                st.session_state.connector = connector
                
                if status['status'] == 'connected':
                    st.success(f"✅ {status['message']}")
                else:
                    st.error(f"❌ {status['message']}")
        
        if st.session_state.connector:
            st.markdown("---")
            st.subheader("Load Data from HDFS")
            
            hdfs_path = st.text_input(
                "HDFS Path",
                value="/user/logs/",
                help="Path to log files in HDFS"
            )
            
            if st.button("Load from HDFS"):
                with st.spinner("Loading data from HDFS..."):
                    connector = st.session_state.connector
                    
                    try:
                        content = connector.read_hdfs_file(hdfs_path)
                        if content:
                            df = parser.parse_file(content)
                            if not df.empty:
                                st.session_state.df = df
                                st.success(f"✅ Loaded {len(df)} log entries from HDFS")
                            else:
                                st.error("❌ Could not parse HDFS file.")
                        else:
                            st.error("❌ Could not read file from HDFS. Check the path.")
                    except Exception as e:
                        st.error(f"❌ Error loading from HDFS: {str(e)}")
    
    if st.session_state.df is not None and not st.session_state.df.empty:
        st.markdown("---")
        st.header("Filters")
        
        df = st.session_state.df
        
        if 'timestamp' in df.columns and not df['timestamp'].isna().all():
            min_date = df['timestamp'].min().date()
            max_date = df['timestamp'].max().date()
            
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
                df = df[mask]
        
        if 'error_level' in df.columns:
            error_levels = df['error_level'].unique().tolist()
            selected_levels = st.multiselect(
                "Error Levels",
                options=error_levels,
                default=error_levels
            )
            df = df[df['error_level'].isin(selected_levels)]
        
        if 'status_code' in df.columns:
            status_codes = sorted(df['status_code'].unique().tolist())
            selected_status = st.multiselect(
                "Status Codes",
                options=status_codes,
                default=status_codes
            )
            df = df[df['status_code'].isin(selected_status)]
        
        st.session_state.filtered_df = df
    else:
        st.info("👆 Upload a log file to begin analysis")

if st.session_state.df is not None and not st.session_state.df.empty:
    df = st.session_state.get('filtered_df', st.session_state.df)
    
    if 'error_level' in df.columns and 'timestamp' in df.columns:
        error_rows = df[df['error_level'].isin(['ERROR', 'SERVER_ERROR', 'CLIENT_ERROR'])]
        
        if st.session_state.last_refresh_time is not None:
            new_error_rows = error_rows[error_rows['timestamp'] > st.session_state.last_refresh_time]
            st.session_state.new_errors = new_error_rows.index.tolist()
        else:
            st.session_state.new_errors = []
        
        st.session_state.last_refresh_time = df['timestamp'].max() if not df['timestamp'].isna().all() else None
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", f"{len(df):,}")
    
    with col2:
        if 'error_level' in df.columns:
            error_count = df[df['error_level'].isin(['ERROR', 'SERVER_ERROR', 'CLIENT_ERROR'])].shape[0]
            error_rate = (error_count / len(df) * 100) if len(df) > 0 else 0
            
            new_errors = error_count - st.session_state.last_error_count
            delta_text = f"+{new_errors}" if new_errors > 0 else None
            st.metric("Error Count", f"{error_count:,}", delta_text, delta_color="inverse")
            st.session_state.last_error_count = error_count
        else:
            st.metric("Error Count", "N/A")
    
    with col3:
        if 'timestamp' in df.columns and not df['timestamp'].isna().all():
            time_span = (df['timestamp'].max() - df['timestamp'].min()).days
            st.metric("Time Span", f"{time_span} days")
        else:
            st.metric("Time Span", "N/A")
    
    with col4:
        if 'ip' in df.columns:
            unique_ips = df['ip'].nunique()
            st.metric("Unique IPs", f"{unique_ips:,}")
        else:
            st.metric("Unique IPs", "N/A")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Traffic Patterns", "⚠️ Error Analysis", "📊 Statistics", "📋 Raw Data"])
    
    with tab1:
        st.subheader("Traffic Patterns Over Time")
        
        if 'timestamp' in df.columns and not df['timestamp'].isna().all():
            df_time = df.copy()
            df_time['hour'] = df_time['timestamp'].dt.floor('H')
            traffic_by_hour = df_time.groupby('hour').size().reset_index(name='requests')
            
            st.markdown("#### 📊 Real-Time Request Stream")
            
            last_5_minutes = df_time[df_time['timestamp'] >= (df_time['timestamp'].max() - timedelta(minutes=5))]
            if not last_5_minutes.empty:
                last_5_minutes['minute'] = last_5_minutes['timestamp'].dt.floor('min')
                streaming_data = last_5_minutes.groupby('minute').size().reset_index(name='requests')
                
                fig_stream = go.Figure()
                fig_stream.add_trace(go.Scatter(
                    x=streaming_data['minute'],
                    y=streaming_data['requests'],
                    mode='lines+markers',
                    fill='tozeroy',
                    line=dict(color='#00cc96', width=3),
                    marker=dict(size=8, color='#00cc96'),
                    name='Live Traffic'
                ))
                
                fig_stream.update_layout(
                    title='Last 5 Minutes Activity (Live)',
                    xaxis_title='Time',
                    yaxis_title='Requests per Minute',
                    height=250,
                    margin=dict(l=40, r=40, t=60, b=40),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_stream, use_container_width=True)
            else:
                st.info("Waiting for recent data...")
            
            st.markdown("#### 📈 Overall Traffic Timeline")
            fig_traffic = px.line(
                traffic_by_hour,
                x='hour',
                y='requests',
                title='Requests Over Time',
                labels={'hour': 'Time', 'requests': 'Number of Requests'}
            )
            fig_traffic.update_traces(line_color='#1f77b4', line_width=2)
            fig_traffic.update_layout(hovermode='x unified')
            st.plotly_chart(fig_traffic, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Peak Traffic Times")
                top_hours = traffic_by_hour.nlargest(10, 'requests')
                st.dataframe(
                    top_hours.style.format({'hour': lambda x: x.strftime('%Y-%m-%d %H:%M')}),
                    hide_index=True,
                    use_container_width=True
                )
            
            with col2:
                st.markdown("#### Requests by Hour of Day")
                df_time['hour_of_day'] = df_time['timestamp'].dt.hour
                hourly_dist = df_time.groupby('hour_of_day').size().reset_index(name='requests')
                
                fig_hourly = px.bar(
                    hourly_dist,
                    x='hour_of_day',
                    y='requests',
                    title='Distribution by Hour',
                    labels={'hour_of_day': 'Hour of Day', 'requests': 'Requests'}
                )
                st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("⏰ Timestamp data not available. Showing alternative traffic visualizations:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'path' in df.columns:
                    st.markdown("#### 🔝 Top Requested Paths")
                    path_counts = df['path'].value_counts().head(15).reset_index()
                    path_counts.columns = ['Path', 'Requests']
                    
                    fig_paths = px.bar(
                        path_counts,
                        y='Path',
                        x='Requests',
                        orientation='h',
                        title='Most Accessed Resources',
                        labels={'Path': 'Path', 'Requests': 'Number of Requests'},
                        color='Requests',
                        color_continuous_scale='Blues'
                    )
                    fig_paths.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_paths, use_container_width=True)
                else:
                    st.info("No path data available.")
            
            with col2:
                if 'ip' in df.columns:
                    st.markdown("#### 🌐 Top IP Addresses")
                    ip_counts = df['ip'].value_counts().head(15).reset_index()
                    ip_counts.columns = ['IP Address', 'Requests']
                    
                    fig_ips = px.bar(
                        ip_counts,
                        y='IP Address',
                        x='Requests',
                        orientation='h',
                        title='Most Active IPs',
                        labels={'IP Address': 'IP', 'Requests': 'Number of Requests'},
                        color='Requests',
                        color_continuous_scale='Greens'
                    )
                    fig_ips.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_ips, use_container_width=True)
                else:
                    st.info("No IP address data available.")
            
            if 'method' in df.columns:
                st.markdown("#### 📡 HTTP Methods Distribution")
                method_counts = df['method'].value_counts().reset_index()
                method_counts.columns = ['Method', 'Count']
                
                fig_methods = px.pie(
                    method_counts,
                    values='Count',
                    names='Method',
                    title='Request Methods',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_methods, use_container_width=True)
            
            st.markdown("#### 📊 Log Entry Sequence")
            df_sequence = df.copy()
            df_sequence['entry_number'] = range(1, len(df_sequence) + 1)
            
            if 'status_code' in df.columns:
                fig_sequence = px.scatter(
                    df_sequence,
                    x='entry_number',
                    y='status_code',
                    color='status_code',
                    title='Status Codes Across Log Entries',
                    labels={'entry_number': 'Log Entry Number', 'status_code': 'Status Code'},
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_sequence, use_container_width=True)
            else:
                st.line_chart(df_sequence.set_index('entry_number'))
    
    with tab2:
        st.subheader("Error Frequency Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'error_level' in df.columns:
                error_counts = df['error_level'].value_counts().reset_index()
                error_counts.columns = ['Error Level', 'Count']
                
                fig_errors = px.bar(
                    error_counts,
                    x='Error Level',
                    y='Count',
                    title='Errors by Level',
                    color='Error Level',
                    text='Count'
                )
                fig_errors.update_traces(textposition='outside')
                st.plotly_chart(fig_errors, use_container_width=True)
            else:
                st.info("No error level data available.")
        
        with col2:
            if 'status_code' in df.columns:
                status_counts = df['status_code'].value_counts().reset_index()
                status_counts.columns = ['Status Code', 'Count']
                status_counts = status_counts.head(10)
                
                fig_status = px.pie(
                    status_counts,
                    values='Count',
                    names='Status Code',
                    title='Top 10 Status Codes'
                )
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No status code data available.")
        
        if 'timestamp' in df.columns and 'error_level' in df.columns and not df['timestamp'].isna().all():
            st.markdown("#### Errors Over Time")
            df_errors = df[df['error_level'].isin(['ERROR', 'SERVER_ERROR', 'CLIENT_ERROR'])].copy()
            
            if not df_errors.empty:
                df_errors['hour'] = df_errors['timestamp'].dt.floor('H')
                errors_by_time = df_errors.groupby(['hour', 'error_level']).size().reset_index(name='count')
                
                fig_errors_time = px.line(
                    errors_by_time,
                    x='hour',
                    y='count',
                    color='error_level',
                    title='Error Trends',
                    labels={'hour': 'Time', 'count': 'Error Count', 'error_level': 'Error Level'}
                )
                st.plotly_chart(fig_errors_time, use_container_width=True)
            else:
                st.info("No errors found in the selected time range.")
    
    with tab3:
        st.subheader("Statistical Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'method' in df.columns:
                st.markdown("#### HTTP Methods")
                method_counts = df['method'].value_counts().reset_index()
                method_counts.columns = ['Method', 'Count']
                st.dataframe(method_counts, hide_index=True, use_container_width=True)
        
        with col2:
            if 'path' in df.columns:
                st.markdown("#### Top Requested Paths")
                path_counts = df['path'].value_counts().head(10).reset_index()
                path_counts.columns = ['Path', 'Requests']
                st.dataframe(path_counts, hide_index=True, use_container_width=True)
        
        if 'ip' in df.columns:
            st.markdown("#### Top IP Addresses")
            ip_counts = df['ip'].value_counts().head(10).reset_index()
            ip_counts.columns = ['IP Address', 'Requests']
            
            fig_ips = px.bar(
                ip_counts,
                x='IP Address',
                y='Requests',
                title='Most Active IPs',
                text='Requests'
            )
            fig_ips.update_traces(textposition='outside')
            st.plotly_chart(fig_ips, use_container_width=True)
    
    with tab4:
        st.subheader("Raw Log Data")
        
        search_term = st.text_input("🔍 Search logs", "")
        
        display_df = df.copy()
        
        if search_term:
            mask = display_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
            display_df = display_df[mask]
        
        if 'error_level' in display_df.columns:
            if len(st.session_state.new_errors) > 0:
                st.markdown("##### 🚨 NEW ERRORS DETECTED!")
                new_error_df = display_df[display_df.index.isin(st.session_state.new_errors)]
                
                for idx, row in new_error_df.iterrows():
                    with st.container():
                        error_msg = row.get('message', row.get('raw', 'No message'))
                        timestamp = row.get('timestamp', 'Unknown time')
                        error_level = row.get('error_level', 'ERROR')
                        
                        st.error(f"🆕 **NEW {error_level}** [{timestamp}]: {error_msg}")
                
                st.markdown("---")
            
            st.markdown("##### 🚨 Recent Errors (Last 10)")
            error_df = display_df[display_df['error_level'].isin(['ERROR', 'SERVER_ERROR', 'CLIENT_ERROR'])].tail(10)
            
            if not error_df.empty:
                for idx, row in error_df.iterrows():
                    with st.container():
                        error_msg = row.get('message', row.get('raw', 'No message'))
                        timestamp = row.get('timestamp', 'Unknown time')
                        error_level = row.get('error_level', 'ERROR')
                        is_new = idx in st.session_state.new_errors
                        
                        if is_new:
                            prefix = "🆕 NEW"
                        else:
                            prefix = ""
                        
                        if error_level == 'SERVER_ERROR':
                            st.error(f"{prefix} 🔴 **{error_level}** [{timestamp}]: {error_msg}")
                        elif error_level == 'CLIENT_ERROR':
                            st.warning(f"{prefix} 🟡 **{error_level}** [{timestamp}]: {error_msg}")
                        else:
                            st.error(f"{prefix} ⛔ **{error_level}** [{timestamp}]: {error_msg}")
            else:
                st.success("✅ No errors found!")
        
        st.markdown("---")
        st.markdown("##### All Logs")
        
        def highlight_errors(row):
            row_idx = row.name
            if 'error_level' in row:
                if row_idx in st.session_state.new_errors:
                    return ['background-color: #ff6b6b; color: white; font-weight: bold'] * len(row)
                elif row['error_level'] in ['ERROR', 'SERVER_ERROR']:
                    return ['background-color: #ffcccc'] * len(row)
                elif row['error_level'] == 'CLIENT_ERROR':
                    return ['background-color: #fff4cc'] * len(row)
            return [''] * len(row)
        
        if 'error_level' in display_df.columns:
            styled_df = display_df.style.apply(highlight_errors, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(display_df, use_container_width=True, height=400)
        
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=display_df.to_csv(index=False).encode('utf-8'),
            file_name=f"filtered_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    st.info("👈 Please upload a log file from the sidebar to start analyzing.")

st.markdown("""
<style>
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@keyframes pulse {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
    }
    50% {
        box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
    }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.floating-chat-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
}

.chat-toggle-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50%;
    width: 70px;
    height: 70px;
    font-size: 32px;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    animation: pulse 2s infinite;
    display: flex;
    align-items: center;
    justify-content: center;
}

.chat-toggle-btn:hover {
    transform: scale(1.15) rotate(5deg);
    box-shadow: 0 12px 32px rgba(102, 126, 234, 0.6);
}

.chat-window {
    position: fixed;
    bottom: 105px;
    right: 20px;
    width: 420px;
    max-height: 600px;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(102, 126, 234, 0.1);
    display: flex;
    flex-direction: column;
    z-index: 9998;
    overflow: hidden;
    animation: slideIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    border: 2px solid rgba(102, 126, 234, 0.2);
}

.chat-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px 24px;
    font-weight: 700;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    position: relative;
    overflow: hidden;
}

.chat-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0%, 100% { transform: translate(-50%, -50%) rotate(0deg); }
    50% { transform: translate(-30%, -30%) rotate(180deg); }
}

.chat-status {
    font-size: 11px;
    opacity: 0.9;
    font-weight: 400;
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #4ade80;
    border-radius: 50%;
    animation: blink 2s infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.chat-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    max-height: 420px;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.chat-body::-webkit-scrollbar {
    width: 6px;
}

.chat-body::-webkit-scrollbar-track {
    background: transparent;
}

.chat-body::-webkit-scrollbar-thumb {
    background: #667eea;
    border-radius: 10px;
}

.welcome-message {
    text-align: center;
    padding: 30px 20px;
    animation: fadeIn 0.6s ease-out;
}

.welcome-icon {
    font-size: 48px;
    margin-bottom: 12px;
    animation: wave 1s infinite;
}

@keyframes wave {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(20deg); }
    75% { transform: rotate(-20deg); }
}

.welcome-text {
    font-size: 16px;
    color: #4a5568;
    line-height: 1.6;
    margin: 10px 0;
}

.welcome-subtext {
    font-size: 13px;
    color: #718096;
    margin-top: 8px;
}

.message-wrapper {
    display: flex;
    margin-bottom: 16px;
    animation: fadeIn 0.3s ease-out;
    gap: 10px;
}

.message-wrapper.user {
    flex-direction: row-reverse;
}

.message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-avatar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.ai-avatar {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.message-content {
    max-width: 75%;
}

.chat-message {
    padding: 12px 16px;
    border-radius: 18px;
    word-wrap: break-word;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    position: relative;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom-right-radius: 4px;
}

.ai-message {
    background: white;
    color: #2d3748;
    border: 1px solid #e2e8f0;
    border-bottom-left-radius: 4px;
}

.message-time {
    font-size: 10px;
    opacity: 0.7;
    margin-top: 4px;
}

.typing-indicator {
    display: flex;
    gap: 4px;
    padding: 12px 16px;
    background: white;
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    width: fit-content;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.typing-dot {
    width: 8px;
    height: 8px;
    background: #cbd5e0;
    border-radius: 50%;
    animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
    30% { transform: translateY(-10px); opacity: 1; }
}

.chat-input-area {
    padding: 16px 20px;
    background: white;
    border-top: 2px solid #e2e8f0;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
}

.quick-questions {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}

.quick-question-btn {
    padding: 6px 12px;
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    font-size: 12px;
    color: #4a5568;
    cursor: pointer;
    transition: all 0.2s;
}

.quick-question-btn:hover {
    background: #edf2f7;
    border-color: #667eea;
    color: #667eea;
}

.chatbot-icon-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.avatar-icon-img {
    width: 32px;
    height: 32px;
    object-fit: contain;
    border-radius: 50%;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.auto_refresh:
    time.sleep(5)
    st.rerun()
