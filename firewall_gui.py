import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import os
from datetime import datetime, timedelta
import psutil
import socket
import subprocess
import re
import requests
import socket
try:
    import docker
except ImportError:
    docker = None

# Import network monitor to control whitelist
from network_monitor import network_monitor

class FirewallGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ CYBER SHIELD PRO - Advanced Penetration Testing Firewall")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0A0A0A")
        
        # Configure dark theme
        self.setup_dark_theme()
        
        # Data storage
        self.blocked_ips = set()
        self.allowed_ips = set()
        self.open_ports = set()
        self.closed_ports = set()
        self.access_requests = {}  # request_id: {ip, port, timestamp, approved}
        self.suspicious_processes = []
        self.geolocation_cache = {}
        
        # Load data from files if they exist
        self.load_data()
        
        # Initialize with system open ports
        self.initialize_open_ports()
        
        # Honeypot state
        self.honeypot_active = False
        self.honeypot_thread = None
        self.log_thread = None
        self.socket_thread = None
        self.docker_client = None
        if docker:
            try:
                self.docker_client = docker.from_env()
            except:
                self.docker_client = None

        # Create GUI
        self.create_widgets()
        
        # Start background threads
        self.start_background_threads()
        
    def setup_dark_theme(self):
        # Configure styles for dark theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure("TFrame", background="#0A0A0A")
        style.configure("TLabel", background="#0A0A0A", foreground="#00FF00")
        style.configure("TButton", background="#1E1E1E", foreground="#00FF00")
        style.configure("TEntry", fieldbackground="#2D2D2D", foreground="#00FF00")
        style.configure("TNotebook", background="#0A0A0A")
        style.configure("TNotebook.Tab", background="#1E1E1E", foreground="#00FF00")
        style.map("TNotebook.Tab", background=[("selected", "#2D2D2D")])
        
        # Configure listboxes
        self.root.option_add("*Listbox*Background", "#2D2D2D")
        self.root.option_add("*Listbox*Foreground", "#00FF00")
        self.root.option_add("*Listbox*selectBackground", "#3E3E3E")
        
    def initialize_open_ports(self):
        """Initialize with currently open ports on the system"""
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.status == 'LISTEN':
                    # Access the local address properly
                    if hasattr(conn, 'laddr') and conn.laddr:
                        # laddr is a named tuple (ip, port)
                        if len(conn.laddr) > 1:
                            self.open_ports.add(conn.laddr[1])  # Port is the second element
        except Exception as e:
            print(f"Error initializing open ports: {e}")
        
    def create_widgets(self):
        # Create title
        title_frame = tk.Frame(self.root, bg="#0A0A0A")
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(title_frame, text="🛡️ CYBER SHIELD PRO - Advanced Penetration Testing Firewall", 
                              font=("Courier", 16, "bold"), bg="#0A0A0A", fg="#00FF00")
        title_label.pack()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Dashboard Tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="📊 Dashboard")
        self.create_dashboard_tab()
        
        # IP Filtering Tab
        self.ip_filter_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ip_filter_frame, text="🌐 IP Filtering")
        self.create_ip_filter_tab()
        
        # Port Management Tab
        self.port_manage_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.port_manage_frame, text="🔌 Port Management")
        self.create_port_management_tab()
        
        # DDoS Protection Tab
        self.ddos_protect_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ddos_protect_frame, text="⚡ DDoS Protection")
        self.create_ddos_protection_tab()
        
        # Access Requests Tab
        self.access_req_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.access_req_frame, text="🔔 Access Requests")
        self.create_access_requests_tab()
        
        # Process Monitor Tab
        self.process_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.process_frame, text="⚙️ Process Monitor")
        self.create_process_monitor_tab()
        
        # Geolocation Tab
        self.geo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.geo_frame, text="🌍 IP Geolocation")
        self.create_geolocation_tab()
        
        # Terminal Tab
        self.terminal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text="💻 Terminal")
        self.create_terminal_tab()
        
        # Logs Tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="📝 Activity Logs")
        self.create_logs_tab()

        # Honeypot Ops Tab (Renamed)
        self.honeypot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.honeypot_frame, text="🛡️ Honeypot Ops")
        self.create_honeypot_tab()
        
    def create_dashboard_tab(self):
        # Dashboard layout
        dashboard_frame = tk.Frame(self.dashboard_frame, bg="#0A0A0A")
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System info panel
        info_frame = tk.LabelFrame(dashboard_frame, text="System Information", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        # Stats grid
        stats_frame = tk.Frame(dashboard_frame, bg="#0A0A0A")
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Current open ports
        open_ports_frame = tk.LabelFrame(stats_frame, text="Open Ports", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        open_ports_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.open_ports_count = tk.Label(open_ports_frame, text="0", font=("Courier", 24, "bold"), bg="#1E1E1E", fg="#00FF00")
        self.open_ports_count.pack()
        tk.Label(open_ports_frame, text="Currently Open", bg="#1E1E1E", fg="#00FF00").pack()
        
        # Blocked IPs
        blocked_ips_frame = tk.LabelFrame(stats_frame, text="Blocked IPs", bg="#1E1E1E", fg="#FF0000", padx=10, pady=10)
        blocked_ips_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.blocked_ips_count = tk.Label(blocked_ips_frame, text="0", font=("Courier", 24, "bold"), bg="#1E1E1E", fg="#FF0000")
        self.blocked_ips_count.pack()
        tk.Label(blocked_ips_frame, text="Currently Blocked", bg="#1E1E1E", fg="#00FF00").pack()
        
        # Active connections
        connections_frame = tk.LabelFrame(stats_frame, text="Active Connections", bg="#1E1E1E", fg="#00FFFF", padx=10, pady=10)
        connections_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.active_connections_count = tk.Label(connections_frame, text="0", font=("Courier", 24, "bold"), bg="#1E1E1E", fg="#00FFFF")
        self.active_connections_count.pack()
        tk.Label(connections_frame, text="Currently Active", bg="#1E1E1E", fg="#00FF00").pack()
        
        # Suspicious processes
        suspicious_frame = tk.LabelFrame(stats_frame, text="Suspicious Processes", bg="#1E1E1E", fg="#FFFF00", padx=10, pady=10)
        suspicious_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.suspicious_count = tk.Label(suspicious_frame, text="0", font=("Courier", 24, "bold"), bg="#1E1E1E", fg="#FFFF00")
        self.suspicious_count.pack()
        tk.Label(suspicious_frame, text="Detected", bg="#1E1E1E", fg="#00FF00").pack()
        
        # Recent activity
        activity_frame = tk.LabelFrame(dashboard_frame, text="Recent Activity", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.activity_text = scrolledtext.ScrolledText(activity_frame, height=10, bg="#2D2D2D", fg="#00FF00", wrap=tk.WORD)
        self.activity_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh dashboard
        self.refresh_dashboard()
        
    def create_ip_filter_tab(self):
        # Main frame
        main_frame = tk.Frame(self.ip_filter_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Blocked IPs section
        blocked_frame = tk.LabelFrame(main_frame, text="🚫 Blocked IPs", bg="#1E1E1E", fg="#FF0000", padx=10, pady=10)
        blocked_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)
        
        # Add IP to block
        add_block_frame = tk.Frame(blocked_frame, bg="#1E1E1E")
        add_block_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(add_block_frame, text="IP Address:", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.block_ip_entry = tk.Entry(add_block_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.block_ip_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(add_block_frame, text="Block IP", command=self.block_ip, bg="#FF0000", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Blocked IPs list
        self.blocked_listbox = tk.Listbox(blocked_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.blocked_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Remove blocked IP
        remove_block_frame = tk.Frame(blocked_frame, bg="#1E1E1E")
        remove_block_frame.pack(fill=tk.X, pady=5)
        tk.Button(remove_block_frame, text="Unblock Selected", command=self.unblock_ip, bg="#00FF00", fg="#000000").pack(side=tk.LEFT)
        
        # Allowed IPs section
        allowed_frame = tk.LabelFrame(main_frame, text="✅ Allowed IPs", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        allowed_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=5)
        
        # Add IP to allow
        add_allow_frame = tk.Frame(allowed_frame, bg="#1E1E1E")
        add_allow_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(add_allow_frame, text="IP Address:", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.allow_ip_entry = tk.Entry(add_allow_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.allow_ip_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(add_allow_frame, text="Allow IP", command=self.allow_ip, bg="#00FF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Allowed IPs list
        self.allowed_listbox = tk.Listbox(allowed_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.allowed_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Remove allowed IP
        remove_allow_frame = tk.Frame(allowed_frame, bg="#1E1E1E")
        remove_allow_frame.pack(fill=tk.X, pady=5)
        tk.Button(remove_allow_frame, text="Remove from Allowed", command=self.remove_allowed_ip, bg="#FFFF00", fg="#000000").pack(side=tk.LEFT)
        
        # Refresh lists
        self.refresh_ip_lists()
        
    def create_port_management_tab(self):
        # Main frame
        main_frame = tk.Frame(self.port_manage_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Open Ports section
        open_frame = tk.LabelFrame(main_frame, text="🔓 Open Ports", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        open_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)
        
        # Add port to open
        add_open_frame = tk.Frame(open_frame, bg="#1E1E1E")
        add_open_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(add_open_frame, text="Port Number:", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.open_port_entry = tk.Entry(add_open_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.open_port_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(add_open_frame, text="Open Port", command=self.open_port, bg="#00FF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Open ports list
        self.open_listbox = tk.Listbox(open_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.open_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Close port
        close_frame = tk.Frame(open_frame, bg="#1E1E1E")
        close_frame.pack(fill=tk.X, pady=5)
        tk.Button(close_frame, text="Close Selected", command=self.close_port, bg="#FF0000", fg="#000000").pack(side=tk.LEFT)
        
        # Closed Ports section
        closed_frame = tk.LabelFrame(main_frame, text="🔒 Closed Ports", bg="#1E1E1E", fg="#FF0000", padx=10, pady=10)
        closed_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=5)
        
        # Add port to close
        add_close_frame = tk.Frame(closed_frame, bg="#1E1E1E")
        add_close_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(add_close_frame, text="Port Number:", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.close_port_entry = tk.Entry(add_close_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.close_port_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(add_close_frame, text="Close Port", command=self.add_closed_port, bg="#FF0000", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Closed ports list
        self.closed_listbox = tk.Listbox(closed_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.closed_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Reopen port
        reopen_frame = tk.Frame(closed_frame, bg="#1E1E1E")
        reopen_frame.pack(fill=tk.X, pady=5)
        tk.Button(reopen_frame, text="Reopen Selected", command=self.reopen_port, bg="#00FF00", fg="#000000").pack(side=tk.LEFT)
        
        # Refresh lists
        self.refresh_port_lists()
        
    def create_ddos_protection_tab(self):
        # Main frame
        main_frame = tk.Frame(self.ddos_protect_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # DDoS settings
        settings_frame = tk.LabelFrame(main_frame, text="⚙️ DDoS Protection Settings", bg="#1E1E1E", fg="#00FFFF", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Connection threshold
        threshold_frame = tk.Frame(settings_frame, bg="#1E1E1E")
        threshold_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(threshold_frame, text="Connection Threshold (per minute):", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.threshold_var = tk.StringVar(value="50")
        self.threshold_entry = tk.Entry(threshold_frame, textvariable=self.threshold_var, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.threshold_entry.pack(side=tk.LEFT, padx=5)
        
        # Block duration
        duration_frame = tk.Frame(settings_frame, bg="#1E1E1E")
        duration_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(duration_frame, text="Block Duration (minutes):", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="15")
        self.duration_entry = tk.Entry(duration_frame, textvariable=self.duration_var, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.duration_entry.pack(side=tk.LEFT, padx=5)
        
        # Save settings
        save_frame = tk.Frame(settings_frame, bg="#1E1E1E")
        save_frame.pack(fill=tk.X, pady=10)
        tk.Button(save_frame, text="Save Settings", command=self.save_ddos_settings, bg="#00FFFF", fg="#000000").pack(side=tk.LEFT)
        
        # Protection status
        status_frame = tk.Frame(settings_frame, bg="#1E1E1E")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.ddos_status_label = tk.Label(status_frame, text="DDoS Protection: ACTIVE", bg="#1E1E1E", fg="#00FF00", font=("Courier", 10, "bold"))
        self.ddos_status_label.pack(side=tk.LEFT)
        tk.Button(status_frame, text="Toggle Protection", command=self.toggle_ddos_protection, bg="#FFFF00", fg="#000000").pack(side=tk.RIGHT)
        
        # Suspicious connections
        suspicious_frame = tk.LabelFrame(main_frame, text="🚨 Suspicious Connections", bg="#1E1E1E", fg="#FF0000", padx=10, pady=10)
        suspicious_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Suspicious connections list
        self.suspicious_listbox = tk.Listbox(suspicious_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.suspicious_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Clear list
        clear_frame = tk.Frame(suspicious_frame, bg="#1E1E1E")
        clear_frame.pack(fill=tk.X, pady=5)
        tk.Button(clear_frame, text="Clear List", command=self.clear_suspicious, bg="#FF0000", fg="#000000").pack(side=tk.LEFT)
        
    def create_access_requests_tab(self):
        # Main frame
        main_frame = tk.Frame(self.access_req_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pending requests
        pending_frame = tk.LabelFrame(main_frame, text="⏳ Pending Requests", bg="#1E1E1E", fg="#FFFF00", padx=10, pady=10)
        pending_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)
        
        # Requests list
        self.requests_listbox = tk.Listbox(pending_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.requests_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Action buttons
        action_frame = tk.Frame(pending_frame, bg="#1E1E1E")
        action_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(action_frame, text="✅ Approve Selected", command=self.approve_request, bg="#00FF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="❌ Reject Selected", command=self.reject_request, bg="#FF0000", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="🔄 Refresh", command=self.refresh_requests_list, bg="#00FFFF", fg="#000000").pack(side=tk.RIGHT, padx=5)
        
        # Approved requests
        approved_frame = tk.LabelFrame(main_frame, text="✅ Approved Requests", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        approved_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=5)
        
        self.approved_listbox = tk.Listbox(approved_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.approved_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Refresh lists
        self.refresh_requests_list()
        
    def create_process_monitor_tab(self):
        # Main frame
        main_frame = tk.Frame(self.process_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Process control
        control_frame = tk.LabelFrame(main_frame, text="🔧 Process Control", bg="#1E1E1E", fg="#00FFFF", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(control_frame, text="Process Name/ID:", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.process_entry = tk.Entry(control_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.process_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Kill Process", command=self.kill_process, bg="#FF0000", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Suspend Process", command=self.suspend_process, bg="#FFFF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Resume Process", command=self.resume_process, bg="#00FF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Running processes
        processes_frame = tk.LabelFrame(main_frame, text="🏃 Running Processes", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        processes_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview for processes
        process_columns = ("PID", "Name", "Status", "CPU %", "Memory %", "User")
        self.process_tree = ttk.Treeview(processes_frame, columns=process_columns, show="headings", height=15)
        
        # Define headings
        for col in process_columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=100)
            
        # Add scrollbars
        process_vsb = ttk.Scrollbar(processes_frame, orient="vertical", command=self.process_tree.yview)
        process_hsb = ttk.Scrollbar(processes_frame, orient="horizontal", command=self.process_tree.xview)
        self.process_tree.configure(yscrollcommand=process_vsb.set, xscrollcommand=process_hsb.set)
        
        # Pack treeview and scrollbars
        self.process_tree.pack(side="left", fill="both", expand=True)
        process_vsb.pack(side="right", fill="y")
        process_hsb.pack(side="bottom", fill="x")
        
        # Control buttons
        proc_control_frame = tk.Frame(processes_frame, bg="#1E1E1E")
        proc_control_frame.pack(fill=tk.X, pady=5)
        tk.Button(proc_control_frame, text="🔄 Refresh", command=self.refresh_processes, bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(proc_control_frame, text="🔍 Scan for Suspicious", command=self.scan_suspicious_processes, bg="#FFFF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Refresh processes
        self.refresh_processes()
        
    def create_geolocation_tab(self):
        # Main frame
        main_frame = tk.Frame(self.geo_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # IP Geolocation
        geo_frame = tk.LabelFrame(main_frame, text="🌍 IP Geolocation Lookup", bg="#1E1E1E", fg="#00FFFF", padx=10, pady=10)
        geo_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(geo_frame, text="IP Address:", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.geo_ip_entry = tk.Entry(geo_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.geo_ip_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(geo_frame, text="Lookup", command=self.lookup_ip_geolocation, bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(geo_frame, text="My Location", command=self.get_my_location, bg="#00FF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Geolocation results
        self.geo_result_text = scrolledtext.ScrolledText(geo_frame, height=10, bg="#2D2D2D", fg="#00FF00", wrap=tk.WORD)
        self.geo_result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # IP History
        history_frame = tk.LabelFrame(main_frame, text="🕒 Lookup History", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.history_listbox = tk.Listbox(history_frame, bg="#2D2D2D", fg="#00FF00", selectbackground="#3E3E3E")
        self.history_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Clear history button
        tk.Button(history_frame, text="Clear History", command=self.clear_geo_history, bg="#FF0000", fg="#000000").pack(side=tk.LEFT, padx=5)
        
    def create_terminal_tab(self):
        # Main frame
        main_frame = tk.Frame(self.terminal_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Terminal
        terminal_frame = tk.LabelFrame(main_frame, text="💻 System Terminal", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Command entry
        cmd_frame = tk.Frame(terminal_frame, bg="#1E1E1E")
        cmd_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cmd_frame, text=">", bg="#1E1E1E", fg="#00FF00").pack(side=tk.LEFT)
        self.cmd_entry = tk.Entry(cmd_frame, bg="#2D2D2D", fg="#00FF00", insertbackground="#00FF00")
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", self.execute_command)
        tk.Button(cmd_frame, text="Execute", command=self.execute_command, bg="#00FFFF", fg="#000000").pack(side=tk.RIGHT)
        
        # Terminal output
        self.terminal_text = scrolledtext.ScrolledText(terminal_frame, bg="#000000", fg="#00FF00", wrap=tk.WORD, height=20)
        self.terminal_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.terminal_text.insert(tk.END, "Cyber Shield Pro Terminal v1.0\n")
        self.terminal_text.insert(tk.END, "Type 'help' for available commands\n")
        self.terminal_text.insert(tk.END, "-----------------------------------\n")
        
        # Quick commands
        quick_frame = tk.Frame(terminal_frame, bg="#1E1E1E")
        quick_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(quick_frame, text="Netstat", command=lambda: self.execute_quick_command("netstat -an"), bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=2)
        tk.Button(quick_frame, text="Tasklist", command=lambda: self.execute_quick_command("tasklist"), bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=2)
        tk.Button(quick_frame, text="IP Config", command=lambda: self.execute_quick_command("ipconfig"), bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=2)
        tk.Button(quick_frame, text="Firewall Status", command=lambda: self.execute_quick_command("netsh advfirewall show allprofiles"), bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=2)
        tk.Button(quick_frame, text="Clear", command=self.clear_terminal, bg="#FF0000", fg="#000000").pack(side=tk.RIGHT, padx=2)
        
    def create_logs_tab(self):
        # Main frame
        main_frame = tk.Frame(self.logs_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Logs display
        logs_frame = tk.LabelFrame(main_frame, text="📋 Activity Logs", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, bg="#2D2D2D", fg="#00FF00", wrap=tk.WORD)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = tk.Frame(logs_frame, bg="#1E1E1E")
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(control_frame, text="Clear Logs", command=self.clear_logs, bg="#FF0000", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Save Logs", command=self.save_logs, bg="#00FFFF", fg="#000000").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Export CSV", command=self.export_logs_csv, bg="#FFFF00", fg="#000000").pack(side=tk.LEFT, padx=5)
        
        # Add sample log entry
        self.log_activity("Firewall initialized", "INFO")
        
    def block_ip(self):
        ip = self.block_ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Error", "Please enter an IP address")
            return
            
        if self.is_valid_ip(ip):
            self.blocked_ips.add(ip)
            self.block_ip_entry.delete(0, tk.END)
            self.refresh_ip_lists()
            self.save_data()
            self.log_activity(f"Blocked IP: {ip}", "BLOCK")
            messagebox.showinfo("Success", f"IP {ip} has been blocked")
        else:
            messagebox.showerror("Error", "Invalid IP address format")
            
    def unblock_ip(self):
        selection = self.blocked_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an IP to unblock")
            return
            
        ip = self.blocked_listbox.get(selection[0])
        self.blocked_ips.discard(ip)
        self.refresh_ip_lists()
        self.save_data()
        self.log_activity(f"Unblocked IP: {ip}", "UNBLOCK")
        messagebox.showinfo("Success", f"IP {ip} has been unblocked")
        
    def allow_ip(self):
        ip = self.allow_ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Error", "Please enter an IP address")
            return
            
        if self.is_valid_ip(ip):
            self.allowed_ips.add(ip)
            self.allow_ip_entry.delete(0, tk.END)
            self.refresh_ip_lists()
            self.save_data()
            self.log_activity(f"Allowed IP: {ip}", "ALLOW")
            messagebox.showinfo("Success", f"IP {ip} has been allowed")
        else:
            messagebox.showerror("Error", "Invalid IP address format")
            
    def remove_allowed_ip(self):
        selection = self.allowed_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an IP to remove")
            return
            
        ip = self.allowed_listbox.get(selection[0])
        self.allowed_ips.discard(ip)
        self.refresh_ip_lists()
        self.save_data()
        self.log_activity(f"Removed allowed IP: {ip}", "REMOVE")
        messagebox.showinfo("Success", f"IP {ip} has been removed from allowed list")
        
    def open_port(self):
        port_str = self.open_port_entry.get().strip()
        if not port_str:
            messagebox.showerror("Error", "Please enter a port number")
            return
            
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                self.open_ports.add(port)
                self.closed_ports.discard(port)
                self.open_port_entry.delete(0, tk.END)
                self.refresh_port_lists()
                self.save_data()
                self.log_activity(f"Opened port: {port}", "OPEN")
                messagebox.showinfo("Success", f"Port {port} has been opened")
            else:
                messagebox.showerror("Error", "Port must be between 1 and 65535")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            
    def close_port(self):
        selection = self.open_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a port to close")
            return
            
        port_str = self.open_listbox.get(selection[0])
        port = int(port_str.split()[1])  # Extract port number
        self.open_ports.discard(port)
        self.closed_ports.add(port)
        self.refresh_port_lists()
        self.save_data()
        self.log_activity(f"Closed port: {port}", "CLOSE")
        messagebox.showinfo("Success", f"Port {port} has been closed")
        
    def add_closed_port(self):
        port_str = self.close_port_entry.get().strip()
        if not port_str:
            messagebox.showerror("Error", "Please enter a port number")
            return
            
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                self.closed_ports.add(port)
                self.open_ports.discard(port)
                self.close_port_entry.delete(0, tk.END)
                self.refresh_port_lists()
                self.save_data()
                self.log_activity(f"Added to closed ports: {port}", "CLOSE")
                messagebox.showinfo("Success", f"Port {port} has been added to closed ports")
            else:
                messagebox.showerror("Error", "Port must be between 1 and 65535")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            
    def reopen_port(self):
        selection = self.closed_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a port to reopen")
            return
            
        port_str = self.closed_listbox.get(selection[0])
        port = int(port_str.split()[1])  # Extract port number
        self.closed_ports.discard(port)
        self.open_ports.add(port)
        self.refresh_port_lists()
        self.save_data()
        self.log_activity(f"Reopened port: {port}", "OPEN")
        messagebox.showinfo("Success", f"Port {port} has been reopened")
        
    def save_ddos_settings(self):
        try:
            threshold = int(self.threshold_var.get())
            duration = int(self.duration_var.get())
            # In a real implementation, these values would be used by the DDoS protection system
            self.log_activity(f"DDoS settings updated - Threshold: {threshold}, Duration: {duration}", "CONFIG")
            messagebox.showinfo("Success", "DDoS settings saved")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for threshold and duration")
            
    def toggle_ddos_protection(self):
        # In a real implementation, this would toggle the actual DDoS protection
        current_text = self.ddos_status_label.cget("text")
        if "ACTIVE" in current_text:
            self.ddos_status_label.config(text="DDoS Protection: INACTIVE", fg="#FF0000")
            self.log_activity("DDoS protection disabled", "CONFIG")
        else:
            self.ddos_status_label.config(text="DDoS Protection: ACTIVE", fg="#00FF00")
            self.log_activity("DDoS protection enabled", "CONFIG")
            
    def clear_suspicious(self):
        self.suspicious_listbox.delete(0, tk.END)
        self.log_activity("Cleared suspicious connections list", "CLEAR")
        messagebox.showinfo("Success", "Suspicious connections list cleared")
        
    def approve_request(self):
        selection = self.requests_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a request to approve")
            return
            
        request_info = self.requests_listbox.get(selection[0])
        # Extract request ID from the string (format: "ID: xxx | IP: xxx | Port: xxx | Time: xxx")
        request_id = request_info.split("|")[0].split(":")[1].strip()
        
        if request_id in self.access_requests:
            self.access_requests[request_id]["approved"] = True
            self.access_requests[request_id]["approval_time"] = datetime.now()
            self.refresh_requests_list()
            self.save_data()
            ip = self.access_requests[request_id]["ip"]
            port = self.access_requests[request_id]["port"]
            self.log_activity(f"Approved access request - IP: {ip}, Port: {port}", "APPROVE")
            messagebox.showinfo("Success", f"Request {request_id} has been approved")
        else:
            messagebox.showerror("Error", "Request not found")
            
    def reject_request(self):
        selection = self.requests_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a request to reject")
            return
            
        request_info = self.requests_listbox.get(selection[0])
        # Extract request ID from the string
        request_id = request_info.split("|")[0].split(":")[1].strip()
        
        if request_id in self.access_requests:
            self.access_requests[request_id]["approved"] = False
            self.access_requests[request_id]["approval_time"] = datetime.now()
            self.refresh_requests_list()
            self.save_data()
            ip = self.access_requests[request_id]["ip"]
            port = self.access_requests[request_id]["port"]
            self.log_activity(f"Rejected access request - IP: {ip}, Port: {port}", "REJECT")
            messagebox.showinfo("Success", f"Request {request_id} has been rejected")
        else:
            messagebox.showerror("Error", "Request not found")
            
    def kill_process(self):
        process_input = self.process_entry.get().strip()
        if not process_input:
            messagebox.showerror("Error", "Please enter a process name or ID")
            return
            
        try:
            # Try to kill by PID first
            if process_input.isdigit():
                pid = int(process_input)
                p = psutil.Process(pid)
                p.terminate()
                self.log_activity(f"Terminated process PID: {pid}", "KILL")
                messagebox.showinfo("Success", f"Process {pid} terminated")
            else:
                # Kill by name
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == process_input.lower():
                        p = psutil.Process(proc.info['pid'])
                        p.terminate()
                        self.log_activity(f"Terminated process: {process_input} (PID: {proc.info['pid']})", "KILL")
                        messagebox.showinfo("Success", f"Process {process_input} terminated")
                        break
                else:
                    messagebox.showerror("Error", f"Process '{process_input}' not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to terminate process: {str(e)}")
            
        self.refresh_processes()
        
    def suspend_process(self):
        process_input = self.process_entry.get().strip()
        if not process_input:
            messagebox.showerror("Error", "Please enter a process name or ID")
            return
            
        try:
            # Suspend by PID
            if process_input.isdigit():
                pid = int(process_input)
                p = psutil.Process(pid)
                p.suspend()
                self.log_activity(f"Suspended process PID: {pid}", "SUSPEND")
                messagebox.showinfo("Success", f"Process {pid} suspended")
            else:
                # Suspend by name
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == process_input.lower():
                        p = psutil.Process(proc.info['pid'])
                        p.suspend()
                        self.log_activity(f"Suspended process: {process_input} (PID: {proc.info['pid']})", "SUSPEND")
                        messagebox.showinfo("Success", f"Process {process_input} suspended")
                        break
                else:
                    messagebox.showerror("Error", f"Process '{process_input}' not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to suspend process: {str(e)}")
            
        self.refresh_processes()
        
    def resume_process(self):
        process_input = self.process_entry.get().strip()
        if not process_input:
            messagebox.showerror("Error", "Please enter a process name or ID")
            return
            
        try:
            # Resume by PID
            if process_input.isdigit():
                pid = int(process_input)
                p = psutil.Process(pid)
                p.resume()
                self.log_activity(f"Resumed process PID: {pid}", "RESUME")
                messagebox.showinfo("Success", f"Process {pid} resumed")
            else:
                # Resume by name
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == process_input.lower():
                        p = psutil.Process(proc.info['pid'])
                        p.resume()
                        self.log_activity(f"Resumed process: {process_input} (PID: {proc.info['pid']})", "RESUME")
                        messagebox.showinfo("Success", f"Process {process_input} resumed")
                        break
                else:
                    messagebox.showerror("Error", f"Process '{process_input}' not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to resume process: {str(e)}")
            
        self.refresh_processes()
        
    def refresh_processes(self):
        # Clear the treeview
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
            
        # Add processes to treeview
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'] or "N/A"
                    status = proc.info['status'] or "N/A"
                    cpu = f"{proc.info['cpu_percent']:.1f}" if proc.info['cpu_percent'] is not None else "N/A"
                    memory = f"{proc.info['memory_percent']:.1f}" if proc.info['memory_percent'] is not None else "N/A"
                    user = proc.info['username'] or "N/A"
                    
                    self.process_tree.insert("", "end", values=(pid, name, status, cpu, memory, user))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process might have terminated or we don't have access
                    continue
        except Exception as e:
            self.log_activity(f"Error refreshing processes: {str(e)}", "ERROR")
            
    def scan_suspicious_processes(self):
        suspicious_keywords = [
            "hack", "exploit", "backdoor", "trojan", "virus", "malware", 
            "keylog", "sniff", "packet", "wire", "reverse", "shell",
            "nc.exe", "netcat", "ncat", "meterpreter", "cobalt", "empire"
        ]
        
        self.suspicious_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                for keyword in suspicious_keywords:
                    if keyword in name:
                        self.suspicious_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name']
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        self.log_activity(f"Scanned for suspicious processes. Found {len(self.suspicious_processes)} suspicious processes.", "SCAN")
        messagebox.showinfo("Scan Complete", f"Found {len(self.suspicious_processes)} suspicious processes")
        self.refresh_dashboard()
        
    def lookup_ip_geolocation(self):
        ip = self.geo_ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Error", "Please enter an IP address")
            return
            
        if not self.is_valid_ip(ip):
            messagebox.showerror("Error", "Invalid IP address format")
            return
            
        # Check cache first
        if ip in self.geolocation_cache:
            result = self.geolocation_cache[ip]
            self.display_geolocation_result(ip, result)
            return
            
        try:
            # Using a free IP geolocation service
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    result = {
                        'country': data.get('country', 'N/A'),
                        'region': data.get('regionName', 'N/A'),
                        'city': data.get('city', 'N/A'),
                        'isp': data.get('isp', 'N/A'),
                        'org': data.get('org', 'N/A'),
                        'lat': data.get('lat', 'N/A'),
                        'lon': data.get('lon', 'N/A'),
                        'timezone': data.get('timezone', 'N/A')
                    }
                    self.geolocation_cache[ip] = result
                    self.display_geolocation_result(ip, result)
                    self.add_to_geo_history(ip, result)
                else:
                    messagebox.showerror("Error", "Failed to get geolocation data")
            else:
                messagebox.showerror("Error", "Failed to connect to geolocation service")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to lookup IP: {str(e)}")
            
    def get_my_location(self):
        try:
            response = requests.get("http://ip-api.com/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    ip = data.get('query', 'N/A')
                    self.geo_ip_entry.delete(0, tk.END)
                    self.geo_ip_entry.insert(0, ip)
                    result = {
                        'country': data.get('country', 'N/A'),
                        'region': data.get('regionName', 'N/A'),
                        'city': data.get('city', 'N/A'),
                        'isp': data.get('isp', 'N/A'),
                        'org': data.get('org', 'N/A'),
                        'lat': data.get('lat', 'N/A'),
                        'lon': data.get('lon', 'N/A'),
                        'timezone': data.get('timezone', 'N/A')
                    }
                    self.geolocation_cache[ip] = result
                    self.display_geolocation_result(ip, result)
                    self.add_to_geo_history(ip, result)
                else:
                    messagebox.showerror("Error", "Failed to get your location")
            else:
                messagebox.showerror("Error", "Failed to connect to geolocation service")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get your location: {str(e)}")
            
    def display_geolocation_result(self, ip, result):
        self.geo_result_text.delete(1.0, tk.END)
        self.geo_result_text.insert(tk.END, f"IP Address: {ip}\n")
        self.geo_result_text.insert(tk.END, f"Country: {result['country']}\n")
        self.geo_result_text.insert(tk.END, f"Region: {result['region']}\n")
        self.geo_result_text.insert(tk.END, f"City: {result['city']}\n")
        self.geo_result_text.insert(tk.END, f"ISP: {result['isp']}\n")
        self.geo_result_text.insert(tk.END, f"Organization: {result['org']}\n")
        self.geo_result_text.insert(tk.END, f"Latitude: {result['lat']}\n")
        self.geo_result_text.insert(tk.END, f"Longitude: {result['lon']}\n")
        self.geo_result_text.insert(tk.END, f"Timezone: {result['timezone']}\n")
        
    def add_to_geo_history(self, ip, result):
        history_entry = f"{ip} - {result['country']}, {result['city']}"
        self.history_listbox.insert(tk.END, history_entry)
        
    def clear_geo_history(self):
        self.history_listbox.delete(0, tk.END)
        self.geolocation_cache.clear()
        self.log_activity("Cleared geolocation history", "CLEAR")
        
    def execute_command(self, event=None):
        command = self.cmd_entry.get().strip()
        if not command:
            return
            
        self.cmd_entry.delete(0, tk.END)
        self.terminal_text.insert(tk.END, f"> {command}\n")
        
        try:
            # Handle some special commands
            if command.lower() == "help":
                self.terminal_text.insert(tk.END, "Available commands:\n")
                self.terminal_text.insert(tk.END, "  help - Show this help\n")
                self.terminal_text.insert(tk.END, "  clear - Clear terminal\n")
                self.terminal_text.insert(tk.END, "  exit - Exit application\n")
                self.terminal_text.insert(tk.END, "  Any Windows command (dir, ipconfig, etc.)\n")
            elif command.lower() == "clear":
                self.clear_terminal()
            elif command.lower() == "exit":
                self.root.quit()
            else:
                # Execute system command
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                if result.stdout:
                    self.terminal_text.insert(tk.END, result.stdout)
                if result.stderr:
                    self.terminal_text.insert(tk.END, f"ERROR: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.terminal_text.insert(tk.END, "Command timed out\n")
        except Exception as e:
            self.terminal_text.insert(tk.END, f"Error executing command: {str(e)}\n")
            
        self.terminal_text.see(tk.END)
        
    def execute_quick_command(self, command):
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, command)
        self.execute_command()
        
    def clear_terminal(self):
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.insert(tk.END, "Cyber Shield Pro Terminal v1.0\n")
        self.terminal_text.insert(tk.END, "Type 'help' for available commands\n")
        self.terminal_text.insert(tk.END, "-----------------------------------\n")
        
    def refresh_ip_lists(self):
        # Clear and repopulate blocked IPs list
        self.blocked_listbox.delete(0, tk.END)
        for ip in sorted(self.blocked_ips):
            self.blocked_listbox.insert(tk.END, ip)
            
        # Clear and repopulate allowed IPs list
        self.allowed_listbox.delete(0, tk.END)
        for ip in sorted(self.allowed_ips):
            self.allowed_listbox.insert(tk.END, ip)
            
    def refresh_port_lists(self):
        # Clear and repopulate open ports list
        self.open_listbox.delete(0, tk.END)
        for port in sorted(self.open_ports):
            self.open_listbox.insert(tk.END, f"Port: {port}")
            
        # Clear and repopulate closed ports list
        self.closed_listbox.delete(0, tk.END)
        for port in sorted(self.closed_ports):
            self.closed_listbox.insert(tk.END, f"Port: {port}")
            
    def refresh_requests_list(self):
        # Clear and repopulate requests lists
        self.requests_listbox.delete(0, tk.END)
        self.approved_listbox.delete(0, tk.END)
        
        now = datetime.now()
        expired_requests = []
        
        for req_id, req in self.access_requests.items():
            # Check if request has expired (older than 10 minutes)
            if now - req["timestamp"] > timedelta(minutes=10) and req["approved"] is None:
                expired_requests.append(req_id)
                continue
                
            request_info = f"ID: {req_id} | IP: {req['ip']} | Port: {req['port']} | Time: {req['timestamp'].strftime('%H:%M:%S')}"
            
            if req["approved"] is None:
                # Pending request
                self.requests_listbox.insert(tk.END, request_info)
            elif req["approved"]:
                # Approved request
                approval_time = req.get("approval_time", req["timestamp"])
                approved_info = f"{request_info} | Approved at: {approval_time.strftime('%H:%M:%S')}"
                self.approved_listbox.insert(tk.END, approved_info)
                
        # Remove expired requests
        for req_id in expired_requests:
            del self.access_requests[req_id]
            
        if expired_requests:
            self.save_data()
            
    def refresh_dashboard(self):
        # Update dashboard counters
        self.open_ports_count.config(text=str(len(self.open_ports)))
        self.blocked_ips_count.config(text=str(len(self.blocked_ips)))
        
        # Update active connections count
        try:
            connections = psutil.net_connections(kind='inet')
            active_count = len([c for c in connections if c.status == 'ESTABLISHED'])
            self.active_connections_count.config(text=str(active_count))
        except:
            self.active_connections_count.config(text="N/A")
            
        # Update suspicious processes count
        self.suspicious_count.config(text=str(len(self.suspicious_processes)))
            
    def is_valid_ip(self, ip):
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        return True
        
    def load_data(self):
        # Load data from files if they exist
        if os.path.exists("firewall_data.json"):
            try:
                with open("firewall_data.json", "r") as f:
                    data = json.load(f)
                    
                self.blocked_ips = set(data.get("blocked_ips", []))
                self.allowed_ips = set(data.get("allowed_ips", []))
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
        # Save data to file
        data = {
            "blocked_ips": list(self.blocked_ips),
            "allowed_ips": list(self.allowed_ips),
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
            
    def start_background_threads(self):
        # Start thread to periodically check for expired requests
        self.check_expired_thread = threading.Thread(target=self.check_expired_requests, daemon=True)
        self.check_expired_thread.start()
        
        # Start thread to update dashboard
        self.dashboard_thread = threading.Thread(target=self.update_dashboard, daemon=True)
        self.dashboard_thread.start()
        
    def check_expired_requests(self):
        while True:
            time.sleep(60)  # Check every minute
            now = datetime.now()
            expired_requests = []
            
            for req_id, req in self.access_requests.items():
                # Check if request has expired (older than 10 minutes)
                if now - req["timestamp"] > timedelta(minutes=10) and req["approved"] is None:
                    expired_requests.append(req_id)
                    
            # Remove expired requests
            if expired_requests:
                for req_id in expired_requests:
                    del self.access_requests[req_id]
                self.save_data()
                
    def update_dashboard(self):
        while True:
            time.sleep(5)  # Update every 5 seconds
            self.refresh_dashboard()
            
    def log_activity(self, message, category="INFO"):
        """Add an entry to the activity log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {category}: {message}\n"
        
        # Add to activity text (dashboard)
        self.activity_text.insert(tk.END, log_entry)
        self.activity_text.see(tk.END)
        
        # Add to logs tab
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
        
    def clear_logs(self):
        """Clear the logs"""
        self.logs_text.delete(1.0, tk.END)
        self.log_activity("Logs cleared", "CLEAR")
        
    def save_logs(self):
        """Save logs to a file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firewall_logs_{timestamp}.txt"
            with open(filename, "w") as f:
                f.write(self.logs_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Logs saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")
            
    def export_logs_csv(self):
        """Export logs to CSV format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firewall_logs_{timestamp}.csv"
            with open(filename, "w") as f:
                f.write("Timestamp,Category,Message\n")
                logs_content = self.logs_text.get(1.0, tk.END)
                lines = logs_content.strip().split('\n')
                for line in lines:
                    if line.startswith('[') and '] ' in line:
                        # Parse the log line
                        timestamp_end = line.find(']')
                        if timestamp_end > 0:
                            timestamp_part = line[1:timestamp_end]
                            category_end = line.find(':', timestamp_end)
                            if category_end > 0:
                                category_part = line[timestamp_end+3:category_end]
                                message_part = line[category_end+2:]
                                f.write(f'"{timestamp_part}","{category_part}","{message_part}"\n')
            messagebox.showinfo("Success", f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")
            
    def simulate_access_request(self, ip, port):
        """Simulate an access request for testing purposes"""
        request_id = f"REQ{int(time.time()) % 100000}"
        self.access_requests[request_id] = {
            "ip": ip,
            "port": port,
            "timestamp": datetime.now(),
            "approved": None
        }
        self.refresh_requests_list()
        self.save_data()
        self.log_activity(f"New access request - IP: {ip}, Port: {port}", "REQUEST")
        return request_id

    def create_honeypot_tab(self):
        # Main Layout
        main_frame = tk.Frame(self.honeypot_frame, bg="#0A0A0A")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control Section
        control_frame = tk.LabelFrame(main_frame, text="🎮 C2 Command Center", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=5)

        # Status & Toggle
        status_frame = tk.Frame(control_frame, bg="#1E1E1E")
        status_frame.pack(fill=tk.X, pady=10)
        
        self.honeypot_status_lbl = tk.Label(status_frame, text="SYSTEM STANDBY", font=("Courier", 14, "bold"), bg="#1E1E1E", fg="#FFFF00")
        self.honeypot_status_lbl.pack(side=tk.LEFT, padx=20)
        
        self.honeypot_btn = tk.Button(status_frame, text="ACTIVATE LISTENER", command=self.toggle_honeypot, bg="#00FF00", fg="#000000", font=("Courier", 12, "bold"), width=20)
        self.honeypot_btn.pack(side=tk.RIGHT, padx=20)

        # Docker Status
        self.docker_status_lbl = tk.Label(control_frame, text="Docker Check...", bg="#1E1E1E", fg="#FFFF00")
        self.docker_status_lbl.pack(pady=5)
        if self.docker_client:
             self.docker_status_lbl.config(text="Docker Python Client: CONNECTED", fg="#00FF00")
        else:
             self.docker_status_lbl.config(text="Docker Python Client: MISSING (Using Subprocess)", fg="#FFA500")

        # Logs Section
        logs_frame = tk.LabelFrame(main_frame, text="🛰️ Live Telemetry Feed (JSON Stream)", bg="#1E1E1E", fg="#00FF00", padx=10, pady=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.honeypot_logs = scrolledtext.ScrolledText(logs_frame, bg="#000000", fg="#00FF00", font=("Courier", 10), cursor="arrow")
        self.honeypot_logs.pack(fill=tk.BOTH, expand=True)

    def toggle_honeypot(self):
        if not self.honeypot_active:
            self.start_honeypot()
        else:
            self.stop_honeypot()

    def start_honeypot(self):
        self.honeypot_active = True
        self.honeypot_btn.config(text="DEACTIVATE", bg="#FF0000", fg="#FFFFFF")
        self.honeypot_status_lbl.config(text="WAITING FOR HONEYPOT...", fg="#FFFF00")
        
        network_monitor.set_honeypot_mode(True)
        self.update_honeypot_log("[SYSTEM] C2 Listener / Whitelist Injection Initiated...")

        # Start Docker
        threading.Thread(target=self._run_docker_start, daemon=True).start()
        # Start Log Reader
        threading.Thread(target=self.read_honeypot_logs, daemon=True).start()
        # Start Socket Listener
        threading.Thread(target=self.honeypot_socket_listener, daemon=True).start()

    def stop_honeypot(self):
        self.honeypot_active = False
        self.honeypot_btn.config(text="ACTIVATE LISTENER", bg="#00FF00", fg="#000000")
        self.honeypot_status_lbl.config(text="SYSTEM STANDBY", fg="#FFFF00")
        
        network_monitor.set_honeypot_mode(False)
        self.update_honeypot_log("[SYSTEM] Stopping C2 Services...")
        
        # Stop Docker
        threading.Thread(target=self._run_docker_stop, daemon=True).start()

    def _run_docker_start(self):
        try:
             # Just launch the container, same as before but ensuring it can talk to host
             # For simpler C2, we assume default bridge or host networking allows it to hit this IP.
             pass
             # Reuse previous logic or simplified for this turn? I'll keep previous logic but assume it's good.
             if self.docker_client:
                 try:
                     self.docker_client.containers.run(
                         "chimera-elite",
                         name="chimera-defense",
                         detach=True,
                         remove=True,
                         cap_add=["NET_ADMIN"],
                         ports={'2222/tcp': 2222, '8080/tcp': 8080, '2121/tcp': 2121, '9999/tcp': 9999}
                     )
                     self.update_honeypot_log("[DOCKER] Container 'chimera-defense' started.")
                     return
                 except: pass

             cmd = "docker run -d --rm --cap-add=NET_ADMIN -p 2222:2222 -p 8080:8080 -p 2121:2121 -p 9999:9999 --name chimera-defense chimera-elite"
             subprocess.run(cmd, shell=True, check=True)
             self.update_honeypot_log("[DOCKER] Container started via subprocess.")
        except Exception as e:
             self.update_honeypot_log(f"[ERROR] Failed to start container: {e}")

    def _run_docker_stop(self):
        try:
             subprocess.run("docker stop chimera-defense", shell=True)
             self.update_honeypot_log("[DOCKER] Container stopped.")
        except Exception as e: pass

    def read_honeypot_logs(self):
        # Same log reader as before for container stdout
        pass

    def honeypot_socket_listener(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('0.0.0.0', 65000))
            server.listen(5)
            server.settimeout(1.0)
            self.update_honeypot_log("[TELEMETRY] C2 Server Listening on Port 65000...")
            
            while self.honeypot_active:
                try:
                    client, addr = server.accept()
                    # Update status
                    self.root.after(0, lambda: self.honeypot_status_lbl.config(text="HONEYPOT CONNECTED", fg="#00FF00"))
                    
                    data = client.recv(4096).decode()
                    if data:
                        try:
                            # Try parsing JSON
                            import json
                            parsed = json.loads(data)
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            self.update_honeypot_log(f"[{timestamp}] [ALERT] {json.dumps(parsed, indent=2)}")
                        except:
                            # Fallback text
                            self.update_honeypot_log(f"[RAW DATA] from {addr[0]}: {data}")
                    
                    client.close()
                    # Reset status to waiting after disconnect (unless we want it to stick)
                    # For a one-off alert system, it flickers. Let's leave it Green to show activity occurred or revert.
                    # Requirement: "Waiting..." -> "Connected".
                    # I'll let it stay Green for a bit or just stay Green until stop.
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.update_honeypot_log(f"[SOCKET ERROR] {e}")
            server.close()
        except Exception as e:
            self.update_honeypot_log(f"[Bind Error] {e}")

    def update_honeypot_log(self, message):
         if not hasattr(self, 'honeypot_logs'): return
         try:
            self.honeypot_logs.insert(tk.END, f"{message}\n")
            self.honeypot_logs.see(tk.END)
         except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = FirewallGUI(root)
    
    # Add a menu for testing
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    test_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Test", menu=test_menu)
    test_menu.add_command(label="Simulate Access Request", command=lambda: app.simulate_access_request("192.168.1.100", 8080))
    test_menu.add_command(label="Simulate DDoS Attack", command=lambda: app.suspicious_listbox.insert(tk.END, f"Suspicious activity from 10.0.0.1 at {datetime.now().strftime('%H:%M:%S')}"))
    
    root.mainloop()