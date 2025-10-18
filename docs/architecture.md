# Architecture

```
Front-end → QIR (static optimization) → QVM (portable, verifiable)
                                │
                                ▼
                          User-mode Runtime
                 (JIT, planner, resource manager)
                                │  qSyscalls
                                ▼
────────────────────────────────────────────────────────
                 QMK Microkernel (Supervisor)
      Mapping • Scheduling • Decoding • Capabilities • Telemetry
────────────────────────────────────────────────────────
                                ▼
                      Physical Control Layer
```

- **User-mode** sees only virtual handles and capabilities; never physical IDs.
- **Supervisor** owns mapping, decoding, scheduling, and entanglement services.
