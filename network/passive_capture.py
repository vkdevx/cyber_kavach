import asyncio
import threading
import time
from typing import Optional, Callable
from scapy.all import AsyncSniffer
from network.flow_models import ValidatedPacket
from network.packet_validator import PacketValidator
from network.deduplicator import PacketDeduplicator
from network.interface_guard import InterfaceGuard
from backend.core.logging_setup import log_security_event
from config.settings import settings


class PassiveCaptureService:
    """Passive packet capture service operating strictly in read-only mode."""

    def __init__(self, packet_callback: Optional[Callable[[ValidatedPacket], None]] = None):
        self.packet_callback = packet_callback
        self.validator = PacketValidator()
        self.deduplicator = PacketDeduplicator()
        self.sniffer: Optional[AsyncSniffer] = None
        self.is_running = False

    def _scapy_callback(self, pkt):
        """Scapy callback executing on sniffer thread."""
        try:
            validated = self.validator.validate_scapy_packet(pkt)
            if validated:
                if not self.deduplicator.is_duplicate(validated):
                    if self.packet_callback:
                        self.packet_callback(validated)
        except Exception as exc:
            log_security_event(
                event_type="SNIFFER_CALLBACK_ERROR",
                message=f"Sniffer callback error: {str(exc)}",
                level=30
            )

    def start(self, interface: Optional[str] = None):
        """Starts passive packet capture on the specified interface."""
        import sys
        from scapy.all import conf
        iface = interface or settings.CAPTURE_INTERFACE

        # On Windows or if eth0 is specified on non-Linux, use default active adapter
        if sys.platform == "win32" or iface == "eth0":
            actual_iface = conf.iface
            try:
                from scapy.all import IFACES
                for k, v in IFACES.items():
                    ip = str(getattr(v, "ip", "") or "")
                    if ip and not ip.startswith("127.") and not ip.startswith("169.254.") and not ip.startswith("192.168.56."):
                        actual_iface = v
                        break
            except Exception:
                pass
        else:
            actual_iface = iface

        InterfaceGuard.assert_read_only_interface(str(actual_iface))

        log_security_event(
            event_type="PASSIVE_CAPTURE_START",
            message=f"Starting passive capture on interface '{actual_iface}'",
            details={"interface": str(actual_iface)}
        )

        try:
            self.sniffer = AsyncSniffer(
                iface=actual_iface,
                prn=self._scapy_callback,
                store=False,
                promisc=settings.PROMISCUOUS_MODE
            )
            self.sniffer.start()
            self.is_running = True
        except Exception as exc:
            log_security_event(
                event_type="PASSIVE_CAPTURE_ERROR",
                message=f"Failed to start passive sniffer on '{actual_iface}': {str(exc)}. Falling back to synthetic mode.",
                level=30
            )
            self.is_running = False

    def stop(self):
        """Stops the passive sniffer."""
        if self.sniffer and self.is_running:
            try:
                self.sniffer.stop()
            except Exception:
                pass
            self.is_running = False
            log_security_event(
                event_type="PASSIVE_CAPTURE_STOP",
                message="Passive sniffer stopped."
            )
