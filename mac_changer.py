#!/usr/bin/env python3
"""MAC Changer - change, randomize or show a network interface's MAC address on Linux.

Uses the `ip` command (iproute2) through subprocess, with `ifconfig` as a fallback.
Run with sudo/root. Only change interfaces on machines you own or administer.
"""
import argparse
import os
import random
import re
import shutil
import subprocess
import sys

MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def is_valid_mac(mac: str) -> bool:
    """Return True for a colon-separated, unicast MAC such as 02:1a:2b:3c:4d:5e."""
    if not MAC_RE.match(mac):
        return False
    return int(mac.split(":")[0], 16) & 0x01 == 0  # multicast bit must be clear


def random_mac() -> str:
    """Random locally administered, unicast MAC (first octet x2, x6, xA or xE)."""
    first = (random.randint(0x00, 0xFF) | 0x02) & 0xFE
    rest = [random.randint(0x00, 0xFF) for _ in range(5)]
    return ":".join(f"{b:02x}" for b in [first, *rest])


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command without a shell and raise a clear error if it fails."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {result.stderr.strip()}")
    return result


def interface_exists(iface: str) -> bool:
    return os.path.isdir(f"/sys/class/net/{iface}")


def get_mac(iface: str) -> str:
    """Read the current MAC from sysfs, falling back to `ip link show`."""
    path = f"/sys/class/net/{iface}/address"
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip().lower()
    out = run(["ip", "link", "show", iface]).stdout
    match = re.search(r"link/ether\s+([0-9a-f:]{17})", out)
    if not match:
        raise RuntimeError(f"Could not read MAC address for {iface}")
    return match.group(1)


def set_mac(iface: str, mac: str) -> None:
    """Bring the interface down, set the new address, and bring it back up."""
    if shutil.which("ip"):
        steps = [
            ["ip", "link", "set", "dev", iface, "down"],
            ["ip", "link", "set", "dev", iface, "address", mac],
            ["ip", "link", "set", "dev", iface, "up"],
        ]
    elif shutil.which("ifconfig"):
        steps = [
            ["ifconfig", iface, "down"],
            ["ifconfig", iface, "hw", "ether", mac],
            ["ifconfig", iface, "up"],
        ]
    else:
        raise RuntimeError("Neither 'ip' nor 'ifconfig' is installed")
    for cmd in steps:
        run(cmd)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Change or randomize a Linux interface's MAC address.")
    p.add_argument("-i", "--interface", required=True, help="interface name, e.g. eth0 or wlan0")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--mac", help="new MAC address, e.g. 02:1a:2b:3c:4d:5e")
    group.add_argument("-r", "--random", action="store_true", help="use a random locally administered MAC")
    group.add_argument("-s", "--show", action="store_true", help="only show the current MAC")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not sys.platform.startswith("linux"):
        print("[-] This tool supports Linux only.", file=sys.stderr)
        return 1
    if not interface_exists(args.interface):
        print(f"[-] Interface '{args.interface}' not found.", file=sys.stderr)
        return 1

    current = get_mac(args.interface)
    print(f"[*] Current MAC for {args.interface}: {current}")
    if args.show:
        return 0

    new_mac = random_mac() if args.random else args.mac.lower()
    if not is_valid_mac(new_mac):
        print(f"[-] '{new_mac}' is not a valid unicast MAC address.", file=sys.stderr)
        return 1
    if os.geteuid() != 0:
        print("[-] Changing a MAC address needs root. Re-run with sudo.", file=sys.stderr)
        return 1

    try:
        set_mac(args.interface, new_mac)
    except RuntimeError as err:
        print(f"[-] {err}", file=sys.stderr)
        return 1

    updated = get_mac(args.interface)
    if updated == new_mac:
        print(f"[+] MAC address changed to {updated}")
        return 0
    print(f"[-] MAC did not change (still {updated}). The driver may not allow it.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
