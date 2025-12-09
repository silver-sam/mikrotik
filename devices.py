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

def get_active_devices_rest() -> List[Dict[str, Any]]:
    """
    Retrieves a list of active ARP entries from a MikroTik router using the REST API.

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
        response = requests.get(
            url, 
            auth=(ROUTER_USER, ROUTER_PASSWORD), 
            verify=ROUTER_CERT_PATH, 
            timeout=5
        )
        response.raise_for_status()

        arp_entries = response.json()
        logger.info(f"Successfully retrieved data from {url}")

        for entry in arp_entries:
            # Handle both string 'true' and boolean True
            is_disabled = str(entry.get('disabled', 'false')).lower() == 'true'
            
            if not is_disabled:
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
            print(f"IP: **{ip}** | MAC: {mac} | Interface: {interface}")

if __name__ == "__main__":
    main()