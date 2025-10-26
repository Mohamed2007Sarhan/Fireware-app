# 🛡️ CYBER SHIELD PRO - Advanced Penetration Testing Firewall

A comprehensive cybersecurity firewall application specifically designed for penetration testers and cybersecurity professionals. This advanced firewall provides real-time protection against unauthorized access, DDoS attacks, and suspicious network activity.

## 🚀 Key Features

### 🔐 Advanced IP Management
- **IP Filtering**: Block and allow specific IP addresses
- **Whitelist Protection**: Never block trusted IPs
- **Suspicious IP Detection**: Automatic flagging of potentially malicious IPs
- **Geolocation Lookup**: Identify the physical location of any IP address

### 🚪 Port Security
- **Port Management**: Open and close ports dynamically
- **Access Control**: Require approval for connections to critical ports
- **Port Monitoring**: Real-time view of all open ports

### ⚡ DDoS Protection
- **Rate Limiting**: Monitor connection rates from each IP
- **Automatic Blocking**: Instantly block IPs with excessive connections
- **Configurable Thresholds**: Adjust sensitivity for your environment
- **Timed Blocking**: Automatically unblock IPs after set duration

### 🔔 Access Request System
- **Approval Workflow**: Require explicit approval for sensitive connections
- **10-Minute Timeout**: Automatic rejection of expired requests
- **Request Logging**: Complete audit trail of all access attempts

### 🖥️ Process Monitoring
- **Real-time Process View**: See all running processes with resource usage
- **Process Control**: Kill, suspend, or resume any process
- **Suspicious Process Detection**: Scan for known malicious software

### 💻 Integrated Terminal
- **System Command Execution**: Run Windows commands directly from the firewall
- **Quick Commands**: One-click access to common security tools
- **Command History**: Track all executed commands

### 🌍 IP Geolocation
- **Location Lookup**: Determine the country, region, and city of any IP
- **ISP Information**: Identify the internet service provider
- **Coordinate Data**: Get latitude and longitude coordinates
- **Lookup History**: Keep track of all geolocation queries

### 📊 Comprehensive Dashboard
- **Real-time Statistics**: View open ports, blocked IPs, and active connections
- **Activity Logs**: Monitor all firewall actions with timestamps
- **Suspicious Activity Alerts**: Immediate notification of potential threats

### 📝 Advanced Logging
- **Detailed Activity Tracking**: Complete record of all firewall events
- **CSV Export**: Export logs for analysis
- **Persistent Storage**: Data saved between sessions

## 🛠️ Installation

1. Install Python 3.7 or higher
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## 🚀 Usage

Run the application:
```
python main.py
```

Or double-click on `run_firewall.bat`

## 🧩 Components

- `main.py`: Entry point for the application
- `firewall_gui.py`: Advanced graphical user interface with cyber-themed design
- `firewall_core.py`: Core firewall logic and data management
- `network_monitor.py`: Network connection monitoring and threat detection
- `requirements.txt`: Python package dependencies

## 🔧 How It Works

### Dashboard
The dashboard provides a real-time overview of your system's network security status, including open ports, blocked IPs, active connections, and suspicious processes.

### IP Filtering
The application maintains lists of blocked, allowed, and whitelisted IP addresses. When a connection attempt is made, the system checks these lists to determine whether to allow or block the connection. Whitelisted IPs are never blocked.

### Port Management
Users can specify which ports should be open or closed. The system monitors network connections and blocks attempts to access closed ports. Critical ports require access approval.

### DDoS Protection
The system monitors connection rates from each IP address. If an IP exceeds the configured threshold (default 50 connections per minute), it is automatically blocked for a configurable duration (default 15 minutes).

### Access Request System
When an access request is made to critical ports, it appears in the "Access Requests" tab. The request must be approved within 10 minutes, or it is automatically rejected.

### Process Monitoring
View all running processes in real-time with CPU and memory usage. Detect and terminate suspicious processes with one click.

### IP Geolocation
Identify the physical location of any IP address to help determine if connections are coming from unexpected locations.

### Integrated Terminal
Execute system commands directly from the firewall interface, with quick access to common security tools.

## 🎨 Professional Cybersecurity Interface

The application features a professional cybersecurity-themed interface with:
- Matrix-style green-on-black color scheme
- Intuitive tabbed navigation
- Real-time dashboard updates
- Responsive design optimized for security professionals

## ⚠️ Limitations

This is a user-space application that simulates firewall functionality. For actual system-level firewall protection, integration with Windows Firewall or other system-level tools would be required.

## 📄 License

This project is for educational and professional cybersecurity purposes only.