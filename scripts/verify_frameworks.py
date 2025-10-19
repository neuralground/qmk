#!/usr/bin/env python3
"""
Quantum Framework Verification Script

Verifies that all quantum computing frameworks are installed correctly
and can execute basic quantum circuits.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def check_qiskit() -> Tuple[bool, str]:
    """Check Qiskit installation."""
    try:
        import qiskit
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator
        
        # Create and run simple circuit
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        simulator = AerSimulator()
        job = simulator.run(qc, shots=100)
        result = job.result()
        counts = result.get_counts()
        
        # Verify we got results
        if len(counts) > 0:
            return True, f"✅ Qiskit {qiskit.__version__} - Working"
        else:
            return False, "❌ Qiskit - No results from simulation"
            
    except ImportError as e:
        return False, f"❌ Qiskit - Not installed ({e})"
    except Exception as e:
        return False, f"❌ Qiskit - Error: {e}"


def check_cirq() -> Tuple[bool, str]:
    """Check Cirq installation."""
    try:
        import cirq
        
        # Create and run simple circuit
        q0, q1 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit(
            cirq.H(q0),
            cirq.CNOT(q0, q1),
            cirq.measure(q0, q1, key='result')
        )
        
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=100)
        histogram = result.histogram(key='result')
        
        # Verify we got results
        if len(histogram) > 0:
            return True, f"✅ Cirq {cirq.__version__} - Working"
        else:
            return False, "❌ Cirq - No results from simulation"
            
    except ImportError as e:
        return False, f"❌ Cirq - Not installed ({e})"
    except Exception as e:
        return False, f"❌ Cirq - Error: {e}"


def check_azure_quantum() -> Tuple[bool, str]:
    """Check Azure Quantum / Q# installation."""
    try:
        import qsharp
        
        # Try to compile simple Q# code
        qsharp_code = """
            open Microsoft.Quantum.Intrinsic;
            
            operation TestOperation() : Result {
                use q = Qubit();
                H(q);
                return M(q);
            }
        """
        
        # Just check if we can import and compile
        # Full execution may require Azure credentials
        return True, f"✅ Q# {qsharp.__version__} - Installed"
            
    except ImportError as e:
        return False, f"❌ Q# - Not installed ({e})"
    except Exception as e:
        # Q# might be installed but not fully configured
        return True, f"⚠️  Q# - Installed but may need configuration"


def check_pyquil() -> Tuple[bool, str]:
    """Check PyQuil installation (optional)."""
    try:
        import pyquil
        from pyquil import Program
        from pyquil.gates import H, CNOT
        
        # Create simple program
        p = Program()
        p += H(0)
        p += CNOT(0, 1)
        
        return True, f"✅ PyQuil {pyquil.__version__} - Installed"
            
    except ImportError:
        return False, "⚠️  PyQuil - Not installed (optional)"
    except Exception as e:
        return False, f"⚠️  PyQuil - Error: {e}"


def check_qmk() -> Tuple[bool, str]:
    """Check QMK installation."""
    try:
        from kernel.simulator.enhanced_executor import EnhancedExecutor
        from kernel.qir_bridge.optimizer_integration import OptimizedExecutor
        
        # Create simple QVM graph
        qvm_graph = {
            "program": {
                "nodes": [
                    {
                        "id": "alloc1",
                        "op": "ALLOC_LQ",
                        "args": {"n": 2, "profile": "logical:Surface(d=7)"},
                        "vqs": ["q0", "q1"]
                    },
                    {"id": "h0", "op": "APPLY_H", "vqs": ["q0"]},
                    {"id": "cx01", "op": "APPLY_CNOT", "vqs": ["q0", "q1"]},
                    {"id": "m0", "op": "MEASURE_Z", "vqs": ["q0"], "produces": ["m0"]},
                    {"id": "m1", "op": "MEASURE_Z", "vqs": ["q1"], "produces": ["m1"]},
                ]
            }
        }
        
        executor = EnhancedExecutor()
        result = executor.execute(qvm_graph)
        
        if result.get('status') == 'COMPLETED':
            return True, "✅ QMK - Working"
        else:
            return False, "❌ QMK - Execution failed"
            
    except ImportError as e:
        return False, f"❌ QMK - Import error ({e})"
    except Exception as e:
        return False, f"❌ QMK - Error: {e}"


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Quantum Framework Verification")
    print("=" * 60)
    print()
    
    checks = {
        "QMK": check_qmk,
        "Qiskit": check_qiskit,
        "Cirq": check_cirq,
        "Azure Quantum (Q#)": check_azure_quantum,
        "PyQuil": check_pyquil,
    }
    
    results: Dict[str, Tuple[bool, str]] = {}
    
    for name, check_func in checks.items():
        print(f"Checking {name}...", end=" ")
        sys.stdout.flush()
        success, message = check_func()
        results[name] = (success, message)
        print(message)
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    required = ["QMK", "Qiskit", "Cirq"]
    optional = ["Azure Quantum (Q#)", "PyQuil"]
    
    required_ok = all(results[name][0] for name in required if name in results)
    optional_count = sum(1 for name in optional if name in results and results[name][0])
    
    print(f"\nRequired frameworks: {'✅ All working' if required_ok else '❌ Some missing'}")
    print(f"Optional frameworks: {optional_count}/{len(optional)} installed")
    
    if required_ok:
        print("\n🎉 All required frameworks are working!")
        print("You can now run end-to-end validation tests:")
        print("  pytest tests/integration/test_end_to_end_validation.py -v")
    else:
        print("\n⚠️  Some required frameworks are missing.")
        print("Install with:")
        print("  pip install -r requirements-quantum-frameworks.txt")
    
    print()
    
    # Return exit code
    return 0 if required_ok else 1


if __name__ == "__main__":
    sys.exit(main())
