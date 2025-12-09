#!/usr/bin/env python3
import os
import logging
from typing import Dict, List, Optional, Any
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
ROUTER_IP: Optional[str] = os.getenv("ROUTER_IP") or os.getenv("ip_address")
ROUTER_USER: Optional[str] = os.getenv("ROUTER_USER") or os.getenv("username")
ROUTER_PASSWORD: Optional[str] = os.getenv("ROUTER_PASSWORD") or os.getenv("pass")
ROUTER_CERT_PATH: Optional[str] = os.getenv("ROUTER_CERT_PATH") or os.getenv("cert")

def get_dhcp_leases() -> Dict[str, Dict[str, str]]:
    """
    Retrieves DHCP leases from the router to map MAC addresses to hostnames/comments.
    Returns:
        A dictionary mapping MAC address to a dict containing 'host-name' and 'comment'.
    """
    if not all([ROUTER_IP, ROUTER_USER, ROUTER_PASSWORD, ROUTER_CERT_PATH]):
        return {}

    url = f"https://{ROUTER_IP}/rest/ip/dhcp-server/lease"
    leases_map = {}

    try:
        response = requests.get(
            url, 
            auth=(ROUTER_USER, ROUTER_PASSWORD), 
            verify=ROUTER_CERT_PATH, 
            timeout=5
        )
        response.raise_for_status()
        
        leases = response.json()
        for lease in leases:
            mac = lease.get('mac-address')
            if mac:
                leases_map[mac] = {
                    'host-name': lease.get('host-name', ''),
                    'comment': lease.get('comment', ''),
                    'active-hostname': lease.get('active-hostname', '') # Sometimes it's here
                }
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch DHCP leases: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching leases: {e}")
    
    return leases_map

def get_active_devices_rest() -> List[Dict[str, Any]]:
    """
    Retrieves a list of active ARP entries from a MikroTik router using the REST API.
    Enriches the data with comments and hostnames from DHCP leases.

    This function requires the 'www-ssl' service to be enabled on the router.

    Returns:
        A list of dictionaries, where each dictionary represents an active ARP entry.
        Returns an empty list if there is an error.
    """
    if not all([ROUTER_IP, ROUTER_USER, ROUTER_PASSWORD, ROUTER_CERT_PATH]):
        logger.error("Missing required configuration. Please check your .env file.")
        logger.error("Required variables: ROUTER_IP, ROUTER_USER, ROUTER_PASSWORD, ROUTER_CERT_PATH")
        return []

    url = f"https://{ROUTER_IP}/rest/ip/arp"
    active_devices: List[Dict[str, Any]] = []

    try:
        # Fetch ARP text first
        response = requests.get(
            url, 
            auth=(ROUTER_USER, ROUTER_PASSWORD), 
            verify=ROUTER_CERT_PATH, 
            timeout=5
        )
        response.raise_for_status()
        arp_entries = response.json()
        logger.info(f"Successfully retrieved ARP data from {url}")

        # Fetch DHCP leases for names
        dhcp_map = get_dhcp_leases()

        for entry in arp_entries:
            # Handle both string 'true' and boolean True
            is_disabled = str(entry.get('disabled', 'false')).lower() == 'true'
            
            if not is_disabled:
                # Try to find a name from various sources
                mac = entry.get('mac-address')
                arp_comment = entry.get('comment', '')
                
                lease_info = dhcp_map.get(mac, {})
                lease_hostname = lease_info.get('host-name') or lease_info.get('active-hostname')
                lease_comment = lease_info.get('comment')

                # Priority: ARP Comment > DHCP Hostname > DHCP Comment > "Unknown"
                # (Actually sometimes DHCP hostname is better than comment, but for static ARP comment is usually the label)
                # Let's try: ARP Comment > Lease Hostname > Lease Comment
                
                name = arp_comment or lease_hostname or lease_comment or "Unknown"
                entry['name'] = name
                
                active_devices.append(entry)
        
        return active_devices

    except requests.exceptions.RequestException as e:
        logger.error("REST API Error: Check if RouterOS is v7+, www-ssl is enabled, or if credentials are correct.")
        logger.error(f"Error details: {e}")
        logger.info("Note: If you see an SSL error, ensure your router's certificate is correctly imported and the path is set in the .env file.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
    
    return []

def main():
    devices = get_active_devices_rest()
    if devices:
        print("--- Active Devices (IP ARP Table via REST API) ---")
        for device in devices:
            ip = device.get('address', 'Unknown')
            mac = device.get('mac-address', 'Unknown')
            interface = device.get('interface', 'Unknown')
            name = device.get('name', 'Unknown')
            print(f"IP: **{ip}** | MAC: {mac} | Name: {name} | Interface: {interface}")

if __name__ == "__main__":
    main()