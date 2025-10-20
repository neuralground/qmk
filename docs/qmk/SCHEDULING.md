# Scheduling & Epochs

- Kernel advances in **epochs** aligned with syndrome cycles.
- Jobs submit DAGs; kernel topologically schedules subject to dependencies, capabilities, and quotas.
- Preemption and migration occur at **FENCE_EPOCH** boundaries; reversible segments may be uncomputed.
