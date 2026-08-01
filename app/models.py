"""
Data models for GEN 1 Printer Onboarding & Registration (dummy/demo service).

These are intentionally simple in-memory dataclasses. In the real GEN 1
platform these would map to persistent cloud identity records.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List


class PrinterStatus(str, Enum):
    PENDING = "PENDING"            # registration in progress
    REGISTERED = "REGISTERED"      # welcome page printed successfully, unclaimed
    CLAIMED = "CLAIMED"            # linked to a user account
    DEREGISTERED = "DEREGISTERED"  # cleaned up


@dataclass
class PrinterCapabilities:
    printer_id: str
    supports_print: bool = True
    supports_scan: bool = False
    supports_color: bool = False
    max_dpi: int = 600


@dataclass
class ClaimCode:
    code: str
    created_at: datetime
    expires_at: datetime
    used: bool = False


@dataclass
class Printer:
    printer_id: str            # internal record id (not the Cloud ID)
    serial_number: str
    model_number: str
    firmware_version: str
    cloud_id: Optional[str] = None
    printer_email_id: Optional[str] = None
    claim_code: Optional[ClaimCode] = None
    xmpp_node: Optional[str] = None
    status: PrinterStatus = PrinterStatus.PENDING
    owner_user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    registration_history: List[str] = field(default_factory=list)

    def log(self, event: str) -> None:
        self.registration_history.append(
            f"{datetime.utcnow().isoformat()} :: {event}"
        )
