# Security Model

- **Capability security**: privileged ops require CAP tokens bound to the submitting principal.
- **Linear handles**: VQ/CH are single-owner; prevents aliasing and accidental cross-tenant entanglement.
- **Entanglement firewall**: channels cannot connect tenants without a brokered capability.
- **Verifiable QVM**: single-pass checks for linearity, capability coverage, DAG acyclicity, bounded guards.
- **Audit & attestation**: per-epoch logs with job/capability decisions and mapping summaries.
