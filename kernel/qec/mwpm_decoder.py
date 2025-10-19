"""
Minimum Weight Perfect Matching (MWPM) Decoder

Implements MWPM decoding for surface codes using a simplified matching algorithm.
This is the gold-standard decoder for surface codes with near-optimal performance.
"""

import numpy as np
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass
import heapq


@dataclass
class Syndrome:
    """
    Represents a syndrome measurement.
    
    Attributes:
        position: (x, y) position of syndrome
        time: Time step of measurement
        parity: X or Z parity
    """
    position: Tuple[int, int]
    time: int
    parity: str  # 'X' or 'Z'
    
    def __hash__(self):
        return hash((self.position, self.time, self.parity))
    
    def __eq__(self, other):
        return (self.position == other.position and 
                self.time == other.time and 
                self.parity == other.parity)


class MWPMDecoder:
    """
    Minimum Weight Perfect Matching decoder for surface codes.
    
    Uses a greedy matching algorithm for demonstration.
    Production implementation would use Blossom algorithm.
    """
    
    def __init__(self, distance: int):
        """
        Initialize MWPM decoder.
        
        Args:
            distance: Code distance
        """
        self.distance = distance
        self.lattice_size = distance
    
    def decode(
        self,
        syndromes: List[Syndrome],
        error_rates: Optional[Dict[str, float]] = None
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Decode syndromes to find correction operations.
        
        Args:
            syndromes: List of detected syndromes
            error_rates: Error rates for weighting (optional)
        
        Returns:
            List of correction chains (pairs of positions)
        """
        if not syndromes:
            return []
        
        # Separate X and Z syndromes
        x_syndromes = [s for s in syndromes if s.parity == 'X']
        z_syndromes = [s for s in syndromes if s.parity == 'Z']
        
        # Match each parity separately
        x_corrections = self._match_syndromes(x_syndromes, error_rates)
        z_corrections = self._match_syndromes(z_syndromes, error_rates)
        
        return x_corrections + z_corrections
    
    def _match_syndromes(
        self,
        syndromes: List[Syndrome],
        error_rates: Optional[Dict[str, float]]
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Match syndromes using greedy algorithm.
        
        Production implementation would use Blossom algorithm for
        true minimum weight perfect matching.
        """
        if len(syndromes) == 0:
            return []
        
        # If odd number of syndromes, add virtual boundary syndrome
        if len(syndromes) % 2 == 1:
            # Add boundary syndrome at nearest edge
            boundary = self._get_boundary_syndrome(syndromes[0])
            syndromes = syndromes + [boundary]
        
        corrections = []
        remaining = set(syndromes)
        
        # Greedy matching: repeatedly match closest pairs
        while len(remaining) > 0:
            # Pick arbitrary syndrome
            s1 = next(iter(remaining))
            remaining.remove(s1)
            
            if len(remaining) == 0:
                break
            
            # Find closest remaining syndrome
            min_dist = float('inf')
            closest = None
            
            for s2 in remaining:
                dist = self._manhattan_distance(s1.position, s2.position)
                if dist < min_dist:
                    min_dist = dist
                    closest = s2
            
            if closest:
                remaining.remove(closest)
                corrections.append((s1.position, closest.position))
        
        return corrections
    
    def _manhattan_distance(
        self,
        pos1: Tuple[int, int],
        pos2: Tuple[int, int]
    ) -> int:
        """Calculate Manhattan distance between positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _get_boundary_syndrome(self, syndrome: Syndrome) -> Syndrome:
        """Get nearest boundary syndrome for odd parity."""
        x, y = syndrome.position
        
        # Find nearest boundary
        distances = [
            (x, 'left'),
            (self.lattice_size - x, 'right'),
            (y, 'top'),
            (self.lattice_size - y, 'bottom')
        ]
        
        min_dist, direction = min(distances)
        
        # Create boundary syndrome
        if direction == 'left':
            boundary_pos = (0, y)
        elif direction == 'right':
            boundary_pos = (self.lattice_size, y)
        elif direction == 'top':
            boundary_pos = (x, 0)
        else:  # bottom
            boundary_pos = (x, self.lattice_size)
        
        return Syndrome(
            position=boundary_pos,
            time=syndrome.time,
            parity=syndrome.parity
        )
    
    def estimate_logical_error_probability(
        self,
        physical_error_rate: float,
        num_rounds: int = 1
    ) -> float:
        """
        Estimate logical error probability using threshold formula.
        
        Args:
            physical_error_rate: Physical error rate
            num_rounds: Number of QEC rounds
        
        Returns:
            Estimated logical error probability
        """
        # Surface code threshold ~0.01
        threshold = 0.01
        
        if physical_error_rate >= threshold:
            return 1.0  # Above threshold
        
        # Below threshold: exponential suppression
        # P_L ≈ (p/p_th)^((d+1)/2)
        d = self.distance
        p_logical = (physical_error_rate / threshold) ** ((d + 1) / 2)
        
        # Account for multiple rounds
        p_logical_per_round = 1 - (1 - p_logical) ** num_rounds
        
        return min(p_logical_per_round, 1.0)
    
    def get_decoder_stats(self) -> Dict:
        """
        Get decoder statistics.
        
        Returns:
            Dictionary with decoder info
        """
        return {
            "decoder_type": "MWPM",
            "algorithm": "Greedy (simplified)",
            "distance": self.distance,
            "lattice_size": self.lattice_size,
            "optimal": False,  # Greedy is not optimal
            "complexity": f"O(n^3) where n = {self.lattice_size}^2"
        }
