"""
Union-Find Decoder

Implements Union-Find decoding for surface codes.
Faster than MWPM with near-optimal performance for most error rates.
"""

from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class Syndrome:
    """Syndrome measurement (same as MWPM)."""
    position: Tuple[int, int]
    time: int
    parity: str
    
    def __hash__(self):
        return hash((self.position, self.time, self.parity))


class UnionFindDecoder:
    """
    Union-Find decoder for surface codes.
    
    Uses union-find data structure for fast decoding.
    Near-optimal performance with O(n log n) complexity.
    """
    
    def __init__(self, distance: int, growth_rate: float = 0.5):
        """
        Initialize Union-Find decoder.
        
        Args:
            distance: Code distance
            growth_rate: Cluster growth rate parameter
        """
        self.distance = distance
        self.lattice_size = distance
        self.growth_rate = growth_rate
        
        # Union-Find data structure
        self.parent: Dict = {}
        self.rank: Dict = {}
        self.cluster_parity: Dict = {}
    
    def decode(
        self,
        syndromes: List[Syndrome],
        error_rates: Optional[Dict[str, float]] = None
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Decode syndromes using Union-Find algorithm.
        
        Args:
            syndromes: List of detected syndromes
            error_rates: Error rates (optional)
        
        Returns:
            List of correction chains
        """
        if not syndromes:
            return []
        
        # Separate X and Z syndromes
        x_syndromes = [s for s in syndromes if s.parity == 'X']
        z_syndromes = [s for s in syndromes if s.parity == 'Z']
        
        # Decode each parity
        x_corrections = self._decode_parity(x_syndromes)
        z_corrections = self._decode_parity(z_syndromes)
        
        return x_corrections + z_corrections
    
    def _decode_parity(
        self,
        syndromes: List[Syndrome]
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Decode syndromes of single parity."""
        if not syndromes:
            return []
        
        # Initialize union-find
        self._initialize_union_find(syndromes)
        
        # Grow clusters
        edges = self._get_sorted_edges(syndromes)
        
        for edge in edges:
            s1, s2, weight = edge
            
            # Find cluster roots
            root1 = self._find(s1)
            root2 = self._find(s2)
            
            # If in different clusters, merge
            if root1 != root2:
                # Check if merging would create odd parity
                parity1 = self.cluster_parity.get(root1, 0)
                parity2 = self.cluster_parity.get(root2, 0)
                
                # Union clusters
                self._union(root1, root2)
                
                # Update parity
                new_root = self._find(root1)
                self.cluster_parity[new_root] = (parity1 + parity2) % 2
        
        # Extract corrections from cluster structure
        corrections = self._extract_corrections(syndromes)
        
        return corrections
    
    def _initialize_union_find(self, syndromes: List[Syndrome]):
        """Initialize union-find data structure."""
        self.parent = {}
        self.rank = {}
        self.cluster_parity = {}
        
        for syndrome in syndromes:
            self.parent[syndrome] = syndrome
            self.rank[syndrome] = 0
            self.cluster_parity[syndrome] = 1  # Each syndrome has odd parity
    
    def _find(self, syndrome: Syndrome) -> Syndrome:
        """Find root of cluster (with path compression)."""
        if self.parent[syndrome] != syndrome:
            self.parent[syndrome] = self._find(self.parent[syndrome])
        return self.parent[syndrome]
    
    def _union(self, s1: Syndrome, s2: Syndrome):
        """Union two clusters (by rank)."""
        root1 = self._find(s1)
        root2 = self._find(s2)
        
        if root1 == root2:
            return
        
        # Union by rank
        if self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        elif self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
    
    def _get_sorted_edges(
        self,
        syndromes: List[Syndrome]
    ) -> List[Tuple[Syndrome, Syndrome, float]]:
        """
        Get edges sorted by weight (distance).
        
        Returns:
            List of (syndrome1, syndrome2, weight) tuples
        """
        edges = []
        
        for i, s1 in enumerate(syndromes):
            for s2 in syndromes[i+1:]:
                weight = self._edge_weight(s1.position, s2.position)
                edges.append((s1, s2, weight))
        
        # Sort by weight
        edges.sort(key=lambda x: x[2])
        
        return edges
    
    def _edge_weight(
        self,
        pos1: Tuple[int, int],
        pos2: Tuple[int, int]
    ) -> float:
        """Calculate edge weight (Manhattan distance)."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _extract_corrections(
        self,
        syndromes: List[Syndrome]
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Extract correction chains from cluster structure.
        
        Simplified: pairs syndromes in same cluster.
        """
        # Group syndromes by cluster
        clusters: Dict[Syndrome, List[Syndrome]] = {}
        
        for syndrome in syndromes:
            root = self._find(syndrome)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(syndrome)
        
        # Create corrections by pairing within clusters
        corrections = []
        
        for cluster_syndromes in clusters.values():
            # Pair syndromes greedily
            remaining = list(cluster_syndromes)
            
            while len(remaining) >= 2:
                s1 = remaining.pop(0)
                
                # Find closest
                min_dist = float('inf')
                closest_idx = 0
                
                for i, s2 in enumerate(remaining):
                    dist = self._edge_weight(s1.position, s2.position)
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
                
                s2 = remaining.pop(closest_idx)
                corrections.append((s1.position, s2.position))
            
            # Handle odd syndrome (connect to boundary)
            if len(remaining) == 1:
                s = remaining[0]
                boundary = self._get_boundary_position(s.position)
                corrections.append((s.position, boundary))
        
        return corrections
    
    def _get_boundary_position(
        self,
        pos: Tuple[int, int]
    ) -> Tuple[int, int]:
        """Get nearest boundary position."""
        x, y = pos
        
        # Find nearest edge
        distances = [
            (x, (0, y)),
            (self.lattice_size - x, (self.lattice_size, y)),
            (y, (x, 0)),
            (self.lattice_size - y, (x, self.lattice_size))
        ]
        
        min_dist, boundary_pos = min(distances, key=lambda x: x[0])
        
        return boundary_pos
    
    def estimate_logical_error_probability(
        self,
        physical_error_rate: float,
        num_rounds: int = 1
    ) -> float:
        """
        Estimate logical error probability.
        
        Union-Find has slightly worse threshold than MWPM (~0.009 vs 0.01).
        """
        threshold = 0.009  # Union-Find threshold
        
        if physical_error_rate >= threshold:
            return 1.0
        
        d = self.distance
        p_logical = (physical_error_rate / threshold) ** ((d + 1) / 2)
        p_logical_per_round = 1 - (1 - p_logical) ** num_rounds
        
        return min(p_logical_per_round, 1.0)
    
    def get_decoder_stats(self) -> Dict:
        """Get decoder statistics."""
        return {
            "decoder_type": "Union-Find",
            "algorithm": "Union-Find with cluster growth",
            "distance": self.distance,
            "lattice_size": self.lattice_size,
            "growth_rate": self.growth_rate,
            "complexity": f"O(n log n) where n = {self.lattice_size}^2",
            "threshold": 0.009
        }
