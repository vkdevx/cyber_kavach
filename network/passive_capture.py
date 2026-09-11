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
        iface = interface or settings.CAPTURE_INTERFACE
        InterfaceGuard.assert_read_only_interface(iface)

        log_security_event(
            event_type="PASSIVE_CAPTURE_START",
            message=f"Starting passive capture on interface '{iface}'",
            details={"interface": iface}
        )

        try:
            self.sniffer = AsyncSniffer(
                iface=iface,
                prn=self._scapy_callback,
                store=False,
                promisc=settings.PROMISCUOUS_MODE
            )
            self.sniffer.start()
            self.is_running = True
        except Exception as exc:
            log_security_event(
                event_type="PASSIVE_CAPTURE_ERROR",
                message=f"Failed to start passive sniffer on '{iface}': {str(exc)}. Falling back to synthetic mode.",
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
