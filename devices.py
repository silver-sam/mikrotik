import requests
from dotenv import load_dotenv
import os

load_dotenv()

#Configuration
ROUTER_IP = os.getenv("ip_address")
USERNAME = os.getenv("username")
PASSWORD = os.getenv("pass")

CERT = os.getenv("cert")

#print(ROUTER_IP, USERNAME, PASSWORD, CERT)

def get_active_devices_rest():
    #Requires www-ssl service to be running on the router
    url = f"https://{ROUTER_IP}/rest/ip/arp"
    
    try:
        # Use HTTP Basic Authentication for the REST API
        response = requests.get(url, auth=(USERNAME, PASSWORD), verify=f"{CERT}", timeout=5)
        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)

        arp_entries = response.json()

        print(f"✅ Successfully retrieved data from {url}\n")
        print("--- Active Devices (IP ARP Table via REST API) ---")
        
        for entry in arp_entries:
            # The 'dynamic' check works the same way
            if entry.get('dynamic') == 'true' and entry.get('disabled') == 'false':
                print(f"IP: **{entry.get('address')}** | MAC: {entry.get('mac-address')} | Interface: {entry.get('interface')}")

    except requests.exceptions.RequestException as e:
        print(f"❌ REST API Error: Check if RouterOS is v7+, www-ssl is enabled, or if credentials are correct. Error: {e}")
        print("Note: If you see an SSL error, try setting 'verify=False' or import the router's certificate.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    get_active_devices_rest()
    pass