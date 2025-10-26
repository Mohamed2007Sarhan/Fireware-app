# 🛡️ CYBER SHIELD PRO - Setup Guide

## 📋 Prerequisites

1. **Python Installation**
   - Download Python from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - Verify installation by opening Command Prompt and typing:
     ```
     python --version
     ```

2. **Required Libraries**
   - This application requires the `psutil` and `requests` libraries
   - Install them using:
     ```
     pip install -r requirements.txt
     ```

## ▶️ Running the Application

### Method 1: Using the Batch File (Recommended)
1. Double-click on `run_firewall.bat`
2. Follow the on-screen instructions

### Method 2: Using Command Line
1. Open Command Prompt
2. Navigate to the application directory:
   ```
   cd C:\Users\Moham\OneDrive\Desktop\test
   ```
3. Run the application:
   ```
   python main.py
   ```

## 🎯 Using the Firewall - Professional Cybersecurity Features

### 📊 Dashboard
When the application starts, you'll see the dashboard which displays:
- Current open ports on your system
- Number of blocked IPs
- Active network connections
- Suspicious processes detected
- Recent activity logs

### 🌐 IP Filtering
1. Go to the "IP Filtering" tab
2. To block an IP:
   - Enter the IP address in the "IP Address" field under "Blocked IPs"
   - Click "Block IP"
3. To allow an IP:
   - Enter the IP address in the "IP Address" field under "Allowed IPs"
   - Click "Allow IP"
4. To whitelist an IP (never block):
   - Add the IP to both "Allowed" and "Blocked" lists to create a whitelist entry

### 🔌 Port Management
1. Go to the "Port Management" tab
2. To open a port:
   - Enter the port number in the "Port Number" field under "Open Ports"
   - Click "Open Port"
3. To close a port:
   - Enter the port number in the "Port Number" field under "Closed Ports"
   - Click "Close Port"
4. Critical ports (21, 22, 23, 25, 53, 80, 110, 143, 443, etc.) require access approval

### ⚡ DDoS Protection
1. Go to the "DDoS Protection" tab
2. Adjust settings as needed:
   - Connection Threshold: Number of connections per minute that triggers protection (default: 50)
   - Block Duration: How long an IP is blocked (in minutes, default: 15)
3. Click "Save Settings"
4. Toggle protection on/off using the "Toggle Protection" button

### 🔔 Access Requests
1. Go to the "Access Requests" tab
2. When an IP tries to access a critical port, a request will appear in the "Pending Requests" list
3. Pending requests will appear in the top list
4. Select a request and click:
   - "Approve Selected" to approve the request
   - "Reject Selected" to reject the request
5. Approved requests will appear in the bottom list
6. Requests automatically expire after 10 minutes if no action is taken

### ⚙️ Process Monitor
1. Go to the "Process Monitor" tab
2. View all running processes with PID, name, status, CPU%, memory%, and user
3. To control a process:
   - Enter the process name or PID in the "Process Name/ID" field
   - Click "Kill Process" to terminate it
   - Click "Suspend Process" to pause it
   - Click "Resume Process" to continue a suspended process
4. Click "Scan for Suspicious" to detect potentially malicious processes

### 🌍 IP Geolocation
1. Go to the "IP Geolocation" tab
2. To lookup an IP:
   - Enter the IP address in the "IP Address" field
   - Click "Lookup"
3. To get your own location:
   - Click "My Location"
4. View detailed information including:
   - Country, region, and city
   - ISP and organization
   - Latitude and longitude coordinates
   - Timezone
5. Lookup history is maintained in the "Lookup History" section

### 💻 Terminal
1. Go to the "Terminal" tab
2. Enter any Windows command in the input field and press Enter
3. Use quick buttons for common commands:
   - "Netstat" - Show network connections
   - "Tasklist" - List running processes
   - "IP Config" - Show network configuration
   - "Firewall Status" - Show Windows Firewall status
4. Click "Clear" to clear the terminal output

### 📝 Activity Logs
1. Go to the "Activity Logs" tab
2. View all firewall activities in real-time
3. Use "Clear Logs" to clear the log display
4. Use "Save Logs" to save logs to a text file
5. Use "Export CSV" to export logs in CSV format for analysis

## 🔥 Advanced Cybersecurity Features

### Automatic Port Detection
On startup, the firewall automatically detects and displays all currently open ports on your system.

### Real-time IP Access Monitoring
The system monitors all incoming connections and creates access requests for connections to critical ports.

### Advanced DDoS Protection
- Monitors connection rates from each IP address
- Automatically blocks IPs that exceed the configured threshold
- Configurable block duration
- Whitelist protection for trusted IPs

### Professional Dark Theme Interface
- Matrix-style green-on-black cyber interface
- Intuitive tabbed navigation
- Real-time dashboard with system information
- Responsive design optimized for security professionals

### Persistent Data Storage
All settings, blocked IPs, allowed IPs, whitelisted IPs, and access requests are saved to `firewall_data.json` between sessions.

### Suspicious Process Detection
The firewall can scan for known penetration testing and malicious tools including:
- Netcat, Nmap, Hydra, Metasploit
- Burp Suite, Wireshark, Tcpdump
- And many other security tools

### IP Geolocation Services
Determine the physical location of any IP address to help identify suspicious connections.

## 📝 Notes

- Data is automatically saved to `firewall_data.json`
- Requests automatically expire after 10 minutes if not approved/rejected
- DDoS protection automatically blocks IPs that exceed the connection threshold
- The application runs in the background monitoring network connections
- Whitelisted IPs are never blocked by any protection mechanism

## 🛠️ Troubleshooting

### If Python is not recognized:
1. Reinstall Python and ensure "Add Python to PATH" is checked
2. Restart your computer after installation
3. Try using `python3` instead of `python`

### If required packages fail to install:
1. Try: `pip install --upgrade pip`
2. Then: `pip install -r requirements.txt`
3. If that fails, try: `python -m pip install -r requirements.txt`

### If the GUI doesn't appear:
1. Check that all Python files are in the same directory
2. Ensure you're running the application from the correct directory
3. Check the Command Prompt for error messages

### If geolocation lookups fail:
1. Ensure you have an internet connection
2. Some networks may block access to geolocation services
3. Try using a different network connection

## 🔍 Advanced Usage for Penetration Testers

### Testing the Firewall
1. Use the "Test" menu in the application to simulate:
   - Access requests
   - DDoS attacks
2. These simulations will help you understand how the firewall responds to different scenarios

### Customizing Protected Ports
To change which ports require access approval:
1. Edit the `network_monitor.py` file
2. Find the `_is_access_request` method
3. Modify the port list as needed

### Performance Considerations
- The firewall monitors connections every second
- Connection logs are limited to 1000 entries to prevent memory issues
- Dashboard updates every 5 seconds
- Process monitoring is on-demand to preserve system resources

## ⚠️ Limitations

This is a user-space application that simulates firewall functionality. For actual system-level firewall protection, integration with Windows Firewall or other system-level tools would be required.