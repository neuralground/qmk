# Azure Quantum Resource Estimator (QRE) Compatibility

**Version 0.1**

QMK provides full compatibility with the Azure Quantum Resource Estimator configuration format and semantics. This allows users to leverage Azure QRE's extensive parameter library and formula-based QEC scheme definitions.

---

## Table of Contents

1. [Overview](#overview)
2. [Azure QRE Configuration Format](#azure-qre-configuration-format)
3. [Predefined Configurations](#predefined-configurations)
4. [Custom QEC Schemes](#custom-qec-schemes)
5. [Formula Syntax](#formula-syntax)
6. [Usage Examples](#usage-examples)
7. [API Reference](#api-reference)

---

## 1. Overview

Azure QRE defines quantum resource estimation through three main components:

1. **Qubit Parameters** (`qubitParams`): Physical qubit characteristics (gate times, error rates)
2. **QEC Schemes** (`qecScheme`): Error correction code parameters and formulas
3. **Code Distance** (`codeDistance`): The distance parameter for the QEC code

QMK implements the same configuration format, allowing seamless migration of Azure QRE configurations to QMK simulations.

### Key Features

- ✅ **Full Azure QRE syntax support**
- ✅ **All 6 predefined qubit parameters** (gate-based and Majorana)
- ✅ **Surface code and Floquet code** QEC schemes
- ✅ **Formula-based resource computation** (matching Azure QRE exactly)
- ✅ **Custom QEC scheme support** with formula syntax
- ✅ **Backward compatible** with QMK's native profile format

---

## 2. Azure QRE Configuration Format

### Complete Configuration Structure

```json
{
  "qubitParams": {
    "name": "qubit_gate_ns_e4",
    "instructionSet": "GateBased",
    "oneQubitMeasurementTime": "100 ns",
    "oneQubitGateTime": "50 ns",
    "twoQubitGateTime": "50 ns",
    "tGateTime": "50 ns",
    "oneQubitMeasurementErrorRate": 1e-4,
    "oneQubitGateErrorRate": 1e-4,
    "twoQubitGateErrorRate": 1e-4,
    "tGateErrorRate": 1e-4
  },
  "qecScheme": {
    "name": "surface_code",
    "errorCorrectionThreshold": 0.01,
    "crossingPrefactor": 0.03,
    "distanceCoefficientPower": 0,
    "logicalCycleTime": "(4 * twoQubitGateTime + 2 * oneQubitMeasurementTime) * codeDistance",
    "physicalQubitsPerLogicalQubit": "2 * codeDistance * codeDistance"
  },
  "codeDistance": 9
}
```

### Instruction Sets

**GateBased**: Standard gate-based quantum computing
- Parameters: `oneQubitGateTime`, `twoQubitGateTime`, `tGateTime`
- Error rates: `oneQubitGateErrorRate`, `twoQubitGateErrorRate`, `tGateErrorRate`

**Majorana**: Topological qubits (Microsoft's approach)
- Parameters: `twoQubitJointMeasurementTime`, `tGateTime`
- Error rates: `twoQubitJointMeasurementErrorRate`, `tGateErrorRate`

---

## 3. Predefined Configurations

Azure QRE provides 6 predefined qubit parameter sets:

### Gate-Based Qubits

| Name | Gate Time | Error Rate | Description |
|------|-----------|------------|-------------|
| `qubit_gate_ns_e3` | 50 ns | 10⁻³ | Fast gates, moderate fidelity |
| `qubit_gate_ns_e4` | 50 ns | 10⁻⁴ | Fast gates, high fidelity |
| `qubit_gate_us_e3` | 100 µs | 10⁻³ | Slow gates, moderate fidelity |
| `qubit_gate_us_e4` | 100 µs | 10⁻⁴ | Slow gates, high fidelity |

### Majorana Qubits

| Name | Measurement Time | Error Rate | Description |
|------|------------------|------------|-------------|
| `qubit_maj_ns_e4` | 100 ns | 10⁻⁴ | Fast measurements |
| `qubit_maj_ns_e6` | 100 ns | 10⁻⁶ | Ultra-high fidelity |

### QEC Schemes

**Surface Code (Gate-Based)**:
- Threshold: 1%
- Physical qubits: `2 * d²`
- Cycle time: `(4 * twoQubitGateTime + 2 * oneQubitMeasurementTime) * d`

**Surface Code (Majorana)**:
- Threshold: 0.15%
- Physical qubits: `2 * d²`
- Cycle time: `20 * oneQubitMeasurementTime * d`

**Floquet Code (Majorana)**:
- Threshold: 1%
- Physical qubits: `4 * d² + 8 * (d - 1)`
- Cycle time: `3 * oneQubitMeasurementTime * d`

---

## 4. Custom QEC Schemes

You can define custom QEC schemes using Azure QRE's formula syntax:

```python
custom_qec = {
    "qecScheme": {
        "name": "my_custom_code",
        "errorCorrectionThreshold": 0.015,
        "crossingPrefactor": 0.05,
        "distanceCoefficientPower": 0,
        "logicalCycleTime": "(6 * twoQubitGateTime + 3 * oneQubitMeasurementTime) * codeDistance",
        "physicalQubitsPerLogicalQubit": "3 * codeDistance * codeDistance"
    }
}
```

### QEC Scheme Parameters

- **errorCorrectionThreshold** (p*): Physical error rate threshold below which the code works
- **crossingPrefactor** (a): Prefactor in logical error rate formula: P_L ≈ a(p/p*)^((d+1)/2)
- **distanceCoefficientPower** (k): Power of distance in crossing prefactor (typically 0)
- **logicalCycleTime**: Formula for time to execute one logical operation
- **physicalQubitsPerLogicalQubit**: Formula for physical qubit overhead

---

## 5. Formula Syntax

Formulas use standard mathematical expressions with predefined variables:

### Available Variables

**From Qubit Parameters**:
- `oneQubitGateTime` (or `one_qubit_gate_time`)
- `twoQubitGateTime` (or `two_qubit_gate_time`)
- `oneQubitMeasurementTime` (or `one_qubit_measurement_time`)
- `twoQubitJointMeasurementTime` (or `two_qubit_joint_measurement_time`)
- `tGateTime` (or `t_gate_time`)

**Code Parameters**:
- `codeDistance` (or `code_distance`): The QEC code distance

### Operators

- Arithmetic: `+`, `-`, `*`, `/`
- Parentheses: `(`, `)`
- Integer operations supported

### Examples

```python
# Surface code cycle time
"(4 * twoQubitGateTime + 2 * oneQubitMeasurementTime) * codeDistance"

# Floquet code physical qubits
"4 * codeDistance * codeDistance + 8 * (codeDistance - 1)"

# Custom formula
"(10 * oneQubitGateTime + 5 * twoQubitGateTime) * codeDistance + 100"
```

---

## 6. Usage Examples

### Example 1: Using Predefined Azure QRE Config

```python
from kernel.simulator.qec_profiles import QECProfile

# Create profile from Azure QRE predefined parameters
profile = QECProfile.from_azure_qre(
    qubit_params="qubit_gate_ns_e4",
    qec_scheme="surface_code",
    code_distance=9
)

print(f"Physical qubits: {profile.physical_qubit_count}")
print(f"Logical cycle time: {profile.logical_cycle_time_us} µs")
print(f"Logical error rate: {profile.logical_error_rate()}")
```

### Example 2: Custom QEC Scheme

```python
custom_params = {
    "qecScheme": {
        "errorCorrectionThreshold": 0.02,
        "crossingPrefactor": 0.04,
        "logicalCycleTime": "(5 * twoQubitGateTime) * codeDistance",
        "physicalQubitsPerLogicalQubit": "2.5 * codeDistance * codeDistance"
    }
}

profile = QECProfile.from_azure_qre(
    qubit_params="qubit_gate_ns_e3",
    qec_scheme="surface_code",
    code_distance=7,
    custom_params=custom_params
)
```

### Example 3: Raw Azure QRE Configuration

```python
from kernel.simulator.azure_qre_compat import (
    create_qre_config,
    compute_logical_qubit_resources
)

# Create complete Azure QRE config
config = create_qre_config(
    qubit_params="qubit_gate_ns_e4",
    qec_scheme="surface_code",
    code_distance=13
)

# Compute resources using Azure QRE formulas
resources = compute_logical_qubit_resources(config)

print(f"Physical qubits per logical: {resources['physical_qubits_per_logical']}")
print(f"Logical cycle time: {resources['logical_cycle_time_us']} µs")
```

### Example 4: Majorana Qubits with Floquet Code

```python
profile = QECProfile.from_azure_qre(
    qubit_params="qubit_maj_ns_e6",
    qec_scheme="floquet_code",
    code_distance=9
)

# Floquet code uses fewer physical qubits than surface code
print(f"Physical qubits: {profile.physical_qubit_count}")
# Output: 356 (vs 162 for surface code)
```

### Example 5: Integration with QVM Graphs

```python
# QVM graphs can reference Azure QRE configs in allocation
qvm_graph = {
    "version": "0.1",
    "program": {
        "nodes": [
            {
                "id": "alloc1",
                "op": "ALLOC_LQ",
                "args": {
                    "n": 2,
                    "profile": "azure:qubit_gate_ns_e4:surface_code(d=9)"
                },
                "vqs": ["q0", "q1"],
                "caps": ["CAP_ALLOC"]
            }
        ]
    }
}
```

---

## 7. API Reference

### `QECProfile.from_azure_qre()`

Create a QEC profile from Azure QRE configuration.

**Parameters**:
- `qubit_params` (str): Azure QRE qubit parameter name
- `qec_scheme` (str): QEC scheme name ("surface_code" or "floquet_code")
- `code_distance` (int): Code distance
- `custom_params` (dict, optional): Custom parameter overrides

**Returns**: `QECProfile` instance

### `create_qre_config()`

Create a complete Azure QRE configuration dictionary.

**Parameters**:
- `qubit_params` (str): Qubit parameter name
- `qec_scheme` (str): QEC scheme name
- `code_distance` (int): Code distance
- `custom_params` (dict, optional): Custom overrides

**Returns**: Azure QRE configuration dict

### `compute_logical_qubit_resources()`

Compute logical qubit resources from Azure QRE config.

**Parameters**:
- `config` (dict): Azure QRE configuration

**Returns**: Dict with computed resources:
```python
{
    "code_distance": 9,
    "logical_cycle_time_us": 4.5,
    "physical_qubits_per_logical": 162,
    "error_correction_threshold": 0.01,
    "crossing_prefactor": 0.03
}
```

### Constants

- `AZURE_QUBIT_PARAMS`: Dict of all 6 predefined qubit parameters
- `AZURE_QEC_SCHEMES`: Dict of predefined QEC schemes

---

## Comparison: QMK vs Azure QRE

| Feature | Azure QRE | QMK |
|---------|-----------|-----|
| Qubit parameters | ✅ 6 predefined | ✅ Same 6 + custom |
| QEC schemes | ✅ Surface, Floquet | ✅ Same + Bacon-Shor, SHYPS |
| Formula syntax | ✅ String formulas | ✅ Exact same syntax |
| Custom schemes | ✅ Full support | ✅ Full support |
| Resource estimation | ✅ Static analysis | ✅ Static + simulation |
| Error simulation | ❌ No | ✅ Full error models |
| Execution | ❌ Estimation only | ✅ Full simulation |

**Key Advantage**: QMK can use Azure QRE configs for **actual simulation** with error models, not just resource estimation.

---

## References

- [Azure QRE Documentation](https://learn.microsoft.com/en-us/azure/quantum/intro-to-resource-estimation)
- [Azure QRE Target Parameters](https://learn.microsoft.com/en-us/azure/quantum/overview-resources-estimator)
- [QMK QEC Profiles](qec_profiles.py)
- [QMK Azure QRE Compatibility Layer](azure_qre_compat.py)

---

**End of Azure QRE Compatibility Documentation**
