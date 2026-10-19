# Mac-changer

A small Linux command-line tool that shows, changes or randomizes a network interface's MAC address. It calls the system `ip` command (or `ifconfig` as a fallback) through Python's `subprocess` module, without a shell, and verifies the change afterward.

## Features
- Show the current MAC address of an interface
- Set a specific MAC address, with validation (format and unicast check)
- Generate a random *locally administered* unicast MAC
- Confirms the new address was actually applied

## Requirements
- Linux with `iproute2` (`ip`) or `net-tools` (`ifconfig`)
- Python 3.9+
- Root privileges (sudo) to change an address

## Usage
```bash
# Show the current MAC
python3 mac_changer.py -i eth0 --show

# Set a specific MAC
sudo python3 mac_changer.py -i eth0 -m 02:1a:2b:3c:4d:5e

# Use a random MAC
sudo python3 mac_changer.py -i wlan0 --random
```

Example output:
```
[*] Current MAC for eth0: 08:00:27:aa:bb:cc
[+] MAC address changed to 02:1a:2b:3c:4d:5e
```

The change lasts until the interface or machine restarts.

## Tests
```bash
pip install pytest
pytest
```

## Responsible use
Use this only on devices and networks you own or are authorized to manage. Changing a MAC address to bypass access controls on networks you don't control may break policy or law.

## License
MIT
