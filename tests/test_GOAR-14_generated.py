import pytest
from app import registration, store


def test_deregister_printer_marks_outstanding_claim_code_used():
    printer = registration.register_printer(
        serial_number="SN-9991",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )

    assert printer.claim_code is not None
    assert printer.claim_code.used is False

    registration.deregister_printer(printer.printer_id)

    assert printer.claim_code.used is True


def test_deregister_printer_removes_printer_and_related_data():
    printer = registration.register_printer(
        serial_number="SN-9992",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )

    registration.deregister_printer(printer.printer_id)

    assert store.get_printer(printer.printer_id) is None
    assert store.get_capabilities(printer.printer_id) is None
    assert store.get_printer_by_serial(printer.serial_number) is None
