import psutil
import threading
import time
from datetime import datetime, timedelta
import json
import os
import socket
import hashlib

class FirewallCore:
    def __init__(self):
        self.blocked_ips = set()
        self.allowed_ips = set()
        self.open_ports = set()
        self.closed_ports = set()
        self.access_requests = {}  # request_id: {ip, port, timestamp, approved}
        self.connection_counts = {}  # ip: {count, last_reset}
        self.ddos_threshold = 50  # connections per minute (more sensitive for pentesting)
        self.block_duration = 15  # minutes
        self.ddos_blocked_ips = set()
        self.ddos_protection_enabled = True
        self.connection_logs = []  # Log of all connections
        self.suspicious_ips = set()  # IPs flagged for suspicious behavior
        self.whitelisted_ips = set()  # IPs that should never be blocked
        
        # Load data from files if they exist
        self.load_data()
        
        # Start monitoring threads
        self.start_monitoring()
        
    def add_blocked_ip(self, ip):
        """Add an IP to the blocked list"""
        if ip not in self.whitelisted_ips:
            self.blocked_ips.add(ip)
            self.save_data()
            return True
        return False
        
    def remove_blocked_ip(self, ip):
        """Remove an IP from the blocked list"""
        self.blocked_ips.discard(ip)
        self.save_data()
        return True
        
    def add_allowed_ip(self, ip):
        """Add an IP to the allowed list"""
        self.allowed_ips.add(ip)
        self.save_data()
        return True
        
    def remove_allowed_ip(self, ip):
        """Remove an IP from the allowed list"""
        self.allowed_ips.discard(ip)
        self.save_data()
        return True
        
    def whitelist_ip(self, ip):
        """Add an IP to the whitelist (cannot be blocked)"""
        self.whitelisted_ips.add(ip)
        # Remove from blocked list if present
        self.blocked_ips.discard(ip)
        self.save_data()
        return True
        
    def remove_whitelisted_ip(self, ip):
        """Remove an IP from the whitelist"""
        self.whitelisted_ips.discard(ip)
        self.save_data()
        return True
        
    def open_port(self, port):
        """Open a port"""
        self.open_ports.add(port)
        self.closed_ports.discard(port)
        self.save_data()
        return True
        
    def close_port(self, port):
        """Close a port"""
        self.closed_ports.add(port)
        self.open_ports.discard(port)
        self.save_data()
        return True
        
    def is_ip_blocked(self, ip):
        """Check if an IP is blocked"""
        return ip in self.blocked_ips or ip in self.ddos_blocked_ips
        
    def is_ip_allowed(self, ip):
        """Check if an IP is explicitly allowed"""
        return ip in self.allowed_ips
        
    def is_ip_whitelisted(self, ip):
        """Check if an IP is whitelisted"""
        return ip in self.whitelisted_ips
        
    def is_port_open(self, port):
        """Check if a port is open"""
        return port in self.open_ports and port not in self.closed_ports
        
    def is_port_closed(self, port):
        """Check if a port is closed"""
        return port in self.closed_ports
        
    def request_access(self, ip, port):
        """Request access to a specific IP and port"""
        request_id = f"REQ{int(time.time()) % 1000000}"
        self.access_requests[request_id] = {
            "ip": ip,
            "port": port,
            "timestamp": datetime.now(),
            "approved": None
        }
        self.save_data()
        return request_id
        
    def approve_request(self, request_id):
        """Approve an access request"""
        if request_id in self.access_requests:
            self.access_requests[request_id]["approved"] = True
            self.access_requests[request_id]["approval_time"] = datetime.now()
            self.save_data()
            return True
        return False
        
    def reject_request(self, request_id):
        """Reject an access request"""
        if request_id in self.access_requests:
            self.access_requests[request_id]["approved"] = False
            self.access_requests[request_id]["approval_time"] = datetime.now()
            self.save_data()
            return True
        return False
        
    def is_request_approved(self, request_id):
        """Check if a request is approved"""
        if request_id in self.access_requests:
            request = self.access_requests[request_id]
            # Check if request has expired (older than 10 minutes)
            if datetime.now() - request["timestamp"] > timedelta(minutes=10):
                if request["approved"] is None:
                    # Auto-reject expired requests
                    self.access_requests[request_id]["approved"] = False
                    self.save_data()
                return request["approved"]
            return request["approved"]
        return False
        
    def check_ddos_protection(self, ip):
        """Check if an IP should be blocked for DDoS protection"""
        if not self.ddos_protection_enabled:
            return False
            
        # Never block whitelisted IPs
        if ip in self.whitelisted_ips:
            return False
            
        # Check if IP is already blocked for DDoS
        if ip in self.ddos_blocked_ips:
            # Check if block duration has expired
            if ip in self.connection_counts:
                block_time = self.connection_counts[ip].get("blocked_at")
                if block_time and datetime.now() - block_time > timedelta(minutes=self.block_duration):
                    self.ddos_blocked_ips.discard(ip)
                    self.connection_counts[ip]["count"] = 0
                    self.connection_counts[ip]["last_reset"] = datetime.now()
                    return False
            return True
            
        # Update connection count for this IP
        now = datetime.now()
        if ip not in self.connection_counts:
            self.connection_counts[ip] = {"count": 1, "last_reset": now, "blocked_at": None}
        else:
            # Reset count if more than a minute has passed
            if now - self.connection_counts[ip]["last_reset"] > timedelta(minutes=1):
                self.connection_counts[ip]["count"] = 0
                self.connection_counts[ip]["last_reset"] = now
                
            self.connection_counts[ip]["count"] += 1
            
            # Check if threshold is exceeded
            if self.connection_counts[ip]["count"] > self.ddos_threshold:
                self.ddos_blocked_ips.add(ip)
                self.connection_counts[ip]["blocked_at"] = now
                self.log_connection(ip, "DDoS_BLOCK", "Blocked for excessive connections")
                self.save_data()
                return True
                
        return False
        
    def toggle_ddos_protection(self):
        """Toggle DDoS protection on/off"""
        self.ddos_protection_enabled = not self.ddos_protection_enabled
        return self.ddos_protection_enabled
        
    def set_ddos_threshold(self, threshold):
        """Set the DDoS connection threshold"""
        self.ddos_threshold = threshold
        return True
        
    def set_block_duration(self, duration):
        """Set the DDoS block duration in minutes"""
        self.block_duration = duration
        return True
        
    def get_blocked_ips(self):
        """Get list of blocked IPs"""
        return list(self.blocked_ips)
        
    def get_allowed_ips(self):
        """Get list of allowed IPs"""
        return list(self.allowed_ips)
        
    def get_whitelisted_ips(self):
        """Get list of whitelisted IPs"""
        return list(self.whitelisted_ips)
        
    def get_open_ports(self):
        """Get list of open ports"""
        return list(self.open_ports)
        
    def get_closed_ports(self):
        """Get list of closed ports"""
        return list(self.closed_ports)
        
    def get_pending_requests(self):
        """Get list of pending access requests"""
        pending = []
        now = datetime.now()
        for req_id, req in self.access_requests.items():
            # Check if request has expired (older than 10 minutes)
            if now - req["timestamp"] <= timedelta(minutes=10) and req["approved"] is None:
                pending.append({
                    "id": req_id,
                    "ip": req["ip"],
                    "port": req["port"],
                    "timestamp": req["timestamp"]
                })
        return pending
        
    def get_approved_requests(self):
        """Get list of approved access requests"""
        approved = []
        for req_id, req in self.access_requests.items():
            if req["approved"] is True:
                approved.append({
                    "id": req_id,
                    "ip": req["ip"],
                    "port": req["port"],
                    "timestamp": req["timestamp"],
                    "approval_time": req.get("approval_time")
                })
        return approved
        
    def get_ddos_blocked_ips(self):
        """Get list of IPs blocked by DDoS protection"""
        return list(self.ddos_blocked_ips)
        
    def log_connection(self, ip, action, details=""):
        """Log a connection attempt"""
        log_entry = {
            "timestamp": datetime.now(),
            "ip": ip,
            "action": action,
            "details": details
        }
        self.connection_logs.append(log_entry)
        
        # Keep only the last 1000 logs to prevent memory issues
        if len(self.connection_logs) > 1000:
            self.connection_logs = self.connection_logs[-1000:]
            
    def get_connection_logs(self, limit=50):
        """Get recent connection logs"""
        return self.connection_logs[-limit:]
        
    def flag_suspicious_ip(self, ip):
        """Flag an IP as suspicious"""
        self.suspicious_ips.add(ip)
        
    def is_ip_suspicious(self, ip):
        """Check if an IP is flagged as suspicious"""
        return ip in self.suspicious_ips
        
    def load_data(self):
        """Load data from files if they exist"""
        if os.path.exists("firewall_data.json"):
            try:
                with open("firewall_data.json", "r") as f:
                    data = json.load(f)
                    
                self.blocked_ips = set(data.get("blocked_ips", []))
                self.allowed_ips = set(data.get("allowed_ips", []))
                self.whitelisted_ips = set(data.get("whitelisted_ips", []))
                self.open_ports = set(data.get("open_ports", []))
                self.closed_ports = set(data.get("closed_ports", []))
                
                # Load access requests with datetime conversion
                requests_data = data.get("access_requests", {})
                self.access_requests = {}
                for req_id, req in requests_data.items():
                    self.access_requests[req_id] = {
                        "ip": req["ip"],
                        "port": req["port"],
                        "timestamp": datetime.fromisoformat(req["timestamp"]),
                        "approved": req["approved"]
                    }
                    if "approval_time" in req and req["approval_time"]:
                        self.access_requests[req_id]["approval_time"] = datetime.fromisoformat(req["approval_time"])
                        
            except Exception as e:
                print(f"Error loading data: {e}")
                
    def save_data(self):
        """Save data to file"""
        data = {
            "blocked_ips": list(self.blocked_ips),
            "allowed_ips": list(self.allowed_ips),
            "whitelisted_ips": list(self.whitelisted_ips),
            "open_ports": list(self.open_ports),
            "closed_ports": list(self.closed_ports),
            "access_requests": {}
        }
        
        # Convert datetime objects to strings for JSON serialization
        for req_id, req in self.access_requests.items():
            data["access_requests"][req_id] = {
                "ip": req["ip"],
                "port": req["port"],
                "timestamp": req["timestamp"].isoformat(),
                "approved": req["approved"]
            }
            if "approval_time" in req and req["approval_time"]:
                data["access_requests"][req_id]["approval_time"] = req["approval_time"].isoformat()
                
        try:
            with open("firewall_data.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
            
    def start_monitoring(self):
        """Start background monitoring threads"""
        # Start thread to periodically check for expired requests
        self.check_expired_thread = threading.Thread(target=self._check_expired_requests, daemon=True)
        self.check_expired_thread.start()
        
        # Start thread to clean up connection counts
        self.cleanup_connections_thread = threading.Thread(target=self._cleanup_connection_counts, daemon=True)
        self.cleanup_connections_thread.start()
        
    def _check_expired_requests(self):
        """Background thread to check for expired requests"""
        while True:
            time.sleep(60)  # Check every minute
            now = datetime.now()
            expired_requests = []
            
            for req_id, req in self.access_requests.items():
                # Check if request has expired (older than 10 minutes)
                if now - req["timestamp"] > timedelta(minutes=10) and req["approved"] is None:
                    expired_requests.append(req_id)
                    
            # Auto-reject expired requests
            if expired_requests:
                for req_id in expired_requests:
                    self.access_requests[req_id]["approved"] = False
                self.save_data()
                
    def _cleanup_connection_counts(self):
        """Background thread to clean up old connection counts"""
        while True:
            time.sleep(300)  # Check every 5 minutes
            now = datetime.now()
            ips_to_remove = []
            
            for ip, data in self.connection_counts.items():
                # Remove counts older than 2 minutes if not blocked
                if ip not in self.ddos_blocked_ips and now - data["last_reset"] > timedelta(minutes=2):
                    ips_to_remove.append(ip)
                    
            for ip in ips_to_remove:
                del self.connection_counts[ip]

# Global firewall instance
firewall = FirewallCore()

if __name__ == "__main__":
    # Example usage
    print("Firewall Core initialized")
    print("Blocked IPs:", firewall.get_blocked_ips())
    print("Allowed IPs:", firewall.get_allowed_ips())
    print("Whitelisted IPs:", firewall.get_whitelisted_ips())
    print("Open Ports:", firewall.get_open_ports())
    print("Closed Ports:", firewall.get_closed_ports())