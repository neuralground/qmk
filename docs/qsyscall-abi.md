# qSyscall ABI (User ↔ Kernel)

**Capability-based** syscalls:

- `q_alloc(n, profile) -> {VQ...}`
- `q_release({VQ...})`
- `q_submit(graph, policy) -> job_id`
- `q_cancel(job_id)`
- `q_status(job_id) -> {state, progress, events}`
- `q_measure_now(VQ, basis) -> EV`
- `q_open_chan(VQa,VQb, opts) -> CH`
- `q_close_chan(CH)`
- `q_checkpoint(job_id) -> ckpt`
- `q_restore(job_id, ckpt)`
- `q_negotiate_caps(requested) -> granted`

All resource identifiers are **kernel-issued handles**; user-mode cannot forge physical IDs.
