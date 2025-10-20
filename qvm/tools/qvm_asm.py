#!/usr/bin/env python3
"""
QVM Assembler - Convert QVM assembly language to JSON.

Assembly syntax:
  .version 0.1
  .caps CAP_ALLOC CAP_TELEPORT
  
  ; Comment
  label: OPCODE args... [guard] [caps]
  
Examples:
  alloc: ALLOC_LQ 2, profile="logical:surface_code(d=3)" -> q0, q1 [CAP_ALLOC]
  h1: H q0
  cnot1: CNOT q0, q1
  m1: MEASURE_Z q0 -> m0
  cond: X q1 if m0==1
  free: FREE_LQ q0, q1
"""

import json
import re
import sys
from typing import Dict, List, Any, Tuple, Optional

try:
    from .qvm_asm_macros import preprocess as preprocess_macros
except ImportError:
    from qvm_asm_macros import preprocess as preprocess_macros


class AssemblyParser:
    """Parser for QVM assembly language."""
    
    def __init__(self):
        self.version = "0.1"
        self.caps = []
        self.nodes = []
        self.resources = {"vqs": set(), "chs": set(), "events": set()}
        self.metadata = {}
        self.edges = []
    
    def parse_guard(self, guard_str: str) -> Optional[Dict[str, Any]]:
        """Parse guard condition from 'if event==value' format."""
        if not guard_str:
            return None
        
        guard_str = guard_str.strip()
        if not guard_str.startswith("if "):
            return None
        
        condition = guard_str[3:].strip()
        
        # Handle AND conditions
        if " && " in condition:
            parts = condition.split(" && ")
            conditions = []
            for part in parts:
                match = re.match(r'(\w+)==(\d+)', part.strip())
                if match:
                    conditions.append({
                        "type": "eq",
                        "event": match.group(1),
                        "value": int(match.group(2))
                    })
            return {"type": "and", "conditions": conditions}
        
        # Handle OR conditions
        if " || " in condition:
            parts = condition.split(" || ")
            conditions = []
            for part in parts:
                match = re.match(r'(\w+)==(\d+)', part.strip())
                if match:
                    conditions.append({
                        "type": "eq",
                        "event": match.group(1),
                        "value": int(match.group(2))
                    })
            return {"type": "or", "conditions": conditions}
        
        # Simple equality
        match = re.match(r'(\w+)==(\d+)', condition)
        if match:
            return {
                "event": match.group(1),
                "equals": int(match.group(2))
            }
        
        return None
    
    def parse_args(self, args_str: str) -> Tuple[Dict[str, Any], List[str]]:
        """Parse arguments, separating key=value pairs from positional args."""
        args_dict = {}
        positional = []
        
        if not args_str:
            return args_dict, positional
        
        # Split by comma, but respect quotes
        parts = []
        current = []
        in_quotes = False
        for char in args_str:
            if char == '"':
                in_quotes = not in_quotes
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            parts.append(''.join(current).strip())
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if it's key=value
            if '=' in part and not part.startswith('"'):
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes from value
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                # Try to parse as number
                else:
                    try:
                        # Try int first
                        if '.' not in value:
                            value = int(value)
                        else:
                            value = float(value)
                    except ValueError:
                        # Keep as string if not a valid number
                        pass
                
                args_dict[key] = value
            else:
                positional.append(part)
        
        return args_dict, positional
    
    def parse_line(self, line: str) -> None:
        """Parse a single line of assembly."""
        # Remove comments
        if ';' in line:
            line = line[:line.index(';')]
        
        line = line.strip()
        if not line:
            return
        
        # Directives
        if line.startswith('.'):
            self.parse_directive(line)
            return
        
        # Node definition: label: OPCODE args... -> outputs [guard] [caps]
        if ':' not in line:
            return
        
        label, rest = line.split(':', 1)
        label = label.strip()
        rest = rest.strip()
        
        # Extract caps [CAP_ALLOC, CAP_TELEPORT]
        caps = []
        caps_match = re.search(r'\[([^\]]+)\]$', rest)
        if caps_match:
            caps_str = caps_match.group(1)
            caps = [c.strip() for c in caps_str.split(',')]
            rest = rest[:caps_match.start()].strip()
        
        # Parse opcode first (we need it to interpret outputs correctly)
        # Extract guard (if event==value)
        guard = None
        guard_match = re.search(r'\bif\s+.+$', rest)
        if guard_match:
            guard_str = guard_match.group(0)
            guard = self.parse_guard(guard_str)
            rest = rest[:guard_match.start()].strip()
        
        # Extract outputs (-> out1, out2) but don't process yet
        produces_raw = []
        output_match = re.search(r'->\s*(.+)$', rest)
        if output_match:
            output_str = output_match.group(1)
            produces_raw = [o.strip() for o in output_str.split(',')]
            rest = rest[:output_match.start()].strip()
        
        # Parse opcode and arguments
        parts = rest.split(None, 1)
        if not parts:
            return
        
        opcode = parts[0]
        args_str = parts[1] if len(parts) > 1 else ""
        
        # Now process outputs based on opcode
        produces = []
        if produces_raw:
            if opcode == "ALLOC_LQ":
                # For ALLOC_LQ, outputs are vqs
                for vq in produces_raw:
                    self.resources["vqs"].add(vq)
            else:
                # For other ops (measurements), outputs are events
                produces = produces_raw
                for event in produces:
                    self.resources["events"].add(event)
        
        # Parse arguments
        args_dict, positional = self.parse_args(args_str)
        
        # Build node
        node = {
            "id": label,
            "op": opcode
        }
        
        # Add args dict if present
        if args_dict:
            node["args"] = args_dict
        
        # Classify positional arguments
        vqs = []
        chs = []
        inputs = []
        
        for arg in positional:
            if arg.startswith('ch'):
                chs.append(arg)
                self.resources["chs"].add(arg)
            elif arg.startswith('ev'):
                inputs.append(arg)
                self.resources["events"].add(arg)
            else:
                vqs.append(arg)
                self.resources["vqs"].add(arg)
        
        # For ALLOC_LQ, outputs go in vqs field
        if opcode == "ALLOC_LQ" and produces_raw:
            vqs = produces_raw
        
        if vqs:
            node["vqs"] = vqs
        if chs:
            node["chs"] = chs
        if inputs:
            node["inputs"] = inputs
        if produces:
            node["produces"] = produces
        if guard:
            node["guard"] = guard
        if caps:
            node["caps"] = caps
        
        self.nodes.append(node)
    
    def parse_directive(self, line: str) -> None:
        """Parse a directive line."""
        parts = line.split(None, 1)
        directive = parts[0][1:]  # Remove leading '.'
        value = parts[1] if len(parts) > 1 else ""
        
        if directive == "version":
            self.version = value.strip()
        elif directive == "caps":
            self.caps = value.split()
        elif directive == "metadata":
            # .metadata key=value
            if '=' in value:
                key, val = value.split('=', 1)
                self.metadata[key.strip()] = val.strip().strip('"')
    
    def parse(self, assembly: str) -> Dict[str, Any]:
        """Parse assembly code and return QVM JSON."""
        for line in assembly.split('\n'):
            self.parse_line(line)
        
        # Build QVM JSON
        qvm = {
            "version": self.version,
            "program": {
                "nodes": self.nodes
            },
            "resources": {
                "vqs": sorted(list(self.resources["vqs"])),
                "chs": sorted(list(self.resources["chs"])),
                "events": sorted(list(self.resources["events"]))
            }
        }
        
        if self.caps:
            qvm["caps"] = self.caps
        
        if self.metadata:
            qvm["metadata"] = self.metadata
        
        if self.edges:
            qvm["program"]["edges"] = self.edges
        
        return qvm


def assemble(assembly: str, filename: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Assemble QVM assembly to JSON with macro preprocessing.
    
    Args:
        assembly: Raw assembly code (may contain macros)
        filename: Optional filename for .include resolution
        params: Optional external parameters to override .param defaults
        
    Returns:
        QVM JSON graph
    """
    # Phase 1: Preprocess macros with parameters
    expanded = preprocess_macros(assembly, filename, params)
    
    # Phase 2: Parse expanded assembly
    parser = AssemblyParser()
    return parser.parse(expanded)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: qvm_asm.py <input.qvm.asm> [output.qvm.json]")
        print("\nAssemble QVM assembly language to JSON.")
        print("\nIf output file is not specified, prints to stdout.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load assembly
    try:
        with open(input_file, 'r') as f:
            assembly = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Assemble
    try:
        qvm_json = assemble(assembly)
    except Exception as e:
        print(f"Error: Assembly failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output
    json_str = json.dumps(qvm_json, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(json_str)
            f.write('\n')
        print(f"Assembled to {output_file}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
