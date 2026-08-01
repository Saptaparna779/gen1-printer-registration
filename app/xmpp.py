"""
Mock of persistent printer<->cloud connectivity (XMPP) — see BUD section 11.4.

In real GEN 1 this assigns a printer to an XMPP node and opens a long-lived
session. Here we just simulate node assignment so downstream registration
logic has something to depend on.
"""
import random


def assign_xmpp_node(printer_id: str) -> str:
    """Simulate assigning a printer to one of a pool of XMPP nodes."""
    node_pool = ["xmpp-node-1", "xmpp-node-2", "xmpp-node-3"]
    return random.choice(node_pool)
