"""
Error Models for Logical Qubit Simulation

Implements various noise models for simulating errors in quantum systems:
- Depolarizing noise
- Coherence errors (T1, T2)
- Gate fidelity
- Measurement errors
"""

import random
from typing import Optional
from dataclasses import dataclass


@dataclass
class ErrorEvent:
    """Represents a single error event."""
    error_type: str  # "X", "Y", "Z", "measurement", "idle"
    qubit_id: str
    time_us: float
    corrected: bool = False


class ErrorModel:
    """Base class for error models."""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.error_history = []
    
    def sample_error(self, error_rate: float) -> bool:
        """Sample whether an error occurs given an error rate."""
        return self.rng.random() < error_rate
    
    def record_error(self, event: ErrorEvent):
        """Record an error event for telemetry."""
        self.error_history.append(event)
    
    def get_error_count(self) -> int:
        """Get total number of errors."""
        return len(self.error_history)
    
    def get_uncorrected_errors(self) -> int:
        """Get number of uncorrected errors."""
        return sum(1 for e in self.error_history if not e.corrected)


class DepolarizingNoise(ErrorModel):
    """
    Depolarizing noise model.
    
    With probability p, applies a random Pauli error (X, Y, or Z).
    Models worst-case noise where all error types are equally likely.
    """
    
    def apply_gate_noise(self, qubit_id: str, gate_error_rate: float, time_us: float) -> Optional[str]:
        """
        Apply depolarizing noise during a gate operation.
        
        Args:
            qubit_id: Qubit identifier
            gate_error_rate: Probability of error
            time_us: Time of operation
        
        Returns:
            Pauli error type ("X", "Y", "Z") or None if no error
        """
        if self.sample_error(gate_error_rate):
            # Uniform distribution over X, Y, Z
            error_type = self.rng.choice(["X", "Y", "Z"])
            self.record_error(ErrorEvent(error_type, qubit_id, time_us))
            return error_type
        return None
    
    def apply_idle_noise(self, qubit_id: str, idle_error_rate: float, 
                        duration_us: float, time_us: float) -> Optional[str]:
        """
        Apply depolarizing noise during idle time.
        
        Args:
            qubit_id: Qubit identifier
            idle_error_rate: Error rate per microsecond
            duration_us: Idle duration
            time_us: Start time
        
        Returns:
            Pauli error type or None
        """
        # Probability scales with duration
        total_error_prob = 1 - (1 - idle_error_rate) ** duration_us
        
        if self.sample_error(total_error_prob):
            error_type = self.rng.choice(["X", "Y", "Z"])
            self.record_error(ErrorEvent(error_type, qubit_id, time_us))
            return error_type
        return None


class CoherenceNoise(ErrorModel):
    """
    Coherence noise model with T1 (amplitude damping) and T2 (dephasing).
    
    T1: Energy relaxation time (|1⟩ → |0⟩)
    T2: Dephasing time (loss of phase coherence)
    
    Note: T2 ≤ 2*T1 always (T2 includes T1 effects)
    """
    
    def __init__(self, t1_us: float, t2_us: float, seed: Optional[int] = None):
        super().__init__(seed)
        self.t1_us = t1_us
        self.t2_us = t2_us
        
        if t2_us > 2 * t1_us:
            raise ValueError(f"T2 ({t2_us}) cannot exceed 2*T1 ({2*t1_us})")
    
    def apply_t1_decay(self, qubit_id: str, duration_us: float, time_us: float) -> bool:
        """
        Apply T1 amplitude damping.
        
        Probability of |1⟩ → |0⟩ decay: 1 - exp(-t/T1)
        
        Args:
            qubit_id: Qubit identifier
            duration_us: Time duration
            time_us: Current time
        
        Returns:
            True if decay occurred
        """
        import math
        decay_prob = 1 - math.exp(-duration_us / self.t1_us)
        
        if self.sample_error(decay_prob):
            # T1 decay is effectively a bit-flip on |1⟩ state
            self.record_error(ErrorEvent("T1_decay", qubit_id, time_us))
            return True
        return False
    
    def apply_t2_dephasing(self, qubit_id: str, duration_us: float, time_us: float) -> bool:
        """
        Apply T2 dephasing (pure dephasing beyond T1 effects).
        
        Pure dephasing time: T_phi = 1/(1/T2 - 1/(2*T1))
        
        Args:
            qubit_id: Qubit identifier
            duration_us: Time duration
            time_us: Current time
        
        Returns:
            True if dephasing occurred
        """
        import math
        
        # Pure dephasing rate
        t_phi = 1 / (1/self.t2_us - 1/(2*self.t1_us)) if self.t2_us < 2*self.t1_us else float('inf')
        
        if t_phi != float('inf'):
            dephase_prob = 1 - math.exp(-duration_us / t_phi)
            
            if self.sample_error(dephase_prob):
                # Dephasing is a Z error
                self.record_error(ErrorEvent("T2_dephasing", qubit_id, time_us))
                return True
        return False


