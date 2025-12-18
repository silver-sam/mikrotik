# MikroTik Active Devices Monitor

This script connects to a MikroTik router via its REST API to retrieve and display a list of active devices from the ARP table. It filters for devices that are **dynamic** and **enabled**, giving you a real-time view of what's actually connected.

## Features

- **Security Alerts**: Monitors MikroTik system logs for critical events and login failures, sending desktop notifications.
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

## Running as a Systemd User Service

To run this script continuously in the background and have it start automatically on login (or boot, if user lingering is enabled), you can set it up as a systemd user service.

1.  **Create the service file:**
    ```bash
    mkdir -p ~/.config/systemd/user/
    ```
    Then, create a file named `mikrotik-monitor.service` inside `~/.config/systemd/user/` with the following content:

    ```ini
    [Unit]
    Description=MikroTik Device Monitor
    After=network.target graphical-session.target

    [Service]
    ExecStart=/home/silver/Desktop/mikrotik/run.sh
    WorkingDirectory=/home/silver/Desktop/mikrotik
    Restart=always
    RestartSec=10
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=/home/silver/.Xauthority

    [Install]
    WantedBy=default.target
    ```
    *Note: Replace `/home/silver/Desktop/mikrotik` with the actual path to your project directory if it differs.*

2.  **Reload systemd, enable, and start the service:**
    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now mikrotik-monitor.service
    ```

3.  **Check the service status and logs:**
    ```bash
    systemctl --user status mikrotik-monitor.service
    journalctl --user -u mikrotik-monitor.service -f
    ```

## Testing

To run the unit test suite:
```bash
python -m unittest discover tests
```