# examples/

This directory contains example workspace fixtures.

## demo-mission/

A pre-populated 8-artifact Sprint Pattern mission under
`examples/demo-mission/` (used as a reference for the canonical mission
structure). The mission demonstrates the template headers written by
`workspace-os mission new`. See `../tests/test_mission.py` for the
canonical 8-artifact list.

To create a fresh example workspace from scratch:

```bash
mkdir -p /tmp/example-ws
workspace-os --workspace /tmp/example-ws init
workspace-os --workspace /tmp/example-ws mission new example-mission
workspace-os --workspace /tmp/example-ws mission list
workspace-os --workspace /tmp/example-ws validate
```
