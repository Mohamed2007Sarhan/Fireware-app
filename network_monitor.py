import psutil
import threading
import time
import socket
from datetime import datetime, timedelta
from firewall_core import firewall
import re

import ipaddress

class NetworkMonitor:
    def __init__(self):
        self.monitoring = False
        self.honeypot_active = False
        self.connections = []
        self.listeners = []
        self.suspicious_patterns = [
            r'.*nc.*',  # Netcat
            r'.*nmap.*',  # Nmap
            r'.*hydra.*',  # Hydra
            r'.*metasploit.*',  # Metasploit
            r'.*burp.*',  # Burp Suite
            r'.*wireshark.*',  # Wireshark
            r'.*tcpdump.*',  # Tcpdump
        ]
        
    def start_monitoring(self):
        """Start monitoring network connections"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self.monitor_thread.start()
        print("Network monitoring started")
        
    def set_honeypot_mode(self, active):
        """Enable or disable Honeypot mode"""
        self.honeypot_active = active
        print(f"Honeypot mode set to: {active}")

    def _is_honeypot_traffic(self, remote_ip, remote_port, local_port):
        """Check if traffic is related to the Honeypot"""
        if not self.honeypot_active:
            return False
            
        try:
            # Check for Docker Bridge Networks (172.17.0.0/16 and 172.18.0.0/16)
            if (ipaddress.ip_address(remote_ip) in ipaddress.ip_network('172.17.0.0/16') or 
                ipaddress.ip_address(remote_ip) in ipaddress.ip_network('172.18.0.0/16')):
                return True
                
            # Check for Honeypot ports
            honeypot_ports = [2222, 8080, 2121, 9999]
            if local_port in honeypot_ports or remote_port in honeypot_ports:
                return True
                
        except ValueError:
            pass
            
        return False

    def stop_monitoring(self):
        """Stop monitoring network connections"""
        self.monitoring = False
        print("Network monitoring stopped")
        
    def _monitor_connections(self):
        """Background thread to monitor connections"""
        while self.monitoring:
            try:
                # Get all network connections
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    # Process each connection
                    self._process_connection(conn)
                    
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Error monitoring connections: {e}")
                time.sleep(5)  # Wait longer on error
                
    def _process_connection(self, conn):
        """Process a single network connection"""
        try:
            # Get remote IP and port
            if conn.raddr:
                remote_ip = conn.raddr[0]  # IP is first element of tuple
                remote_port = conn.raddr[1]  # Port is second element
            else:
                return  # Skip connections without remote address
                
            # Get local port
            if hasattr(conn.laddr, '__len__') and len(conn.laddr) > 1:
                local_port = conn.laddr[1]  # Port is second element
            else:
                # Fallback for different psutil versions
                local_port = getattr(conn.laddr, 'port', 0)
                
            # Check if connection should be blocked
            if self._should_block_connection(remote_ip, remote_port, local_port):
                self._handle_blocked_connection(remote_ip, remote_port, local_port, conn)
                return
                
            # Check for DDoS protection
            if firewall.check_ddos_protection(remote_ip):
                self._handle_ddos_blocked_connection(remote_ip, remote_port, local_port, conn)
                return
                
            # Check if this is an access request
            if self._is_access_request(remote_ip, local_port):
                self._handle_access_request(remote_ip, local_port, conn)
                return
                
            # Check for suspicious activity
            if self._is_suspicious_activity(remote_ip, local_port):
                self._handle_suspicious_activity(remote_ip, local_port, conn)
                return
                
            # Connection is allowed
            self._log_allowed_connection(remote_ip, remote_port, local_port, conn)
            
        except Exception as e:
            print(f"Error processing connection: {e}")
            
    def _should_block_connection(self, remote_ip, remote_port, local_port):
        """Determine if a connection should be blocked"""
        # Bypass for Honeypot traffic
        if self._is_honeypot_traffic(remote_ip, remote_port, local_port):
            return False

        # Check if IP is explicitly blocked
        if firewall.is_ip_blocked(remote_ip):
            firewall.log_connection(remote_ip, "BLOCK", f"Blocked IP trying to access port {local_port}")
            return True
            
        # Check if port is closed
        if firewall.is_port_closed(local_port):
            firewall.log_connection(remote_ip, "BLOCK", f"Blocked access to closed port {local_port}")
            return True
            
        return False
        
    def _is_access_request(self, remote_ip, local_port):
        """Determine if this is a connection that requires access approval"""
        # Bypass for Honeypot traffic
        if self._is_honeypot_traffic(remote_ip, 0, local_port):
            return False

        # For penetration testing, we'll treat connections to common target ports as requiring approval
        target_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432, 8080]
        if local_port in target_ports:
            return True
        return False
        
    def _is_suspicious_activity(self, remote_ip, local_port):
        """Detect suspicious network activity"""
        # Bypass for Honeypot traffic
        if self._is_honeypot_traffic(remote_ip, 0, local_port):
            return False

        # Check for rapid connections from same IP (potential scanning)
        # This would require maintaining connection history, simplified here
        return False
        
    def _handle_blocked_connection(self, remote_ip, remote_port, local_port, conn):
        """Handle a blocked connection"""
        print(f"BLOCKED: Connection from {remote_ip}:{remote_port} to local port {local_port}")
        firewall.log_connection(remote_ip, "BLOCK", f"Blocked connection to port {local_port}")
        # In a real implementation, you would actually block the connection here
        # This might involve using netsh, iptables, or other system-level tools
        
    def _handle_ddos_blocked_connection(self, remote_ip, remote_port, local_port, conn):
        """Handle a DDoS-blocked connection"""
        print(f"DDOS BLOCKED: Connection from {remote_ip}:{remote_port} to local port {local_port}")
        firewall.log_connection(remote_ip, "DDOS_BLOCK", f"Blocked DDoS connection to port {local_port}")
        # In a real implementation, you would actually block the connection here
        
    def _handle_access_request(self, remote_ip, local_port, conn):
        """Handle a connection that requires access approval"""
        # Check if there's already a pending request for this IP and port
        existing_request = None
        for req_id, req in firewall.access_requests.items():
            if req["ip"] == remote_ip and req["port"] == local_port and req["approved"] is None:
                # Check if request is still valid (not expired)
                if datetime.now() - req["timestamp"] <= timedelta(minutes=10):
                    existing_request = req_id
                    break
                    
        if not existing_request:
            # Create a new access request
            request_id = firewall.request_access(remote_ip, local_port)
            print(f"ACCESS REQUEST: New request {request_id} from {remote_ip} for port {local_port}")
            firewall.log_connection(remote_ip, "REQUEST", f"Access request for port {local_port}")
        else:
            print(f"ACCESS REQUEST: Existing request {existing_request} from {remote_ip} for port {local_port}")
            
    def _handle_suspicious_activity(self, remote_ip, local_port, conn):
        """Handle suspicious network activity"""
        firewall.log_connection(remote_ip, "SUSPICIOUS", f"Suspicious activity detected on port {local_port}")
        print(f"SUSPICIOUS: Activity from {remote_ip} on port {local_port}")
        
    def _log_allowed_connection(self, remote_ip, remote_port, local_port, conn):
        """Log an allowed connection"""
        # For performance reasons, we don't log every allowed connection
        # But we can log some for monitoring purposes
        critical_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432, 8080]
        if local_port in critical_ports:
            firewall.log_connection(remote_ip, "ALLOW", f"Allowed connection to port {local_port}")
        
    def get_active_connections(self):
        """Get a list of active connections"""
        try:
            connections = psutil.net_connections(kind='inet')
            active_conns = []
            
            for conn in connections:
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    # Handle local address properly
                    if hasattr(conn.laddr, '__len__') and len(conn.laddr) > 1:
                        local_ip = conn.laddr[0]
                        local_port = conn.laddr[1]
                    else:
                        # Fallback for different psutil versions
                        local_ip = getattr(conn.laddr, 'ip', 'Unknown')
                        local_port = getattr(conn.laddr, 'port', 0)
                        
                    active_conns.append({
                        'local_ip': local_ip,
                        'local_port': local_port,
                        'remote_ip': conn.raddr[0],
                        'remote_port': conn.raddr[1],
                        'status': conn.status
                    })
                    
            return active_conns
        except Exception as e:
            print(f"Error getting active connections: {e}")
            return []
            
    def get_network_stats(self):
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }
        except Exception as e:
            print(f"Error getting network stats: {e}")
            return {}
            
    def scan_for_malicious_processes(self):
        """Scan for potentially malicious processes"""
        suspicious_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ''
                    
                    # Check against suspicious patterns
                    for pattern in self.suspicious_patterns:
                        if re.match(pattern, name) or re.match(pattern, cmdline):
                            suspicious_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline
                            })
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process might have terminated or we don't have access
                    continue
        except Exception as e:
            print(f"Error scanning for malicious processes: {e}")
            
        return suspicious_processes

# Global network monitor instance
network_monitor = NetworkMonitor()

if __name__ == "__main__":
    # Example usage
    monitor = NetworkMonitor()
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(10)
            stats = monitor.get_network_stats()
            print(f"Network Stats: {stats}")
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("Monitoring stopped")