# Reversibility Semantics

- Segments between irreversible ops (`MEASURE_*`, `RESET`, `CLOSE_CHAN`) are **REV** if only unitary ops appear.
- Kernel may **uncompute** REV segments for rollback, migration, or energy-efficiency.
- Crossing an irreversible boundary requires a **checkpoint** if rollback is desired.
