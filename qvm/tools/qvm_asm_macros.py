#!/usr/bin/env python3
"""
QVM Assembly Macro Preprocessor

Supports:
- .for loops with range and list iteration
- .if/.else/.endif conditionals
- .set variable definitions
- .macro/.endmacro definitions
- Variable substitution with {var}
- .include file inclusion

Example:
    .set n_qubits = 4
    
    .for i in 0..n_qubits-1
        h{i}: APPLY_H q{i}
    .endfor
    
    .macro BELL_PAIR(q0, q1)
        h: APPLY_H {q0}
        cnot: APPLY_CNOT {q0}, {q1}
    .endmacro
    
    BELL_PAIR(q0, q1)
"""

import re
import math
from typing import Dict, List, Any, Optional
from pathlib import Path


class MacroPreprocessor:
    """Preprocessor for QVM assembly macros."""
    
    def __init__(self):
        self.variables = {}
        self.macros = {}
        self.include_paths = [Path("."), Path(__file__).parent.parent / "asm"]
        
    def preprocess(self, assembly: str, filename: Optional[str] = None) -> str:
        """
        Preprocess assembly code to expand macros.
        
        Args:
            assembly: Raw assembly code
            filename: Optional filename for .include resolution
            
        Returns:
            Expanded assembly code
        """
        if filename:
            self.include_paths.insert(0, Path(filename).parent)
        
        lines = assembly.split('\n')
        
        # Phase 1: Process .include directives
        lines = self._process_includes(lines)
        
        # Phase 2: Parse .macro definitions (remove from output)
        lines = self._parse_macros(lines)
        
        # Phase 3: Process .set directives and expand variables
        lines = self._process_variables(lines)
        
        # Phase 4: Process .for loops
        lines = self._process_loops(lines)
        
        # Phase 5: Process .if conditionals
        lines = self._process_conditionals(lines)
        
        # Phase 6: Expand macro calls
        lines = self._expand_macro_calls(lines)
        
        # Phase 7: Final variable substitution
        lines = self._substitute_variables(lines)
        
        return '\n'.join(lines)
    
    def _process_includes(self, lines: List[str]) -> List[str]:
        """Process .include directives."""
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('.include'):
                # Extract filename
                match = re.match(r'\.include\s+"([^"]+)"', stripped)
                if match:
                    filename = match.group(1)
                    # Find file in include paths
                    for include_path in self.include_paths:
                        filepath = include_path / filename
                        if filepath.exists():
                            with open(filepath, 'r') as f:
                                included = f.read()
                            # Recursively preprocess included file
                            included_lines = self.preprocess(included, str(filepath)).split('\n')
                            result.extend(included_lines)
                            break
                    else:
                        raise FileNotFoundError(f"Include file not found: {filename}")
            else:
                result.append(line)
        return result
    
    def _parse_macros(self, lines: List[str]) -> List[str]:
        """Parse and store macro definitions, remove from output."""
        result = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith('.macro'):
                # Parse macro definition
                match = re.match(r'\.macro\s+(\w+)\((.*?)\)', stripped)
                if match:
                    name = match.group(1)
                    params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                    
                    # Collect macro body until .endmacro
                    body = []
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('.endmacro'):
                        body.append(lines[i])
                        i += 1
                    
                    self.macros[name] = {'params': params, 'body': body}
                i += 1
            else:
                result.append(lines[i])
                i += 1
        return result
    
    def _process_variables(self, lines: List[str]) -> List[str]:
        """Process .set directives and store variables."""
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('.set'):
                # Parse variable assignment
                match = re.match(r'\.set\s+(\w+)\s*=\s*(.+)', stripped)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    
                    # First, substitute any variables in the expression
                    # This handles cases like ".set next = i + 1" where i is a loop variable
                    var_value_substituted = re.sub(r'\{([^}]+)\}', 
                        lambda m: str(self.variables.get(m.group(1), m.group(0))), 
                        var_value)
                    
                    # Also substitute bare variable names (not in braces)
                    # Sort variables by length (longest first) to avoid partial matches
                    for var in sorted(self.variables.keys(), key=len, reverse=True):
                        # Use word boundaries to avoid partial matches
                        # Only substitute if not already part of another word
                        pattern = r'(?<![a-zA-Z_])' + re.escape(var) + r'(?![a-zA-Z_0-9])'
                        var_value_substituted = re.sub(pattern, 
                            str(self.variables[var]), 
                            var_value_substituted)
                    
                    # Evaluate the expression
                    try:
                        # Support basic Python expressions
                        self.variables[var_name] = eval(var_value_substituted, {"__builtins__": {}, "pi": math.pi, "math": math}, self.variables)
                    except Exception as e:
                        # If evaluation fails (e.g., undefined variable), keep the .set line for later processing
                        # This happens when .set is inside a loop and references the loop variable
                        # DEBUG: Keeping .set line for later processing in loop
                        result.append(line)  # Keep the original .set line
            else:
                result.append(line)
        return result
    
    def _process_loops(self, lines: List[str]) -> List[str]:
        """Process .for loops."""
        result = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith('.for'):
                # Parse for loop
                match = re.match(r'\.for\s+(\w+)\s+in\s+(.+)', stripped)
                if match:
                    var_name = match.group(1)
                    iterable_expr = match.group(2).strip()
                    
                    # Collect loop body
                    body = []
                    i += 1
                    depth = 1
                    while i < len(lines) and depth > 0:
                        if lines[i].strip().startswith('.for'):
                            depth += 1
                        elif lines[i].strip().startswith('.endfor'):
                            depth -= 1
                            if depth == 0:
                                break
                        body.append(lines[i])
                        i += 1
                    
                    # Evaluate iterable
                    iterable = self._evaluate_iterable(iterable_expr)
                    
                    # Expand loop body for each iteration
                    for value in iterable:
                        # Save current variable state
                        vars_before = set(self.variables.keys())
                        old_value = self.variables.get(var_name)
                        self.variables[var_name] = value
                        
                        # Process body: substitute variables, process .set, then process nested constructs
                        expanded_body = self._substitute_variables(body)
                        expanded_body = self._process_variables(expanded_body)  # Process .set inside loop
                        expanded_body = self._process_loops(expanded_body)  # Process nested loops
                        expanded_body = self._substitute_variables(expanded_body)  # Final substitution
                        result.extend(expanded_body)
                        
                        # Restore variable state: remove variables added during this iteration
                        vars_after = set(self.variables.keys())
                        vars_added = vars_after - vars_before
                        for added_var in vars_added:
                            if added_var != var_name:  # Don't remove the loop variable yet
                                self.variables.pop(added_var, None)
                        
                        # Restore loop variable
                        if old_value is not None:
                            self.variables[var_name] = old_value
                        else:
                            self.variables.pop(var_name, None)
                i += 1
            else:
                result.append(lines[i])
                i += 1
        return result
    
    def _evaluate_iterable(self, expr: str) -> List[Any]:
        """Evaluate an iterable expression."""
        # Handle range syntax: 0..n-1
        if '..' in expr:
            match = re.match(r'(\d+|[\w\+\-\*/]+)\.\.(\d+|[\w\+\-\*/]+)', expr)
            if match:
                try:
                    start = eval(match.group(1), {"__builtins__": {}}, self.variables)
                    end = eval(match.group(2), {"__builtins__": {}}, self.variables)
                    return list(range(int(start), int(end) + 1))
                except:
                    pass
        
        # Handle list literals or variable references
        try:
            return eval(expr, {"__builtins__": {}, "range": range}, self.variables)
        except:
            return []
    
    def _process_conditionals(self, lines: List[str]) -> List[str]:
        """Process .if/.else/.endif conditionals."""
        result = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith('.if'):
                # Parse condition
                match = re.match(r'\.if\s+(.+)', stripped)
                if match:
                    condition = match.group(1).strip()
                    
                    # Collect if body
                    if_body = []
                    else_body = []
                    i += 1
                    depth = 1
                    in_else = False
                    
                    while i < len(lines) and depth > 0:
                        line_stripped = lines[i].strip()
                        if line_stripped.startswith('.if'):
                            depth += 1
                        elif line_stripped.startswith('.else') and depth == 1:
                            in_else = True
                            i += 1
                            continue
                        elif line_stripped.startswith('.endif'):
                            depth -= 1
                            if depth == 0:
                                break
                        
                        if in_else:
                            else_body.append(lines[i])
                        else:
                            if_body.append(lines[i])
                        i += 1
                    
                    # Evaluate condition
                    try:
                        condition_result = eval(condition, {"__builtins__": {}}, self.variables)
                        if condition_result:
                            result.extend(self._process_conditionals(if_body))
                        else:
                            result.extend(self._process_conditionals(else_body))
                    except:
                        # If evaluation fails, include if body by default
                        result.extend(self._process_conditionals(if_body))
                i += 1
            else:
                result.append(lines[i])
                i += 1
        return result
    
    def _expand_macro_calls(self, lines: List[str]) -> List[str]:
        """Expand macro calls."""
        result = []
        for line in lines:
            stripped = line.strip()
            # Check if line is a macro call
            match = re.match(r'(\w+)\((.*?)\)', stripped)
            if match and match.group(1) in self.macros:
                macro_name = match.group(1)
                args = [a.strip().strip('"') for a in match.group(2).split(',') if a.strip()]
                
                macro = self.macros[macro_name]
                
                # Create parameter bindings
                old_values = {}
                for param, arg in zip(macro['params'], args):
                    old_values[param] = self.variables.get(param)
                    self.variables[param] = arg
                
                # Expand macro body
                expanded = self._substitute_variables(macro['body'])
                result.extend(expanded)
                
                # Restore old values
                for param, old_value in old_values.items():
                    if old_value is not None:
                        self.variables[param] = old_value
                    else:
                        self.variables.pop(param, None)
            else:
                result.append(line)
        return result
    
    def _substitute_variables(self, lines: List[str]) -> List[str]:
        """Substitute {var} and {expr} with variable values."""
        result = []
        for line in lines:
            # Find all {expr} patterns (including array indexing, arithmetic, etc.)
            def replace_expr(match):
                expr = match.group(1)
                try:
                    # Try to evaluate the expression
                    value = eval(expr, {"__builtins__": {}, "math": __import__('math')}, self.variables)
                    return str(value)
                except:
                    # If evaluation fails, try simple variable lookup
                    if expr in self.variables:
                        return str(self.variables[expr])
                    return match.group(0)
            
            # Match {anything} where anything can include brackets, dots, etc.
            expanded = re.sub(r'\{([^}]+)\}', replace_expr, line)
            result.append(expanded)
        return result


def preprocess(assembly: str, filename: Optional[str] = None) -> str:
    """
    Preprocess QVM assembly with macro expansion.
    
    Args:
        assembly: Raw assembly code
        filename: Optional filename for .include resolution
        
    Returns:
        Expanded assembly code
    """
    preprocessor = MacroPreprocessor()
    return preprocessor.preprocess(assembly, filename)
