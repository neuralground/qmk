#!/usr/bin/env python3
"""
Update imports for domain refactoring.

This script updates import statements to reflect the new domain structure.
"""

import os
import re
from pathlib import Path

# Define import replacements
REPLACEMENTS = {
    # QIR domain
    'from kernel.qir_bridge.optimizer': 'from qir.optimizer',
    'from kernel.qir_bridge.qiskit_to_qir': 'from qir.translators.qiskit_to_qir',
    'from kernel.qir_bridge.cirq_to_qir': 'from qir.translators.cirq_to_qir',
    'from kernel.qir_bridge.qir_parser': 'from qir.parser.qir_parser',
    'import kernel.qir_bridge.optimizer': 'import qir.optimizer',
    
    # QVM domain
    'from kernel.qir_bridge.qvm_generator': 'from qvm.generator.qvm_generator',
    'import kernel.qir_bridge.qvm_generator': 'import qvm.generator.qvm_generator',
    
    # QMK domain - core
    'from kernel.qmk_server': 'from kernel.core.qmk_server',
    'from kernel.session_manager': 'from kernel.core.session_manager',
    'from kernel.job_manager': 'from kernel.core.job_manager',
    'from kernel.rpc_server': 'from kernel.core.rpc_server',
    'import kernel.qmk_server': 'import kernel.core.qmk_server',
    'import kernel.session_manager': 'import kernel.core.session_manager',
    'import kernel.job_manager': 'import kernel.core.job_manager',
    
    # QMK domain - executor
    'from kernel.simulator.enhanced_executor': 'from kernel.executor.enhanced_executor',
    'from kernel.simulator.resource_manager': 'from kernel.executor.resource_manager',
    'import kernel.simulator.enhanced_executor': 'import kernel.executor.enhanced_executor',
    'import kernel.simulator.resource_manager': 'import kernel.executor.resource_manager',
}

def update_file(filepath):
    """Update imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for old, new in REPLACEMENTS.items():
            content = content.replace(old, new)
        
        # Only write if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error updating {filepath}: {e}")
        return False

def main():
    """Update all Python files in the repository."""
    root = Path(__file__).parent.parent
    updated_count = 0
    
    # Directories to scan
    scan_dirs = [
        root / 'qir',
        root / 'qvm',
        root / 'kernel',
        root / 'tests',
        root / 'examples',
    ]
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
            
        for filepath in scan_dir.rglob('*.py'):
            if update_file(filepath):
                updated_count += 1
    
    print(f"\n{'='*60}")
    print(f"Import update complete!")
    print(f"Files updated: {updated_count}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
