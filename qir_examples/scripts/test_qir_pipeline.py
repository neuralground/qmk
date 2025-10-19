#!/usr/bin/env python3
"""
Test QIR pipeline end-to-end.

This script:
1. Detects available QIR compilers
2. Compiles example programs to QIR
3. Parses QIR with QMK's QIR bridge
4. Generates QVM graphs
5. Verifies correctness
6. Cleans up generated files
"""

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path

# Add parent directory to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.qir_bridge import QIRParser, QVMGraphGenerator, ResourceEstimator


class CompilerDetector:
    """Detect available QIR compilers."""
    
    @staticmethod
    def has_qsharp():
        """Check if Q# compiler is available."""
        try:
            result = subprocess.run(['qsc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def has_qiskit_qir():
        """Check if Qiskit QIR is available."""
        try:
            import qiskit_qir
            return True
        except ImportError:
            return False
    
    @staticmethod
    def has_cirq_qir():
        """Check if Cirq QIR is available."""
        try:
            import cirq_qir
            return True
        except ImportError:
            return False


class QIRPipelineTester:
    """Test QIR pipeline with various front-ends."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.qir_examples_dir = ROOT / 'qir_examples'
        self.temp_dir = tempfile.mkdtemp(prefix='qmk_qir_test_')
        self.results = []
    
    def log(self, message):
        """Log message if verbose."""
        if self.verbose:
            print(message)
    
    def test_qsharp_example(self, qs_file):
        """Test Q# example."""
        self.log(f"\n{'='*70}")
        self.log(f"Testing Q# example: {qs_file.name}")
        self.log('='*70)
        
        # Compile to QIR
        qir_file = Path(self.temp_dir) / f"{qs_file.stem}.ll"
        
        try:
            # Note: This is a placeholder - actual Q# compilation would use qsc
            # For now, we'll use the embedded QIR from the demo
            self.log("⚠️  Q# compiler not fully integrated - using embedded QIR examples")
            return self._test_embedded_qir()
        except Exception as e:
            self.log(f"❌ Failed to compile Q#: {e}")
            return False
    
    def test_qiskit_example(self, py_file):
        """Test Qiskit example."""
        self.log(f"\n{'='*70}")
        self.log(f"Testing Qiskit example: {py_file.name}")
        self.log('='*70)
        
        qir_file = Path(self.temp_dir) / f"{py_file.stem}.ll"
        
        try:
            # Run Qiskit script to generate QIR
            result = subprocess.run(
                [sys.executable, str(py_file), '--output', str(qir_file)],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                self.log(f"❌ Qiskit script failed: {result.stderr}")
                return False
            
            # Test the generated QIR
            return self._test_qir_file(qir_file, "Qiskit")
            
        except Exception as e:
            self.log(f"❌ Failed to test Qiskit example: {e}")
            return False
    
    def test_cirq_example(self, py_file):
        """Test Cirq example."""
        self.log(f"\n{'='*70}")
        self.log(f"Testing Cirq example: {py_file.name}")
        self.log('='*70)
        
        qir_file = Path(self.temp_dir) / f"{py_file.stem}.ll"
        
        try:
            # Run Cirq script to generate QIR
            result = subprocess.run(
                [sys.executable, str(py_file), '--output', str(qir_file)],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                self.log(f"❌ Cirq script failed: {result.stderr}")
                return False
            
            # Test the generated QIR
            return self._test_qir_file(qir_file, "Cirq")
            
        except Exception as e:
            self.log(f"❌ Failed to test Cirq example: {e}")
            return False
    
    def _test_embedded_qir(self):
        """Test with embedded QIR examples from demo."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "qir_bridge_demo", 
            ROOT / "examples" / "qir_bridge_demo.py"
        )
        demo_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(demo_module)
        
        BELL_STATE_QIR = demo_module.BELL_STATE_QIR
        GROVER_ORACLE_QIR = demo_module.GROVER_ORACLE_QIR
        T_CIRCUIT_QIR = demo_module.T_CIRCUIT_QIR
        
        test_cases = [
            ("Bell State", BELL_STATE_QIR),
            ("Grover Oracle", GROVER_ORACLE_QIR),
            ("T Circuit", T_CIRCUIT_QIR)
        ]
        
        all_passed = True
        for name, qir_code in test_cases:
            self.log(f"\n  Testing {name}...")
            
            try:
                # Parse QIR
                parser = QIRParser()
                functions = parser.parse(qir_code)
                
                if not functions:
                    self.log(f"  ❌ No functions parsed")
                    all_passed = False
                    continue
                
                func = list(functions.values())[0]
                self.log(f"  ✓ Parsed function with {len(func.instructions)} instructions")
                
                # Generate QVM graph
                generator = QVMGraphGenerator()
                graph = generator.generate(func)
                
                self.log(f"  ✓ Generated QVM graph with {len(graph['nodes'])} nodes")
                
                # Estimate resources
                estimator = ResourceEstimator()
                estimate = estimator.estimate(func)
                
                self.log(f"  ✓ Estimated {estimate.logical_qubits} logical qubits")
                self.log(f"  ✓ Estimated {estimate.physical_qubits} physical qubits")
                
                self.results.append({
                    'name': name,
                    'source': 'embedded',
                    'status': 'passed',
                    'logical_qubits': estimate.logical_qubits,
                    'physical_qubits': estimate.physical_qubits,
                    'gate_count': estimate.gate_count
                })
                
            except Exception as e:
                self.log(f"  ❌ Failed: {e}")
                all_passed = False
                self.results.append({
                    'name': name,
                    'source': 'embedded',
                    'status': 'failed',
                    'error': str(e)
                })
        
        return all_passed
    
    def _test_qir_file(self, qir_file, source):
        """Test a QIR file."""
        try:
            # Read QIR
            with open(qir_file, 'r') as f:
                qir_code = f.read()
            
            self.log(f"  ✓ Read QIR file ({len(qir_code)} bytes)")
            
            # Parse QIR
            parser = QIRParser()
            functions = parser.parse(qir_code)
            
            if not functions:
                self.log(f"  ❌ No functions parsed")
                return False
            
            func = list(functions.values())[0]
            self.log(f"  ✓ Parsed function with {len(func.instructions)} instructions")
            
            # Generate QVM graph
            generator = QVMGraphGenerator()
            graph = generator.generate(func)
            
            self.log(f"  ✓ Generated QVM graph with {len(graph['nodes'])} nodes")
            
            # Estimate resources
            estimator = ResourceEstimator()
            estimate = estimator.estimate(func)
            
            self.log(f"  ✓ Estimated {estimate.logical_qubits} logical qubits")
            self.log(f"  ✓ Estimated {estimate.physical_qubits} physical qubits")
            
            self.results.append({
                'name': qir_file.stem,
                'source': source,
                'status': 'passed',
                'logical_qubits': estimate.logical_qubits,
                'physical_qubits': estimate.physical_qubits,
                'gate_count': estimate.gate_count
            })
            
            return True
            
        except Exception as e:
            self.log(f"  ❌ Failed: {e}")
            self.results.append({
                'name': qir_file.stem,
                'source': source,
                'status': 'failed',
                'error': str(e)
            })
            return False
    
    def run_all_tests(self):
        """Run all available tests."""
        self.log("\n" + "="*70)
        self.log("QIR PIPELINE INTEGRATION TEST")
        self.log("="*70)
        
        # Detect compilers
        self.log("\nDetecting available compilers...")
        has_qsharp = CompilerDetector.has_qsharp()
        has_qiskit = CompilerDetector.has_qiskit_qir()
        has_cirq = CompilerDetector.has_cirq_qir()
        
        self.log(f"  Q# compiler: {'✓' if has_qsharp else '✗'}")
        self.log(f"  Qiskit QIR: {'✓' if has_qiskit else '✗'}")
        self.log(f"  Cirq QIR: {'✓' if has_cirq else '✗'}")
        
        # Test embedded examples (always available)
        self.log("\n" + "="*70)
        self.log("Testing embedded QIR examples")
        self.log("="*70)
        self._test_embedded_qir()
        
        # Test Qiskit examples if available
        if has_qiskit:
            qiskit_dir = self.qir_examples_dir / 'qiskit'
            for py_file in qiskit_dir.glob('*.py'):
                if py_file.name != '__init__.py':
                    self.test_qiskit_example(py_file)
        
        # Test Cirq examples if available
        if has_cirq:
            cirq_dir = self.qir_examples_dir / 'cirq'
            for py_file in cirq_dir.glob('*.py'):
                if py_file.name != '__init__.py':
                    self.test_cirq_example(py_file)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        self.log("\n" + "="*70)
        self.log("TEST SUMMARY")
        self.log("="*70)
        
        passed = sum(1 for r in self.results if r['status'] == 'passed')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        
        self.log(f"\nTotal tests: {len(self.results)}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        
        if passed > 0:
            self.log("\n✅ Passed tests:")
            for result in self.results:
                if result['status'] == 'passed':
                    self.log(f"  • {result['name']} ({result['source']})")
                    self.log(f"    - {result['logical_qubits']} logical qubits")
                    self.log(f"    - {result['physical_qubits']} physical qubits")
                    self.log(f"    - {result['gate_count']} gates")
        
        if failed > 0:
            self.log("\n❌ Failed tests:")
            for result in self.results:
                if result['status'] == 'failed':
                    self.log(f"  • {result['name']} ({result['source']})")
                    self.log(f"    Error: {result.get('error', 'Unknown')}")
        
        self.log("\n" + "="*70)
        self.log("QIR PIPELINE TEST COMPLETE")
        self.log("="*70)
        
        return failed == 0
    
    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.log(f"\nCleaned up temporary directory: {self.temp_dir}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test QIR pipeline end-to-end')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    args = parser.parse_args()
    
    tester = QIRPipelineTester(verbose=not args.quiet)
    
    try:
        tester.run_all_tests()
        success = all(r['status'] == 'passed' for r in tester.results)
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == '__main__':
    sys.exit(main())
