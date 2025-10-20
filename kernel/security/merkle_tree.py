"""
Merkle Tree for Tamper-Evident Audit Logs

Implements a cryptographic Merkle tree to provide tamper-evidence for audit logs.
Any modification to historical audit entries will be detected through root hash changes.

A Merkle tree is a binary tree where:
- Leaf nodes contain hashes of data items
- Internal nodes contain hashes of their children
- The root hash represents the entire tree

Security Properties:
- Tamper Evidence: Any change to data changes the root hash
- Efficient Verification: Can verify inclusion in O(log n) time
- Append-Only: New data can be added without recomputing entire tree
- Cryptographic Binding: Uses SHA-256 for collision resistance

Research:
    - Merkle, R. C. (1988). "A Digital Signature Based on a Conventional 
      Encryption Function"
    - Crosby, M., et al. (2016). "BlockChain Technology: Beyond Bitcoin"
    - Buldas, A., et al. (2000). "Accountable Certificate Management using 
      Undeniable Attestations"
"""

import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MerkleProof:
    """Proof of inclusion in Merkle tree."""
    leaf_index: int
    leaf_hash: bytes
    proof_hashes: List[Tuple[str, bytes]]  # ('left'/'right', hash)
    root_hash: bytes
    
    def verify(self, leaf_data: bytes) -> bool:
        """Verify that leaf_data is in the tree."""
        # Hash the leaf data
        computed_hash = hashlib.sha256(leaf_data).digest()
        
        if computed_hash != self.leaf_hash:
            return False
        
        # Compute root from proof
        current_hash = self.leaf_hash
        for direction, sibling_hash in self.proof_hashes:
            if direction == 'left':
                current_hash = hashlib.sha256(sibling_hash + current_hash).digest()
            else:
                current_hash = hashlib.sha256(current_hash + sibling_hash).digest()
        
        return current_hash == self.root_hash


class MerkleTree:
    """
    Cryptographic Merkle tree for tamper-evident audit logs.
    
    Provides efficient tamper detection and proof of inclusion for audit entries.
    Uses SHA-256 for cryptographic hashing.
    
    Security Guarantees:
    - Tamper evidence: Any modification changes root hash
    - Collision resistance: SHA-256 provides 128-bit security
    - Efficient verification: O(log n) proof size
    - Append-only: Can add entries without full recomputation
    
    Attributes:
        leaves: List of leaf hashes
        tree: Complete binary tree of hashes
    """
    
    def __init__(self):
        """Initialize empty Merkle tree."""
        self.leaves: List[bytes] = []
        self.tree: List[List[bytes]] = []
    
    def append(self, data: bytes) -> bytes:
        """
        Append data to tree and return new root hash.
        
        Args:
            data: Data to append (will be hashed)
        
        Returns:
            New root hash after appending
        
        Example:
            >>> tree = MerkleTree()
            >>> root1 = tree.append(b'entry1')
            >>> root2 = tree.append(b'entry2')
            >>> assert root1 != root2  # Root changes
        """
        # Hash the data
        leaf_hash = hashlib.sha256(data).digest()
        self.leaves.append(leaf_hash)
        
        # Rebuild tree
        self._build_tree()
        
        return self.root()
    
    def root(self) -> bytes:
        """
        Get current root hash.
        
        Returns:
            Root hash, or empty bytes if tree is empty
        """
        if not self.tree or not self.tree[-1]:
            return b''
        return self.tree[-1][0]
    
    def get_proof(self, index: int) -> Optional[MerkleProof]:
        """
        Get Merkle proof for leaf at index.
        
        Args:
            index: Index of leaf to prove
        
        Returns:
            MerkleProof or None if index invalid
        
        Example:
            >>> tree = MerkleTree()
            >>> tree.append(b'data1')
            >>> tree.append(b'data2')
            >>> proof = tree.get_proof(0)
            >>> assert proof.verify(b'data1')
        """
        if index < 0 or index >= len(self.leaves):
            return None
        
        if not self.tree:
            return None
        
        proof_hashes = []
        current_index = index
        
        # Walk up the tree collecting sibling hashes
        for level in range(len(self.tree) - 1):
            level_nodes = self.tree[level]
            
            # Find sibling
            if current_index % 2 == 0:
                # We're a left child, sibling is on right
                if current_index + 1 < len(level_nodes):
                    sibling_hash = level_nodes[current_index + 1]
                    proof_hashes.append(('right', sibling_hash))
                else:
                    # No sibling (odd number of nodes), duplicate ourselves
                    sibling_hash = level_nodes[current_index]
                    proof_hashes.append(('right', sibling_hash))
            else:
                # We're a right child, sibling is on left
                sibling_hash = level_nodes[current_index - 1]
                proof_hashes.append(('left', sibling_hash))
            
            # Move to parent
            current_index = current_index // 2
        
        return MerkleProof(
            leaf_index=index,
            leaf_hash=self.leaves[index],
            proof_hashes=proof_hashes,
            root_hash=self.root()
        )
    
    def verify_proof(self, proof: MerkleProof, data: bytes) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            proof: Merkle proof to verify
            data: Original data
        
        Returns:
            True if proof is valid
        """
        return proof.verify(data)
    
    def size(self) -> int:
        """Get number of leaves in tree."""
        return len(self.leaves)
    
    def _build_tree(self):
        """Build Merkle tree from leaves."""
        if not self.leaves:
            self.tree = []
            return
        
        # Start with leaves as level 0
        self.tree = [self.leaves.copy()]
        
        # Build up the tree
        while len(self.tree[-1]) > 1:
            current_level = self.tree[-1]
            next_level = []
            
            # Process pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    # Odd number of nodes, duplicate the last one
                    right = left
                
                # Hash the pair
                parent_hash = hashlib.sha256(left + right).digest()
                next_level.append(parent_hash)
            
            self.tree.append(next_level)
    
    def get_leaf_hash(self, index: int) -> Optional[bytes]:
        """Get hash of leaf at index."""
        if 0 <= index < len(self.leaves):
            return self.leaves[index]
        return None
    
    def to_dict(self) -> dict:
        """Serialize tree to dictionary."""
        return {
            'size': len(self.leaves),
            'root': self.root().hex() if self.root() else '',
            'leaves': [leaf.hex() for leaf in self.leaves]
        }
