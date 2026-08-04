import pytest
from app import registration, store


def test_capabilities_are_captured_on_first_registration():
    printer = registration.register_printer(
        serial_number="SN-1001",
        model_number="HP-C-MFP-9500",
        firmware_version="1.0.0",
    )

    caps = store.get_capabilities(printer.printer_id)

    assert caps is not None
    assert caps.supports_color is True
    assert caps.supports_scan is True
    assert caps.supports_print is True


def test_reregistration_does_not_overwrite_existing_capabilities():
    first = registration.register_printer(
        serial_number="SN-1002",
        model_number="HP-C-MFP-9500",
        firmware_version="1.0.0",
    )
    original_caps = store.get_capabilities(first.printer_id)

    second = registration.register_printer(
        serial_number="SN-1002",
        model_number="HP-LJ-2055",
        firmware_version="1.0.1",
    )
    updated_caps = store.get_capabilities(second.printer_id)

    assert second.printer_id == first.printer_id
    assert second.model_number == "HP-LJ-2055"
    assert updated_caps is not None
    assert updated_caps.supports_color is True
    assert updated_caps.supports_scan is True
    assert updated_caps.max_dpi == original_caps.max_dpi
    assert updated_caps.supports_print == original_caps.supports_print
