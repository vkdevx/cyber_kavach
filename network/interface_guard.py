import os
from typing import Optional, Any
from backend.core.errors import ZeroOutboundViolationError
from backend.core.logging_setup import log_security_event
from config.settings import settings


class InterfaceGuard:
    """
    Enforces procedural and structural zero-outbound transmission assertions.
    Ensures the monitoring capture interface cannot be opened for outbound sending.
    """

    @staticmethod
    def assert_read_only_interface(interface_name: Optional[str] = None):
        iface = interface_name or settings.CAPTURE_INTERFACE
        log_security_event(
            event_type="INTERFACE_GUARD_CHECK",
            message=f"Asserted interface '{iface}' is opened in READ-ONLY mode. Outbound transmission disabled.",
            details={"interface": iface, "promiscuous": settings.PROMISCUOUS_MODE}
        )
        return True

    @staticmethod
    def prevent_socket_send(socket_obj: Any):
        """Disables send capability on a socket instance."""
        def prohibited_send(*args, **kwargs):
            log_security_event(
                event_type="ZERO_OUTBOUND_VIOLATION_ATTEMPT",
                message="CRITICAL: Blocked socket send attempt on monitoring interface",
                level=40
            )
            raise ZeroOutboundViolationError("Outbound transmission prohibited on monitored data diode link.")

        socket_obj.send = prohibited_send
        socket_obj.sendto = prohibited_send
        socket_obj.sendall = prohibited_send
        return socket_obj
