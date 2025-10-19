#!/usr/bin/env python3
"""
QVM Disassembler - Convert QVM JSON to assembly language.

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
import sys
from typing import Dict, List, Any


def format_guard(guard: Dict[str, Any]) -> str:
    """Format a guard condition."""
    if not guard:
        return ""
    
    guard_type = guard.get("type", "eq")
    
    if guard_type == "eq":
        event = guard["event"]
        value = guard.get("equals", guard.get("value", 0))
        return f"if {event}=={value}"
    elif guard_type == "and":
        conditions = guard.get("conditions", [])
        parts = []
        for cond in conditions:
            event = cond["event"]
            value = cond.get("equals", cond.get("value", 0))
            parts.append(f"{event}=={value}")
        return f"if {' && '.join(parts)}"
    elif guard_type == "or":
        conditions = guard.get("conditions", [])
        parts = []
        for cond in conditions:
            event = cond["event"]
            value = cond.get("equals", cond.get("value", 0))
            parts.append(f"{event}=={value}")
        return f"if {' || '.join(parts)}"
    
    return ""


def format_args(args: Dict[str, Any]) -> str:
    """Format operation arguments."""
    if not args:
        return ""
    
    parts = []
    for key, value in args.items():
        if isinstance(value, str):
            parts.append(f'{key}="{value}"')
        else:
            parts.append(f'{key}={value}')
    
    return ", ".join(parts)


def format_node(node: Dict[str, Any]) -> str:
    """Format a single node as assembly."""
    node_id = node["id"]
    op = node["op"]
    
    # Build operands
    operands = []
    
    # Add args first (for ALLOC_LQ, etc.)
    args = node.get("args", {})
    if args:
        operands.append(format_args(args))
    
    # Add vqs (qubits)
    vqs = node.get("vqs", [])
    if vqs:
        operands.extend(vqs)
    
    # Add chs (channels)
    chs = node.get("chs", [])
    if chs:
        operands.extend(chs)
    
    # Add inputs
    inputs = node.get("inputs", [])
    if inputs:
        operands.extend(inputs)
    
    # Build output part
    output_part = ""
    produces = node.get("produces", [])
    if produces:
        output_part = f" -> {', '.join(produces)}"
    
    # Build guard part
    guard_part = ""
    guard = node.get("guard")
    if guard:
        guard_part = f" {format_guard(guard)}"
    
    # Build caps part
    caps_part = ""
    caps = node.get("caps", [])
    if caps:
        caps_part = f" [{', '.join(caps)}]"
    
    # Assemble the line
    operand_str = ", ".join(operands) if operands else ""
    
    return f"{node_id}: {op} {operand_str}{output_part}{guard_part}{caps_part}".rstrip()


def disassemble(qvm_json: Dict[str, Any]) -> str:
    """Disassemble QVM JSON to assembly language."""
    lines = []
    
    # Header
    version = qvm_json.get("version", "0.1")
    lines.append(f".version {version}")
    lines.append("")
    
    # Metadata
    metadata = qvm_json.get("metadata", {})
    if metadata:
        lines.append("; Metadata")
        for key, value in metadata.items():
            lines.append(f"; {key}: {value}")
        lines.append("")
    
    # Capabilities
    caps = qvm_json.get("caps", [])
    if caps:
        lines.append(f".caps {' '.join(caps)}")
        lines.append("")
    
    # Resources declaration
    resources = qvm_json.get("resources", {})
    if resources:
        lines.append("; Resources")
        vqs = resources.get("vqs", [])
        if vqs:
            lines.append(f"; vqs: {', '.join(vqs)}")
        chs = resources.get("chs", [])
        if chs:
            lines.append(f"; chs: {', '.join(chs)}")
        events = resources.get("events", [])
        if events:
            lines.append(f"; events: {', '.join(events)}")
        lines.append("")
    
    # Program nodes
    program = qvm_json.get("program", {})
    nodes = program.get("nodes", [])
    
    if nodes:
        lines.append("; Program")
        for node in nodes:
            lines.append(format_node(node))
        lines.append("")
    
    # Edges (if any)
    edges = program.get("edges", [])
    if edges:
        lines.append("; Edges")
        for edge in edges:
            src = edge.get("from", edge.get("src"))
            dst = edge.get("to", edge.get("dst"))
            lines.append(f"; {src} -> {dst}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: qvm_disasm.py <input.qvm.json> [output.qvm.asm]")
        print("\nDisassemble QVM JSON to assembly language.")
        print("\nIf output file is not specified, prints to stdout.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load JSON
    try:
        with open(input_file, 'r') as f:
            qvm_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Disassemble
    assembly = disassemble(qvm_json)
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            f.write(assembly)
        print(f"Disassembled to {output_file}")
    else:
        print(assembly)


if __name__ == "__main__":
    main()
