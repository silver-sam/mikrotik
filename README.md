# MikroTik Active Devices Monitor

This script connects to a MikroTik router via its REST API to retrieve and display a list of active devices from the ARP table. It filters for devices that are **dynamic** and **enabled**, giving you a real-time view of what's actually connected.

## Features

- **Secure**: Uses HTTPS and verifies SSL certificates.
- **Robust**: Handles boolean values correctly (whether the API returns JSON booleans or strings).
- **Professional**: Includes logging and a full unit test suite.
- **Configurable**: Uses `.env` for configuration.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/silver-sam/mikrotik.git
    cd mikrotik
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration:**
    Create a `.env` file in the project root with the following variables:
    ```ini
    ROUTER_IP=192.168.88.1
    ROUTER_USER=admin
    ROUTER_PASSWORD=your_secure_password
    ROUTER_CERT_PATH=/path/to/router.crt
    ```
    *(Note: Backward compatibility with `ip_address`, `username`, `pass`, etc., is supported but deprecated.)*

## Usage

The easiest way to run the script is using the wrapper, which automatically handles the virtual environment:

```bash
./run.sh
```

Alternatively, if you prefer manual execution:
```bash
source venv/bin/activate
./devices.py
```

## Testing

To run the unit test suite:
```bash
python -m unittest discover tests
```