"""
Measurement Deferral Pass

Moves measurements to the end of the circuit when possible.

Benefits:
- Enables more gate optimizations (gates after measurement can be optimized)
- Reduces mid-circuit measurement overhead
- Simplifies circuit structure

Rules:
- Can defer if measurement result is not used by subsequent gates
- Cannot defer if measurement controls later operations
- Must preserve measurement order for classical dependencies

Example:
  Before:
    H(q0) → MEASURE(q0) → H(q1) → MEASURE(q1)
  
  After:
    H(q0) → H(q1) → MEASURE(q0) → MEASURE(q1)
    (Measurements moved to end)
"""

import time
from typing import List, Set, Dict
from ..pass_base import OptimizationPass
from ..ir import QIRCircuit, QIRInstruction, QIRQubit


class MeasurementDeferralPass(OptimizationPass):
    """
    Defers measurements to the end of the circuit when safe.
    
    Strategy:
    1. Identify measurements that can be moved
    2. Check for dependencies (measurement results used later)
    3. Move safe measurements to end
    4. Preserve measurement order
    """
    
    def __init__(self):
        super().__init__("MeasurementDeferral")
    
    def run(self, circuit: QIRCircuit) -> QIRCircuit:
        """
        Run measurement deferral on the circuit.
        
        Moves measurements to the end when safe.
        """
        start_time = time.time()
        
        # Find all measurements
        measurements = []
        measurement_indices = []
        
        for i, inst in enumerate(circuit.instructions):
            if inst.is_measurement():
                measurements.append(inst)
                measurement_indices.append(i)
        
        if not measurements:
            self.metrics.execution_time_ms = (time.time() - start_time) * 1000
            return circuit
        
        # Check which measurements can be deferred
        deferrable = []
        
        for i, (meas_inst, meas_idx) in enumerate(zip(measurements, measurement_indices)):
            if self._can_defer(circuit, meas_inst, meas_idx):
                deferrable.append((meas_inst, meas_idx))
        
        # Remove deferrable measurements from their current positions
        # (in reverse order to maintain indices)
        for meas_inst, meas_idx in reversed(deferrable):
            circuit.remove_instruction(meas_idx)
            self.metrics.custom['measurements_deferred'] = \
                self.metrics.custom.get('measurements_deferred', 0) + 1
        
        # Add them at the end
        for meas_inst, _ in deferrable:
            circuit.add_instruction(meas_inst)
        
        self.metrics.execution_time_ms = (time.time() - start_time) * 1000
        
        return circuit
    
    def _can_defer(
        self,
        circuit: QIRCircuit,
        measurement: QIRInstruction,
        meas_idx: int
    ) -> bool:
        """
        Check if a measurement can be safely deferred.
        
        A measurement can be deferred if:
        1. Its result is not used by subsequent operations
        2. The measured qubit is not used in subsequent gates
        3. No classical control dependencies
        
        Args:
            circuit: The circuit
            measurement: The measurement instruction
            meas_idx: Index of the measurement
        
        Returns:
            True if measurement can be deferred
        """
        measured_qubit = measurement.qubits[0]
        result_name = measurement.result
        
        # Check all instructions after this measurement
        for i in range(meas_idx + 1, len(circuit.instructions)):
            inst = circuit.instructions[i]
            
            # Check if measurement result is used (classical control)
            # For now, we assume no classical control if not explicitly marked
            # In a full implementation, we'd check for conditional gates
            
            # Check if measured qubit is used in subsequent gates
            if inst.is_gate() and measured_qubit in inst.qubits:
                # Qubit is used after measurement - cannot defer
                return False
        
        return True
    
    def should_run(self, circuit: QIRCircuit) -> bool:
        """Only run if there are measurements."""
        has_measurements = any(inst.is_measurement() for inst in circuit.instructions)
        return self.enabled and has_measurements
