"""
Hardware Topology Representation

Represents the connectivity constraints of quantum hardware.
"""

from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class HardwareTopology:
    """
    Represents the connectivity graph of quantum hardware.
    
    Attributes:
        num_qubits: Number of physical qubits
        edges: Set of (qubit1, qubit2) tuples representing connectivity
        name: Name of the topology
    """
    num_qubits: int
    edges: Set[Tuple[int, int]]
    name: str = "custom"
    
    def __post_init__(self):
        """Ensure edges are bidirectional."""
        # Add reverse edges
        all_edges = set()
        for q1, q2 in self.edges:
            all_edges.add((q1, q2))
            all_edges.add((q2, q1))
        self.edges = all_edges
    
    def are_connected(self, q1: int, q2: int) -> bool:
        """Check if two qubits are directly connected."""
        return (q1, q2) in self.edges
    
    def get_neighbors(self, qubit: int) -> Set[int]:
        """Get all qubits connected to the given qubit."""
        return {q2 for q1, q2 in self.edges if q1 == qubit}
    
    def get_distance(self, q1: int, q2: int) -> int:
        """
        Get the shortest path distance between two qubits.
        
        Returns:
            Number of SWAPs needed to bring qubits adjacent
        """
        if q1 == q2:
            return 0
        if self.are_connected(q1, q2):
            return 0  # Already adjacent
        
        # BFS to find shortest path
        visited = {q1}
        queue = [(q1, 0)]
        
        while queue:
            current, dist = queue.pop(0)
            
            for neighbor in self.get_neighbors(current):
                if neighbor == q2:
                    return dist
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        
        return float('inf')  # Not connected
    
    def find_path(self, q1: int, q2: int) -> Optional[List[int]]:
        """
        Find shortest path between two qubits.
        
        Returns:
            List of qubits in path from q1 to q2, or None if no path
        """
        if q1 == q2:
            return [q1]
        
        # BFS with path tracking
        visited = {q1}
        queue = [(q1, [q1])]
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in self.get_neighbors(current):
                if neighbor == q2:
                    return path + [q2]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    @staticmethod
    def linear(num_qubits: int) -> 'HardwareTopology':
        """
        Create a linear topology (chain).
        
        Connectivity: 0-1-2-3-...-n
        """
        edges = {(i, i+1) for i in range(num_qubits - 1)}
        return HardwareTopology(num_qubits, edges, "linear")
    
    @staticmethod
    def grid(rows: int, cols: int) -> 'HardwareTopology':
        """
        Create a 2D grid topology.
        
        Connectivity: rectangular grid with nearest-neighbor connections
        """
        num_qubits = rows * cols
        edges = set()
        
        for r in range(rows):
            for c in range(cols):
                qubit = r * cols + c
                
                # Connect to right neighbor
                if c < cols - 1:
                    edges.add((qubit, qubit + 1))
                
                # Connect to bottom neighbor
                if r < rows - 1:
                    edges.add((qubit, qubit + cols))
        
        return HardwareTopology(num_qubits, edges, f"grid_{rows}x{cols}")
    
    @staticmethod
    def all_to_all(num_qubits: int) -> 'HardwareTopology':
        """
        Create an all-to-all topology (fully connected).
        
        Every qubit can interact with every other qubit.
        """
        edges = {(i, j) for i in range(num_qubits) for j in range(num_qubits) if i != j}
        return HardwareTopology(num_qubits, edges, "all_to_all")
    
    @staticmethod
    def ibm_falcon() -> 'HardwareTopology':
        """
        Create IBM Falcon r5.11 topology (27 qubits).
        
        Heavy-hex lattice structure.
        """
        # Simplified version - actual IBM topology is more complex
        # This is a representative heavy-hex pattern
        edges = {
            # Row 0
            (0, 1), (1, 2), (2, 3), (3, 4),
            # Row 1
            (5, 6), (6, 7), (7, 8), (8, 9),
            # Row 2
            (10, 11), (11, 12), (12, 13), (13, 14),
            # Row 3
            (15, 16), (16, 17), (17, 18), (18, 19),
            # Row 4
            (20, 21), (21, 22), (22, 23), (23, 24),
            # Vertical connections
            (1, 6), (3, 8),
            (6, 11), (8, 13),
            (11, 16), (13, 18),
            (16, 21), (18, 23),
        }
        return HardwareTopology(27, edges, "ibm_falcon")
    
    def __repr__(self):
        return f"HardwareTopology({self.name}, {self.num_qubits} qubits, {len(self.edges)//2} edges)"
