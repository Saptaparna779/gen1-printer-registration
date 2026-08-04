import pytest
from app import registration, store


def test_registration_history_logging_distinguishes_first_time_vs_reregistration():
    first_printer = registration.register_printer(
        serial_number="SN-1313",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )

    assert any("Registration started" in entry for entry in first_printer.registration_history)

    rerun_printer = registration.register_printer(
        serial_number="SN-1313",
        model_number="HP-LJ-2055",
        firmware_version="1.0.1",
    )

    assert any("Re-registration started" in entry for entry in rerun_printer.registration_history)


def test_reregistration_preserves_core_registration_behavior():
    first_printer = registration.register_printer(
        serial_number="SN-1314",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    original_xmpp_node = first_printer.xmpp_node

    rerun_printer = registration.register_printer(
        serial_number="SN-1314",
        model_number="HP-LJ-2055",
        firmware_version="1.0.1",
    )

    assert rerun_printer.status == "REGISTERED"
    assert rerun_printer.xmpp_node == original_xmpp_node
    assert rerun_printer.printer_id == first_printer.printer_id
