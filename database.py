
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_name: str = "app_data.db"):
        self.db_name = db_name
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            cursor = self.conn.cursor()
            
            # Create scans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    people_count INTEGER DEFAULT 0,
                    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    detection_time REAL DEFAULT 0,
                    confidence_threshold REAL DEFAULT 0.5,
                    model_used TEXT DEFAULT 'yolov8n.pt',
                    status TEXT DEFAULT 'success'
                )
            ''')
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT DEFAULT 'INFO',
                    message TEXT NOT NULL,
                    source TEXT DEFAULT 'app',
                    scan_id INTEGER,
                    FOREIGN KEY(scan_id) REFERENCES scans(id)
                )
            ''')
            
            # Create scan_details table for individual detections
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    bbox_x1 INTEGER,
                    bbox_y1 INTEGER,
                    bbox_x2 INTEGER,
                    bbox_y2 INTEGER,
                    confidence REAL,
                    class_name TEXT DEFAULT 'person',
                    FOREIGN KEY(scan_id) REFERENCES scans(id)
                )
            ''')
            
            self.conn.commit()
            print(f"✓ Database initialized successfully: {self.db_name}")
            
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
    
    def add_scan(self, image_path: str, filename: str, people_count: int = 0, 
                 detection_time: float = 0.0, confidence_threshold: float = 0.5,
                 model_used: str = 'yolov8n.pt', status: str = 'success') -> int:
        """Add a new scan record to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO scans (image_path, filename, people_count, detection_time, 
                                confidence_threshold, model_used, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (image_path, filename, people_count, detection_time, 
                  confidence_threshold, model_used, status))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"✗ Failed to add scan: {e}")
            return -1
    
    def add_scan_detail(self, scan_id: int, bbox: tuple, confidence: float, class_name: str = 'person'):
        """Add detection details for a scan"""
        try:
            cursor = self.conn.cursor()
            x1, y1, x2, y2 = bbox
            cursor.execute('''
                INSERT INTO scan_details (scan_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, confidence, class_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (scan_id, x1, y1, x2, y2, confidence, class_name))
            self.conn.commit()
        except Exception as e:
            print(f"✗ Failed to add scan detail: {e}")
    
    def add_log(self, message: str, level: str = 'INFO', source: str = 'app', scan_id: int = None):
        """Add a log entry"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO logs (timestamp, level, message, source, scan_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), level, message, source, scan_id))
            self.conn.commit()
        except Exception as e:
            print(f"✗ Failed to add log: {e}")
    
    def get_all_scans(self) -> List[Dict]:
        """Get all scan records"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM scans ORDER BY scan_date DESC')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"✗ Failed to get scans: {e}")
            return []
    
    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent log entries"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"✗ Failed to get logs: {e}")
            return []
    
    def get_scan_details(self, scan_id: int) -> List[Dict]:
        """Get detection details for a specific scan"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM scan_details WHERE scan_id = ?', (scan_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"✗ Failed to get scan details: {e}")
            return []
    
    def get_scan_stats(self) -> Dict:
        """Get statistics about scans"""
        try:
            cursor = self.conn.cursor()
            
            # Total scans
            cursor.execute('SELECT COUNT(*) FROM scans')
            total_scans = cursor.fetchone()[0]
            
            # Total people detected
            cursor.execute('SELECT COALESCE(SUM(people_count), 0) FROM scans')
            total_people = cursor.fetchone()[0]
            
            # Average people per scan
            if total_scans > 0:
                avg_people = round(total_people / total_scans, 2)
            else:
                avg_people = 0.0
            
            # Today's scans
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM scans WHERE DATE(scan_date) = ?", (today,))
            today_scans = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute('SELECT COUNT(*) FROM scans WHERE status = "success"')
            success_count = cursor.fetchone()[0]
            if total_scans > 0:
                success_rate = round((success_count / total_scans) * 100, 2)
            else:
                success_rate = 100.0
            
            return {
                'total_scans': total_scans,
                'total_people': total_people,
                'avg_people_per_scan': avg_people,
                'today_scans': today_scans,
                'success_rate': success_rate
            }
        except Exception as e:
            print(f"✗ Failed to get stats: {e}")
            return {}
    
    def delete_scan(self, scan_id: int):
        """Delete a scan and its associated details"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM scan_details WHERE scan_id = ?', (scan_id,))
            cursor.execute('DELETE FROM logs WHERE scan_id = ?', (scan_id,))
            cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
            self.conn.commit()
        except Exception as e:
            print(f"✗ Failed to delete scan: {e}")
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()

# Example usage
if __name__ == "__main__":
    db = DatabaseManager()
    
    # Test adding a scan
    scan_id = db.add_scan(
        image_path="/path/to/image.jpg",
        filename="image.jpg",
        people_count=3,
        detection_time=0.5,
        confidence_threshold=0.5,
        model_used="yolov8n.pt",
        status="success"
    )
    print(f"Added scan with ID: {scan_id}")
    
    # Test adding a log
    db.add_log("Test log message", level="INFO", source="test", scan_id=scan_id)
    print("Added log entry")
    
    # Test getting stats
    stats = db.get_scan_stats()
    print("Scan Statistics:", stats)
    
    # Test getting scans
    scans = db.get_all_scans()
    print(f"Total scans in DB: {len(scans)}")
    
    # Test getting logs
    logs = db.get_all_logs()
    print(f"Total logs in DB: {len(logs)}")
    
    db.close()
