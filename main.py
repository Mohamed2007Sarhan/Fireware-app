import sys
import os
import threading
import time

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firewall_gui import FirewallGUI
from firewall_core import firewall
from network_monitor import network_monitor
import tkinter as tk
from tkinter import messagebox

def start_network_monitoring():
    """Start the network monitoring in a separate thread"""
    network_monitor.start_monitoring()

def main():
    # Start network monitoring in background
    monitor_thread = threading.Thread(target=start_network_monitoring, daemon=True)
    monitor_thread.start()
    
    # Create and run the GUI
    root = tk.Tk()
    app = FirewallGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()