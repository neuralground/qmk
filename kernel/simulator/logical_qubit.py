"""
Logical Qubit Abstraction

Represents a logical qubit protected by quantum error correction.
Tracks logical state, error syndrome, and QEC code parameters.
"""

import random
from typing import Optional, List, Tuple
from enum import Enum

from .qec_profiles import QECProfile
from .error_models import CompositeErrorModel, ErrorEvent


class LogicalState(Enum):
    """Logical qubit computational basis states."""
    ZERO = 0
    ONE = 1
    PLUS = 2   # |+⟩ = (|0⟩ + |1⟩)/√2
    MINUS = 3  # |-⟩ = (|0⟩ - |1⟩)/√2


class LogicalQubit:
    """
    Logical qubit with QEC protection.
    
    Simulates a logical qubit encoded in a quantum error correction code.
    Tracks:
    - Logical state (simplified: computational basis + superpositions)
    - Error syndrome (accumulated errors)
    - QEC profile (code distance, physical resources)
    - Error model (noise sources)
    """
    
    def __init__(self, qubit_id: str, profile: QECProfile, seed: Optional[int] = None):
        self.qubit_id = qubit_id
        self.profile = profile
        self.rng = random.Random(seed)
        
        # Logical state (simplified model)
        self.state = LogicalState.ZERO
        self.phase = 0.0  # Global phase (not observable, but tracked)
        
        # Error tracking
        self.error_model = CompositeErrorModel(
            gate_error_rate=profile.physical_gate_error_rate,
            measurement_error_rate=profile.measurement_error_rate,
            idle_error_rate=profile.idle_error_rate,
            t1_us=profile.t1_us,
            t2_us=profile.t2_us,
            seed=seed
        )
        
        # Syndrome tracking (simplified: count of uncorrected errors)
        self.syndrome_weight = 0
        self.decoder_cycles = 0
        
        # Timing
        self.current_time_us = 0.0
        self.last_gate_time_us = 0.0
        
        # Statistics
        self.gate_count = 0
        self.measurement_count = 0
        self.correction_count = 0
    
    def apply_gate(self, gate_type: str, time_us: float):
        """
        Apply a logical gate operation.
        
        Args:
            gate_type: Gate name (H, S, X, Y, Z, etc.)
            time_us: Time of operation
        """
        # Apply idle errors since last operation
        idle_duration = time_us - self.last_gate_time_us
        if idle_duration > 0:
            self.error_model.apply_idle_errors(
                self.qubit_id, idle_duration, self.last_gate_time_us
            )
        
        # Apply gate errors
        error = self.error_model.apply_gate_errors(self.qubit_id, time_us)
        if error:
            self.syndrome_weight += 1
        
        # Update logical state (simplified unitary evolution)
        self._apply_logical_gate(gate_type)
        
        # Run decoder cycle
        self._run_decoder_cycle()
        
        # Update timing and stats
        self.current_time_us = time_us + self.profile.logical_cycle_time_us
        self.last_gate_time_us = self.current_time_us
        self.gate_count += 1
    
    def measure(self, basis: str, time_us: float) -> int:
        """
        Measure the logical qubit.
        
        Args:
            basis: Measurement basis ("Z" or "X")
            time_us: Measurement time
        
        Returns:
            Measurement outcome (0 or 1)
        """
        # Apply idle errors
        idle_duration = time_us - self.last_gate_time_us
        if idle_duration > 0:
            self.error_model.apply_idle_errors(
                self.qubit_id, idle_duration, self.last_gate_time_us
            )
        
        # Determine true outcome based on logical state
        if basis == "Z":
            true_outcome = self._measure_z()
        elif basis == "X":
            true_outcome = self._measure_x()
        else:
            raise ValueError(f"Unknown measurement basis: {basis}")
        
        # Apply measurement errors
        observed_outcome = self.error_model.apply_measurement_errors(
            self.qubit_id, true_outcome, time_us
        )
        
        # Measurement is destructive (collapses to computational basis)
        self.state = LogicalState.ZERO if observed_outcome == 0 else LogicalState.ONE
        
        # Update timing and stats
        self.current_time_us = time_us + self.profile.logical_cycle_time_us
        self.last_gate_time_us = self.current_time_us
        self.measurement_count += 1
        
        return observed_outcome
    
    def reset(self, time_us: float):
        """Reset qubit to |0⟩ state."""
        self.state = LogicalState.ZERO
        self.phase = 0.0
        self.syndrome_weight = 0
        self.current_time_us = time_us + self.profile.logical_cycle_time_us
        self.last_gate_time_us = self.current_time_us
    
    def get_logical_error_probability(self) -> float:
        """
        Get current logical error probability.
        
        Returns:
            Probability of uncorrected logical error
        """
        return self.profile.logical_error_rate()
    
    def get_telemetry(self) -> dict:
        """
        Get telemetry data for this logical qubit.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "qubit_id": self.qubit_id,
            "profile": self.profile.code_family,
            "distance": self.profile.code_distance,
            "physical_qubits": self.profile.physical_qubit_count,
            "gate_count": self.gate_count,
            "measurement_count": self.measurement_count,
            "decoder_cycles": self.decoder_cycles,
            "correction_count": self.correction_count,
            "syndrome_weight": self.syndrome_weight,
            "error_breakdown": self.error_model.get_error_breakdown(),
            "logical_error_rate": self.get_logical_error_probability(),
            "total_time_us": self.current_time_us
        }
    
    # Private methods
    
    def _apply_logical_gate(self, gate_type: str):
        """Apply logical gate to state (simplified model)."""
        if gate_type == "H":
            # Hadamard: |0⟩ ↔ |+⟩, |1⟩ ↔ |-⟩
            if self.state == LogicalState.ZERO:
                self.state = LogicalState.PLUS
            elif self.state == LogicalState.ONE:
                self.state = LogicalState.MINUS
            elif self.state == LogicalState.PLUS:
                self.state = LogicalState.ZERO
            elif self.state == LogicalState.MINUS:
                self.state = LogicalState.ONE
        
        elif gate_type == "X":
            # Bit flip: |0⟩ ↔ |1⟩, |+⟩ → |+⟩, |-⟩ → |-⟩
            if self.state == LogicalState.ZERO:
                self.state = LogicalState.ONE
            elif self.state == LogicalState.ONE:
                self.state = LogicalState.ZERO
        
        elif gate_type == "Z":
            # Phase flip: |+⟩ ↔ |-⟩, |0⟩ → |0⟩, |1⟩ → -|1⟩
            if self.state == LogicalState.PLUS:
                self.state = LogicalState.MINUS
            elif self.state == LogicalState.MINUS:
                self.state = LogicalState.PLUS
            elif self.state == LogicalState.ONE:
                self.phase += 3.14159  # π phase
        
        elif gate_type == "Y":
            # Y = iXZ
            self._apply_logical_gate("X")
            self._apply_logical_gate("Z")
        
        elif gate_type == "S":
            # S = √Z: |0⟩ → |0⟩, |1⟩ → i|1⟩
            if self.state == LogicalState.ONE:
                self.phase += 1.5708  # π/2 phase
            elif self.state == LogicalState.PLUS:
                # |+⟩ → (|0⟩ + i|1⟩)/√2
                pass  # Simplified: stays in superposition
    
    def _measure_z(self) -> int:
        """Measure in Z basis (computational basis)."""
        if self.state == LogicalState.ZERO:
            return 0
        elif self.state == LogicalState.ONE:
            return 1
        elif self.state in [LogicalState.PLUS, LogicalState.MINUS]:
            # Superposition: 50/50 outcome
            return self.rng.randint(0, 1)
        return 0
    
    def _measure_x(self) -> int:
        """Measure in X basis (Hadamard basis)."""
        if self.state == LogicalState.PLUS:
            return 0
        elif self.state == LogicalState.MINUS:
            return 1
        elif self.state in [LogicalState.ZERO, LogicalState.ONE]:
            # Computational basis: 50/50 in X basis
            return self.rng.randint(0, 1)
        return 0
    
    def _run_decoder_cycle(self):
        """
        Run a decoder cycle to correct errors.
        
        Simplified model: decoder succeeds if syndrome weight is below threshold.
        """
        self.decoder_cycles += 1
        
        # Decoder threshold: roughly d/2 errors can be corrected
        threshold = self.profile.code_distance // 2
        
        if self.syndrome_weight > 0:
            if self.syndrome_weight <= threshold:
                # Successful correction
                self.syndrome_weight = 0
                self.correction_count += 1
            else:
                # Decoder failure (logical error)
                # In real system, this would cause logical error
                # For simulation, we just track it
                pass


class TwoQubitGate:
    """Helper for two-qubit gate operations."""
    
    @staticmethod
    def apply_cnot(control: LogicalQubit, target: LogicalQubit, time_us: float):
        """
        Apply CNOT gate between two logical qubits.
        
        Args:
            control: Control qubit
            target: Target qubit
            time_us: Operation time
        """
        # Simplified CNOT: if control is |1⟩, flip target
        control_outcome = control._measure_z()  # Peek at control state
        
        if control_outcome == 1:
            target._apply_logical_gate("X")
        
        # Apply errors to both qubits
        control.error_model.apply_gate_errors(control.qubit_id, time_us)
        target.error_model.apply_gate_errors(target.qubit_id, time_us)
        
        # Run decoder cycles
        control._run_decoder_cycle()
        target._run_decoder_cycle()
        
        # Update timing
        cycle_time = max(control.profile.logical_cycle_time_us, 
                        target.profile.logical_cycle_time_us)
        control.current_time_us = time_us + cycle_time
        target.current_time_us = time_us + cycle_time
        control.last_gate_time_us = control.current_time_us
        target.last_gate_time_us = target.current_time_us
        
        control.gate_count += 1
        target.gate_count += 1
