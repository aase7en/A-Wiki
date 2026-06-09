# Scout Benchmark Source

This is a tiny fixture used by `scripts/batch/scout.py --benchmark` to verify
that a candidate model can produce structurally-valid output.

It is intentionally small (~10 sentences) and English-only so any free model
should handle it cleanly.

## Topic

The fixture describes a simple device: a USB hub. A USB hub multiplies a
single USB port into several ports. Powered hubs supply external power so
high-draw devices don't starve. Bus-powered hubs share the host's 500 mA
budget across all downstream devices, which limits how many devices can run
simultaneously.

USB hubs follow the USB 2.0 or USB 3.x specification. The hub controller
chip handles signal routing and downstream-port enumeration. The number of
addressable downstream devices is capped at 127 per host controller.

Typical use cases include desktop port expansion, laptop dock replacement,
and embedded development boards exposing extra peripherals.
