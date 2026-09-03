import socket
import getpass
import logging
from zeroconf import ServiceInfo, Zeroconf

logger = logging.getLogger("tinyscreen.services.zeroconf")

_zeroconf_instance = None

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

def get_host_label():
    return socket.gethostname().split('.')[0].replace(' ', '-') or "tinyscreen-host"

def register_mdns_service(port=5000, pair_id="", companion_version="0.5.0"):
    global _zeroconf_instance
    try:
        local_ip = get_local_ip()
        host_label = get_host_label()
        properties = {
            "pair_id": pair_id,
            "hostname": host_label,
            "user": getpass.getuser(),
            "version": companion_version,
        }
        info = ServiceInfo(
            "_tinyscreen._tcp.local.",
            f"Tiny AI Screen Companion ({host_label})._tinyscreen._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties=properties,
            server=f"{host_label}.local.",
        )
        _zeroconf_instance = Zeroconf()
        _zeroconf_instance.register_service(info)
        logger.info(f"[mDNS] Advertising _tinyscreen._tcp.local at {local_ip}:{port} (server: {host_label}.local., pair_id: {pair_id})")
    except Exception as e:
        logger.warning(f"[mDNS] Failed to register service: {e}")

def stop_mdns_service():
    global _zeroconf_instance
    if _zeroconf_instance is not None:
        try:
            _zeroconf_instance.close()
        except Exception:
            pass
        _zeroconf_instance = None
