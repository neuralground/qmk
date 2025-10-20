"""
Timing Isolation for Multi-Tenant Quantum Systems

Prevents timing side-channels that could leak information between tenants
through execution time variations.

Research:
    - Kocher, P. C. (1996). "Timing Attacks on Implementations of 
      Diffie-Hellman, RSA, DSS, and Other Systems"
    - Ge, Q., et al. (2018). "A Survey of Microarchitectural Timing 
      Attacks and Countermeasures on Contemporary Hardware"
"""

import time
import random
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class TimingMode(Enum):
    """Timing isolation mode."""
    TIME_SLOTTED = "TIME_SLOTTED"
    NOISE_INJECTION = "NOISE_INJECTION"
    DISABLED = "DISABLED"


@dataclass
class ExecutionRecord:
    """Record of an isolated execution."""
    tenant_id: str
    operation_name: Optional[str]
    actual_time: float
    padded_time: float
    noise_added: float
    timestamp: float


class TimingIsolator:
    """
    Provides timing isolation between tenants.
    
    Prevents timing side-channels by normalizing execution times.
    """
    
    def __init__(
        self,
        mode: TimingMode = TimingMode.TIME_SLOTTED,
        time_slot_ms: float = 100.0,
        noise_ms: float = 10.0
    ):
        """Initialize timing isolator."""
        self.mode = mode
        self.time_slot_ms = time_slot_ms
        self.noise_ms = noise_ms
        self.execution_history: list[ExecutionRecord] = []
        self.total_executions = 0
        self.total_overhead_ms = 0.0
    
    def execute_isolated(
        self,
        operation: Callable[[], Any],
        tenant_id: str,
        operation_name: Optional[str] = None
    ) -> Any:
        """Execute operation with timing isolation."""
        if self.mode == TimingMode.DISABLED:
            return operation()
        
        start_time = time.time()
        result = operation()
        actual_time = time.time() - start_time
        
        # Apply timing isolation
        if self.mode == TimingMode.TIME_SLOTTED:
            padded_time = self._apply_time_slotting(actual_time)
        else:
            padded_time = actual_time
        
        # Add noise
        noise = random.uniform(0, self.noise_ms / 1000.0)
        total_time = padded_time + noise
        
        # Sleep for remaining time
        elapsed = time.time() - start_time
        remaining = total_time - elapsed
        if remaining > 0:
            time.sleep(remaining)
        
        # Record execution
        self.execution_history.append(ExecutionRecord(
            tenant_id=tenant_id,
            operation_name=operation_name,
            actual_time=actual_time,
            padded_time=padded_time,
            noise_added=noise,
            timestamp=time.time()
        ))
        
        self.total_executions += 1
        self.total_overhead_ms += (padded_time - actual_time) * 1000
        
        return result
    
    def _apply_time_slotting(self, actual_time: float) -> float:
        """Round up to next time slot."""
        slot_duration = self.time_slot_ms / 1000.0
        slots_needed = int(actual_time / slot_duration) + 1
        return slots_needed * slot_duration
    
    def get_statistics(self) -> Dict:
        """Get timing isolation statistics."""
        return {
            'mode': self.mode.value,
            'time_slot_ms': self.time_slot_ms,
            'noise_ms': self.noise_ms,
            'total_executions': self.total_executions,
            'total_overhead_ms': self.total_overhead_ms,
            'avg_overhead_ms': (
                self.total_overhead_ms / self.total_executions
                if self.total_executions > 0 else 0
            )
        }
