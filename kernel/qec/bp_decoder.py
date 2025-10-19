"""
Belief Propagation (BP) Decoder

Implements BP decoding for QLDPC codes.
Iterative message-passing algorithm for sparse parity-check codes.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class ParityCheck:
    """
    Parity check constraint.
    
    Attributes:
        qubits: List of qubit indices in check
        parity: X or Z parity
    """
    qubits: List[int]
    parity: str


class BeliefPropagationDecoder:
    """
    Belief Propagation decoder for QLDPC codes.
    
    Uses sum-product algorithm for iterative decoding.
    """
    
    def __init__(
        self,
        parity_checks: List[ParityCheck],
        max_iterations: int = 100,
        convergence_threshold: float = 1e-6
    ):
        """
        Initialize BP decoder.
        
        Args:
            parity_checks: List of parity check constraints
            max_iterations: Maximum BP iterations
            convergence_threshold: Convergence threshold
        """
        self.parity_checks = parity_checks
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        
        # Build factor graph
        self._build_factor_graph()
    
    def _build_factor_graph(self):
        """Build bipartite factor graph for BP."""
        # Variable nodes (qubits)
        self.num_qubits = max(
            max(check.qubits) for check in self.parity_checks
        ) + 1
        
        # Check nodes
        self.num_checks = len(self.parity_checks)
        
        # Adjacency lists
        self.qubit_to_checks: Dict[int, List[int]] = {
            i: [] for i in range(self.num_qubits)
        }
        self.check_to_qubits: Dict[int, List[int]] = {
            i: [] for i in range(self.num_checks)
        }
        
        for check_idx, check in enumerate(self.parity_checks):
            self.check_to_qubits[check_idx] = check.qubits
            for qubit in check.qubits:
                self.qubit_to_checks[qubit].append(check_idx)
    
    def decode(
        self,
        syndrome: np.ndarray,
        channel_probs: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Decode syndrome using BP algorithm.
        
        Args:
            syndrome: Binary syndrome vector (1 = violated check)
            channel_probs: Prior error probabilities for each qubit
        
        Returns:
            Decoded error vector
        """
        if channel_probs is None:
            # Uniform prior
            channel_probs = np.ones(self.num_qubits) * 0.1
        
        # Initialize messages
        # qubit_to_check_msgs[qubit][check_idx] = log-likelihood ratio
        qubit_to_check_msgs = {
            qubit: {check: 0.0 for check in self.qubit_to_checks[qubit]}
            for qubit in range(self.num_qubits)
        }
        
        check_to_qubit_msgs = {
            check: {qubit: 0.0 for qubit in self.check_to_qubits[check]}
            for check in range(self.num_checks)
        }
        
        # Convert channel probs to log-likelihood ratios
        channel_llrs = self._prob_to_llr(channel_probs)
        
        # BP iterations
        for iteration in range(self.max_iterations):
            # Check to qubit messages
            new_check_to_qubit = self._update_check_to_qubit_messages(
                qubit_to_check_msgs,
                syndrome
            )
            
            # Qubit to check messages
            new_qubit_to_check = self._update_qubit_to_check_messages(
                check_to_qubit_msgs,
                channel_llrs
            )
            
            # Check convergence
            if self._has_converged(
                check_to_qubit_msgs,
                new_check_to_qubit
            ):
                break
            
            check_to_qubit_msgs = new_check_to_qubit
            qubit_to_check_msgs = new_qubit_to_check
        
        # Compute final beliefs
        beliefs = self._compute_beliefs(
            check_to_qubit_msgs,
            channel_llrs
        )
        
        # Hard decision
        error = (beliefs < 0).astype(int)
        
        return error
    
    def _update_check_to_qubit_messages(
        self,
        qubit_to_check_msgs: Dict,
        syndrome: np.ndarray
    ) -> Dict:
        """Update messages from checks to qubits."""
        new_msgs = {
            check: {} for check in range(self.num_checks)
        }
        
        for check_idx in range(self.num_checks):
            qubits = self.check_to_qubits[check_idx]
            syndrome_bit = syndrome[check_idx]
            
            for target_qubit in qubits:
                # Product of tanh(msg/2) from other qubits
                product = 1.0
                
                for qubit in qubits:
                    if qubit != target_qubit:
                        msg = qubit_to_check_msgs[qubit].get(check_idx, 0.0)
                        product *= np.tanh(msg / 2.0)
                
                # Incorporate syndrome
                if syndrome_bit == 1:
                    product *= -1
                
                # Convert back to LLR
                product = np.clip(product, -0.9999, 0.9999)
                new_msg = 2.0 * np.arctanh(product)
                
                new_msgs[check_idx][target_qubit] = new_msg
        
        return new_msgs
    
    def _update_qubit_to_check_messages(
        self,
        check_to_qubit_msgs: Dict,
        channel_llrs: np.ndarray
    ) -> Dict:
        """Update messages from qubits to checks."""
        new_msgs = {
            qubit: {} for qubit in range(self.num_qubits)
        }
        
        for qubit in range(self.num_qubits):
            checks = self.qubit_to_checks[qubit]
            
            for target_check in checks:
                # Sum of messages from other checks + channel
                msg_sum = channel_llrs[qubit]
                
                for check in checks:
                    if check != target_check:
                        msg_sum += check_to_qubit_msgs[check].get(qubit, 0.0)
                
                new_msgs[qubit][target_check] = msg_sum
        
        return new_msgs
    
    def _compute_beliefs(
        self,
        check_to_qubit_msgs: Dict,
        channel_llrs: np.ndarray
    ) -> np.ndarray:
        """Compute final beliefs (posterior LLRs)."""
        beliefs = np.copy(channel_llrs)
        
        for qubit in range(self.num_qubits):
            for check in self.qubit_to_checks[qubit]:
                beliefs[qubit] += check_to_qubit_msgs[check].get(qubit, 0.0)
        
        return beliefs
    
    def _has_converged(
        self,
        old_msgs: Dict,
        new_msgs: Dict
    ) -> bool:
        """Check if messages have converged."""
        max_diff = 0.0
        
        for check in old_msgs:
            for qubit in old_msgs[check]:
                old_val = old_msgs[check][qubit]
                new_val = new_msgs[check].get(qubit, 0.0)
                diff = abs(new_val - old_val)
                max_diff = max(max_diff, diff)
        
        return max_diff < self.convergence_threshold
    
    def _prob_to_llr(self, probs: np.ndarray) -> np.ndarray:
        """Convert probabilities to log-likelihood ratios."""
        # LLR = log(P(0) / P(1)) = log((1-p) / p)
        probs = np.clip(probs, 1e-10, 1 - 1e-10)
        return np.log((1 - probs) / probs)
    
    def estimate_logical_error_probability(
        self,
        physical_error_rate: float,
        code_rate: float = 0.1
    ) -> float:
        """
        Estimate logical error probability for QLDPC code.
        
        Args:
            physical_error_rate: Physical error rate
            code_rate: Code rate (k/n)
        
        Returns:
            Estimated logical error probability
        """
        # QLDPC codes have higher thresholds than surface codes
        # Typical threshold ~0.02-0.05 depending on code
        threshold = 0.03
        
        if physical_error_rate >= threshold:
            return 1.0
        
        # Simplified scaling (actual depends on code structure)
        # Better codes have better scaling
        exponent = 1.0 / code_rate  # Higher rate = better scaling
        p_logical = (physical_error_rate / threshold) ** exponent
        
        return min(p_logical, 1.0)
    
    def get_decoder_stats(self) -> Dict:
        """Get decoder statistics."""
        return {
            "decoder_type": "Belief Propagation",
            "algorithm": "Sum-product message passing",
            "num_qubits": self.num_qubits,
            "num_checks": self.num_checks,
            "max_iterations": self.max_iterations,
            "convergence_threshold": self.convergence_threshold,
            "complexity": f"O(iterations * edges) ≈ O({self.max_iterations} * {self.num_checks * 10})"
        }
