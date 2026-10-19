import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[0]))
import mac_changer as mc


def test_valid_macs():
    assert mc.is_valid_mac("02:1a:2b:3c:4d:5e")
    assert mc.is_valid_mac("00:11:22:33:44:55")


def test_invalid_macs():
    for bad in ["", "02:1a:2b:3c:4d", "zz:1a:2b:3c:4d:5e", "02-1a-2b-3c-4d-5e", "01:00:5e:00:00:01"]:
        assert not mc.is_valid_mac(bad)


def test_random_mac_is_local_unicast():
    for _ in range(500):
        mac = mc.random_mac()
        first = int(mac.split(":")[0], 16)
        assert mc.is_valid_mac(mac)
        assert first & 0x02 and not first & 0x01


def test_cli_requires_action():
    import pytest
    with pytest.raises(SystemExit):
        mc.parse_args(["-i", "eth0"])
