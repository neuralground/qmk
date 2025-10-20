#!/usr/bin/env python3
"""
ASM Runner - Utility for loading and executing QVM Assembly files

This module provides helper functions to load .qvm.asm files,
substitute parameters, and execute them via the QSyscall client.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.client.qsyscall_client import QSyscallClient
from qvm.tools.qvm_asm import assemble


def load_asm_file(filename: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Load an ASM file and substitute parameters.
    
    Args:
        filename: Path to .qvm.asm file (relative to examples/asm/)
        params: Dictionary of parameters to substitute
        
    Returns:
        ASM code with parameters substituted
    """
    asm_dir = Path(__file__).parent / "asm"
    filepath = asm_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"ASM file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        asm = f.read()
    
    # Substitute parameters if provided
    if params:
        # Add parameters as .set directives at the top
        param_lines = []
        for key, value in params.items():
            if isinstance(value, str):
                param_lines.append(f'.set {key} = "{value}"')
            elif isinstance(value, list):
                param_lines.append(f'.set {key} = {value}')
            else:
                param_lines.append(f'.set {key} = {value}')
        
        # Insert after .version and .caps lines
        lines = asm.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('.caps'):
                insert_idx = i + 1
                break
        
        lines = lines[:insert_idx] + [''] + param_lines + [''] + lines[insert_idx:]
        asm = '\n'.join(lines)
    
    return asm


def assemble_file(filename: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load and assemble an ASM file.
    
    Args:
        filename: Path to .qvm.asm file
        params: Dictionary of parameters to substitute
        
    Returns:
        QVM JSON graph
    """
    asm = load_asm_file(filename, params)
    return assemble(asm)


def execute_asm_file(
    client: QSyscallClient,
    filename: str,
    params: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Load, assemble, and execute an ASM file.
    
    Args:
        client: QSyscall client
        filename: Path to .qvm.asm file
        params: Dictionary of parameters to substitute
        **kwargs: Additional arguments for submit_and_wait
        
    Returns:
        Job result dictionary
    """
    graph = assemble_file(filename, params)
    return client.submit_and_wait(graph, **kwargs)


# Convenience function for common use case
def run_circuit(filename: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """
    Quick function to run a circuit from an ASM file.
    
    Args:
        filename: Path to .qvm.asm file
        params: Dictionary of parameters
        **kwargs: Additional arguments for submit_and_wait
        
    Returns:
        Job result dictionary
    """
    client = QSyscallClient(socket_path="/tmp/qmk.sock")
    
    # Negotiate capabilities
    client.negotiate_capabilities([
        "CAP_ALLOC",
        "CAP_COMPUTE",
        "CAP_MEASURE"
    ])
    
    return execute_asm_file(client, filename, params, **kwargs)


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: asm_runner.py <file.qvm.asm> [param=value ...]")
        print("\nExample:")
        print("  asm_runner.py ghz_state.qvm.asm n_qubits=4")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Parse parameters from command line
    params = {}
    for arg in sys.argv[2:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Try to evaluate as Python literal
            try:
                params[key] = eval(value)
            except:
                params[key] = value
    
    print(f"Running {filename} with params: {params}")
    result = run_circuit(filename, params)
    
    print(f"\nStatus: {result['state']}")
    print(f"Events: {result.get('events', {})}")
