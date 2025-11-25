import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class LogParser:
    def __init__(self):
        self.apache_pattern = r'(\S+) \S+ \S+ \[(.*?)\] "(\S+) (\S+) (\S+)" (\d+) (\S+)'
        self.nginx_pattern = r'(\S+) - - \[(.*?)\] "(\S+) (\S+) (\S+)" (\d+) (\d+)'
        self.common_error_pattern = r'\[(.*?)\] \[(.*?)\] (.*)'
        
    def detect_format(self, lines: List[str]) -> str:
        """Detect the log format from sample lines."""
        sample = lines[:10] if len(lines) > 10 else lines
        
        apache_matches = sum(1 for line in sample if re.match(self.apache_pattern, line))
        nginx_matches = sum(1 for line in sample if re.match(self.nginx_pattern, line))
        error_matches = sum(1 for line in sample if re.match(self.common_error_pattern, line))
        
        if apache_matches >= len(sample) * 0.5:
            return 'apache'
        elif nginx_matches >= len(sample) * 0.5:
            return 'nginx'
        elif error_matches >= len(sample) * 0.5:
            return 'error'
        else:
            return 'generic'
    
    def parse_apache_log(self, line: str) -> Optional[Dict]:
        """Parse Apache/Combined log format - extract all tokens even if malformed."""
        match = re.match(self.apache_pattern, line)
        if match:
            ip, timestamp, method, path, protocol, status, size = match.groups()
            try:
                dt = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S %z')
            except:
                try:
                    dt = datetime.strptime(timestamp.split()[0], '%d/%b/%Y:%H:%M:%S')
                except:
                    dt = None
            
            return {
                'ip': ip,
                'timestamp': dt,
                'timestamp_raw': timestamp,
                'method': method,
                'path': path,
                'protocol': protocol,
                'status_code': int(status),
                'size': size,
                'error_level': self._classify_status(int(status)),
                'raw': line
            }
        
        parts = re.split(r'\s*"\s*|"\s*|\s+', line)
        if len(parts) < 5:
            return None
        
        ip = parts[0] if parts else '-'
        
        timestamp_match = re.search(r'\[(.*?)\]', line)
        timestamp = timestamp_match.group(1) if timestamp_match else '-'
        timestamp_dt = None
        if timestamp and timestamp != '-':
            try:
                timestamp_dt = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S %z')
            except:
                try:
                    if ' ' in timestamp:
                        timestamp_dt = datetime.strptime(timestamp.split()[0], '%d/%b/%Y:%H:%M:%S')
                except:
                    pass
        
        request_match = re.search(r'"([^"]*)"', line)
        if request_match:
            request = request_match.group(1).split()
            method = request[0] if len(request) > 0 else '-'
            path = request[1] if len(request) > 1 else '-'
            protocol = request[2] if len(request) > 2 else '-'
        else:
            method, path, protocol = '-', '-', '-'
        
        after_request = line.split('"')[-1].strip().split() if '"' in line else parts[-2:]
        status = after_request[0] if len(after_request) > 0 else '-'
        size = after_request[1] if len(after_request) > 1 else '-'
        
        return {
            'ip': ip,
            'timestamp': timestamp_dt,
            'timestamp_raw': timestamp,
            'method': method,
            'path': path,
            'protocol': protocol,
            'status_code': status,
            'size': size,
            'error_level': 'INFO',
            'raw': line
        }
        
        return None
    
    def parse_nginx_log(self, line: str) -> Optional[Dict]:
        """Parse Nginx log format."""
        match = re.match(self.nginx_pattern, line)
        if match:
            ip, timestamp, method, path, protocol, status, size = match.groups()
            try:
                dt = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S %z')
            except:
                try:
                    dt = datetime.strptime(timestamp.split()[0], '%d/%b/%Y:%H:%M:%S')
                except:
                    dt = None
            
            return {
                'ip': ip,
                'timestamp': dt,
                'method': method,
                'path': path,
                'protocol': protocol,
                'status_code': int(status),
                'size': size,
                'error_level': self._classify_status(int(status)),
                'raw': line
            }
        return None
    
    def parse_error_log(self, line: str) -> Optional[Dict]:
        """Parse generic error log format."""
        match = re.match(self.common_error_pattern, line)
        if match:
            timestamp_str, level, message = match.groups()
            try:
                dt = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')
            except:
                dt = None
            
            return {
                'timestamp': dt,
                'error_level': level.upper(),
                'message': message,
                'status_code': self._level_to_status(level),
                'raw': line
            }
        return None
    
    def parse_generic_log(self, line: str) -> Optional[Dict]:
        """Parse generic log lines - extract timestamp if possible."""
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})',
            r'\[(.*?)\]'
        ]
        
        dt = None
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    dt = pd.to_datetime(timestamp_str, errors='coerce')
                    break
                except:
                    continue
        
        error_level = 'INFO'
        if any(word in line.upper() for word in ['ERROR', 'CRITICAL', 'FATAL']):
            error_level = 'ERROR'
        elif 'WARN' in line.upper():
            error_level = 'WARNING'
        
        return {
            'timestamp': dt,
            'message': line,
            'error_level': error_level,
            'raw': line
        }
    
    def _classify_status(self, status_code: int) -> str:
        """Classify HTTP status code into error levels."""
        if status_code < 300:
            return 'SUCCESS'
        elif status_code < 400:
            return 'REDIRECT'
        elif status_code < 500:
            return 'CLIENT_ERROR'
        else:
            return 'SERVER_ERROR'
    
    def _level_to_status(self, level: str) -> int:
        """Convert error level to approximate status code."""
        level = level.upper()
        if 'ERROR' in level or 'CRIT' in level:
            return 500
        elif 'WARN' in level:
            return 400
        else:
            return 200
    
    def parse_file(self, file_content: str) -> pd.DataFrame:
        """Parse entire log file and return DataFrame."""
        lines = file_content.strip().split('\n')
        log_format = self.detect_format(lines)
        
        parsed_logs = []
        
        for line in lines:
            if not line.strip():
                continue
            
            if log_format == 'apache':
                parsed = self.parse_apache_log(line)
            elif log_format == 'nginx':
                parsed = self.parse_nginx_log(line)
            elif log_format == 'error':
                parsed = self.parse_error_log(line)
            else:
                parsed = self.parse_generic_log(line)
            
            if parsed:
                parsed_logs.append(parsed)
            else:
                parsed_logs.append({
                    'timestamp': None,
                    'raw': line,
                    'error_level': 'UNPARSED'
                })
        
        if not parsed_logs:
            return pd.DataFrame()
        
        df = pd.DataFrame(parsed_logs)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        if 'status_code' in df.columns:
            df['status_code'] = df['status_code'].astype('object')
        if 'size' in df.columns:
            df['size'] = df['size'].astype('object')
        
        return df
