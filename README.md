# mikrotik

A Python script to retrieve connected devices from a MikroTik router using the REST API (reads the ARP table).

## Features

- Connects to MikroTik RouterOS via REST API
- Retrieves and lists active devices (IP, MAC, Interface)
- Uses environment variables for secure configuration

## Prerequisites

- Python 3.8+
- MikroTik router with RouterOS v7+ and www-ssl enabled
- REST API access (username, password)
- [requests](https://pypi.org/project/requests/) and [python-dotenv](https://pypi.org/project/python-dotenv/)

## Installation

```bash
git clone https://github.com/silver-sam/mikrotik.git
cd mikrotik
pip install -r requirements.txt
```

## Setup

Create a `.env` file in the project root:

```env
ip_address=YOUR_ROUTER_IP
username=YOUR_USERNAME
pass=YOUR_PASSWORD
cert=PATH_TO_YOUR_CERT_FILE # or False to skip verification (not recommended)
```

## Usage

```bash
python devices.py
```

Example output:
```
✅ Successfully retrieved data from https://192.168.88.1/rest/ip/arp

--- Active Devices (IP ARP Table via REST API) ---
IP: 192.168.88.10 | MAC: AA:BB:CC:DD:EE:FF | Interface: ether1
```

## Troubleshooting

- Ensure your router allows REST API access (RouterOS v7+)
- Make sure the www-ssl service is running
- If you get SSL errors, set `cert=False` in your `.env` (not secure for production)

## License

MIT

## Acknowledgements

- [MikroTik Documentation](https://help.mikrotik.com/docs/display/ROS/REST+API)
- [requests library](https://pypi.org/project/requests/)