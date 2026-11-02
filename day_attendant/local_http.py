"""Canonical origins for the strictly loopback-only local HTTP boundary."""
from ipaddress import IPv4Address
import socket
from urllib.parse import urlsplit, urlunsplit

LOOPBACK_HOST = str(IPv4Address(socket.INADDR_LOOPBACK))


def local_origin(port):
    return urlunsplit(('http', f'{LOOPBACK_HOST}:{port}', '', '', ''))


def is_local_origin(value):
    if not isinstance(value, str):
        return False
    try:
        port = urlsplit(value).port
    except ValueError:
        return False
    return port is not None and 0 < port <= 65535 and value == local_origin(port)
