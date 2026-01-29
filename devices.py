#!/usr/bin/env python3
import os
import time
import logging
import subprocess
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
ROUTER_IP = os.getenv("ROUTER_IP") or "192.168.10.1"
ROUTER_USER = os.getenv("ROUTER_USER") or "admin"
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD")

class MikroTikClient:
    def __init__(self, ip: str, user: str, password: str):
        self.base_url = f"http://{ip}/rest"  # Base URL for REST
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.session.headers.update({"Content-Type": "application/json"})

    def get_dhcp_leases(self) -> Dict[str, Dict[str, str]]:
        url = f"{self.base_url}/ip/dhcp-server/lease"
        leases_map = {}
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                for lease in response.json():
                    mac = lease.get('mac-address')
                    if mac:
                        leases_map[mac] = {
                            'host-name': lease.get('host-name', ''),
                            'comment': lease.get('comment', '')
                        }
        except Exception:
            pass # Silent fail to keep logs clean
        return leases_map

    def get_hotspot_active(self) -> List[str]:
        url = f"{self.base_url}/ip/hotspot/active"
        active_macs = []
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                for user in response.json():
                    active_macs.append(user.get('mac-address'))
        except Exception:
            pass
        return active_macs

    def get_active_devices(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/ip/arp"
        devices = []
        try:
            arp_data = self.session.get(url, timeout=5).json()
            dhcp_map = self.get_dhcp_leases()

            for entry in arp_data:
                if entry.get('disabled') == 'true' or not entry.get('mac-address'):
                    continue
                
                mac = entry.get('mac-address')
                lease = dhcp_map.get(mac, {})
                name = entry.get('comment') or lease.get('host-name') or lease.get('comment') or "Unknown"
                
                entry['name'] = name
                devices.append(entry)
        except Exception as e:
            logger.error(f"ARP Fetch Error: {e}")
            
        return devices

    def get_system_logs(self) -> List[Dict[str, Any]]:
        """Fetch the latest system logs."""
        url = f"{self.base_url}/log"
        try:
            # We fetch all logs (RouterOS usually keeps last ~1000 in memory)
            # The API returns them oldest -> newest
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Log Fetch Error: {e}")
        return []

def send_notification(title, message, urgency='normal'):
    try:
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        subprocess.run(['notify-send', '-u', urgency, title, message], env=env)
    except Exception as e:
        logger.error(f"Notification failed: {e}")

def main():
    if not ROUTER_PASSWORD:
        logger.error("❌ Error: ROUTER_PASSWORD not found in .env file.")
        return

    client = MikroTikClient(ROUTER_IP, ROUTER_USER, ROUTER_PASSWORD)
    print(f"--- 🛡️  Security Center Active on {ROUTER_IP} ---")

    # State Tracking
    known_macs = set()
    last_log_id = None 
    first_run = True

    # Initialize last_log_id
    initial_logs = client.get_system_logs()
    if initial_logs:
        last_log_id = initial_logs[-1].get('.id')

    try:
        while True:
            # --- 1. LURKER CHECK ---
            arp_devices = client.get_active_devices()
            hotspot_active = client.get_hotspot_active()
            
            # We no longer wipe 'known_macs' every loop. We accumulate.

            for device in arp_devices:
                mac = device.get('mac-address')
                ip = device.get('address', '')
                name = device.get('name')

                # If we have seen this MAC before in this session, skip it completely
                if mac in known_macs:
                    continue

                # --- NEW DEVICE PROCESSING ---
                urgency = "low" # Default
                should_alert = True

                # Filter 1: Trusted LAN (Wired)
                if ip.startswith("192.168.10."):
                    status = "Trusted LAN"
                    should_alert = False # Don't annoy me with wired devices
                
                # Filter 2: Upstream WAN (Huawei) - THE FIX FOR 192.168.100.1
                elif ip.startswith("192.168.100."):
                    status = "Upstream Gateway"
                    should_alert = False # Ignore the ISP router
                
                # Filter 3: Hotspot WiFi
                elif ip.startswith("192.168.20."):
                    if mac in hotspot_active:
                        status = "✅ Authenticated User"
                        urgency = "normal"
                    else:
                        status = "⚠️ LURKER (Not Logged In)"
                        urgency = "critical"
                
                # Filter 4: Unknown Subnets
                else:
                    status = "❓ Unknown Network"
                    urgency = "critical"

                # Add to memory so we don't alert again
                known_macs.add(mac)

                # Only alert if it's not first run (boot up) and not ignored
                if not first_run and should_alert:
                    logger.info(f"New Device: {name} - {status}")
                    send_notification("New Device Detected", f"{name}\n{ip}\n{status}", urgency)


            # --- 2. LOG WATCHER ---
            try:
                logs = client.get_system_logs()
                if logs and last_log_id:
                    new_logs = []
                    found_last = False
                    for log in logs:
                        if found_last:
                            new_logs.append(log)
                        elif log.get('.id') == last_log_id:
                            found_last = True
                    
                    for log in new_logs:
                        topics = log.get('topics', '')
                        message = log.get('message', '')
                        
                        is_critical = "critical" in topics or "error" in topics
                        is_login_fail = "login failure" in message
                        
                        if is_critical or is_login_fail:
                            logger.warning(f"SECURITY ALERT: {message}")
                            send_notification("🚨 SECURITY ALERT", f"{message}", "critical")
                        
                        last_log_id = log.get('.id')
                elif logs:
                    last_log_id = logs[-1].get('.id')
            except Exception as e:
                logger.error(f"Log Watcher Error: {e}")

            first_run = False
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nStopping Monitor.")

if __name__ == "__main__":
    main()