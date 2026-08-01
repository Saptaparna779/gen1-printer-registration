"""
In-memory data store standing in for the real GEN 1 printer/cloud-identity
database. Kept intentionally dumb (dict-backed) since this is a demo
environment, not a production data layer.
"""
from typing import Dict, Optional
from app.models import Printer, PrinterCapabilities

# printer_id -> Printer
_printers: Dict[str, Printer] = {}

# printer_id -> PrinterCapabilities
_capabilities: Dict[str, PrinterCapabilities] = {}

# serial_number -> printer_id  (only for ACTIVE/REGISTERED printers)
_serial_index: Dict[str, str] = {}

_email_index: Dict[str, str] = {}

def index_email(email: str, printer_id: str) -> None:
    _email_index[email] = printer_id

def get_printer_by_email(email: str):
    printer_id = _email_index.get(email)
    return _printers.get(printer_id) if printer_id else None
    
def reset() -> None:
    """Wipe the store. Used between tests / demo runs."""
    _printers.clear()
    _capabilities.clear()
    _serial_index.clear()


def save_printer(printer: Printer) -> None:
    _printers[printer.printer_id] = printer


def get_printer(printer_id: str) -> Optional[Printer]:
    return _printers.get(printer_id)


def get_printer_by_serial(serial_number: str) -> Optional[Printer]:
    printer_id = _serial_index.get(serial_number)
    if printer_id is None:
        return None
    return _printers.get(printer_id)


def index_serial(serial_number: str, printer_id: str) -> None:
    _serial_index[serial_number] = printer_id


def remove_serial_index(serial_number: str) -> None:
    _serial_index.pop(serial_number, None)


def delete_printer(printer_id: str) -> None:
    _printers.pop(printer_id, None)


def save_capabilities(capabilities: PrinterCapabilities) -> None:
    _capabilities[capabilities.printer_id] = capabilities


def get_capabilities(printer_id: str) -> Optional[PrinterCapabilities]:
    return _capabilities.get(printer_id)


def delete_capabilities(printer_id: str) -> None:
    _capabilities.pop(printer_id, None)


def all_printers():
    return list(_printers.values())


def all_capabilities():
    """Exposed mainly so tests can assert nothing orphaned is left behind."""
    return list(_capabilities.values())