class MeasurementNoise(ErrorModel):
    """
    Measurement error model.
    
    Models readout errors where measurement outcome is flipped.
    """
    
    def apply_measurement_error(self, qubit_id: str, true_outcome: int, 
                               measurement_error_rate: float, time_us: float) -> int:
        """
        Apply measurement readout error.
        
        Args:
            qubit_id: Qubit identifier
            true_outcome: True measurement outcome (0 or 1)
            measurement_error_rate: Probability of bit flip
            time_us: Measurement time
        
        Returns:
            Observed measurement outcome (possibly flipped)
        """
        if self.sample_error(measurement_error_rate):
            self.record_error(ErrorEvent("measurement", qubit_id, time_us))
            return 1 - true_outcome  # Flip the bit
        return true_outcome


class CompositeErrorModel:
    """
    Composite error model combining multiple noise sources.
    
    Applies depolarizing, coherence, and measurement errors.
    """
    
    def __init__(self, gate_error_rate: float, measurement_error_rate: float,
                 idle_error_rate: float, t1_us: float, t2_us: float, 
                 seed: Optional[int] = None):
        self.depolarizing = DepolarizingNoise(seed)
        self.coherence = CoherenceNoise(t1_us, t2_us, seed)
        self.measurement = MeasurementNoise(seed)
        
        self.gate_error_rate = gate_error_rate
        self.measurement_error_rate = measurement_error_rate
        self.idle_error_rate = idle_error_rate
    
    def apply_gate_errors(self, qubit_id: str, time_us: float) -> Optional[str]:
        """Apply all gate-related errors."""
        return self.depolarizing.apply_gate_noise(
            qubit_id, self.gate_error_rate, time_us
        )
    
    def apply_idle_errors(self, qubit_id: str, duration_us: float, time_us: float):
        """Apply all idle-time errors (depolarizing + coherence)."""
        # Depolarizing during idle
        self.depolarizing.apply_idle_noise(
            qubit_id, self.idle_error_rate, duration_us, time_us
        )
        
        # T1 decay
        self.coherence.apply_t1_decay(qubit_id, duration_us, time_us)
        
        # T2 dephasing
        self.coherence.apply_t2_dephasing(qubit_id, duration_us, time_us)
    
    def apply_measurement_errors(self, qubit_id: str, true_outcome: int, time_us: float) -> int:
        """Apply measurement readout errors."""
        return self.measurement.apply_measurement_error(
            qubit_id, true_outcome, self.measurement_error_rate, time_us
        )
    
    def get_total_errors(self) -> int:
        """Get total error count across all models."""
        return (self.depolarizing.get_error_count() + 
                self.coherence.get_error_count() + 
                self.measurement.get_error_count())
    
    def get_error_breakdown(self) -> dict:
        """Get breakdown of errors by type."""
        return {
            "depolarizing": self.depolarizing.get_error_count(),
            "coherence": self.coherence.get_error_count(),
            "measurement": self.measurement.get_error_count(),
            "total": self.get_total_errors()
        }
