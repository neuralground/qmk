"""
Decoder Manager

Manages multiple QEC decoders and provides unified interface.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import time

from .mwpm_decoder import MWPMDecoder, Syndrome
from .union_find_decoder import UnionFindDecoder
from .bp_decoder import BeliefPropagationDecoder, ParityCheck
from .syndrome_extractor import SyndromeExtractor


class DecoderType(Enum):
    """Available decoder types."""
    MWPM = "mwpm"
    UNION_FIND = "union_find"
    BELIEF_PROPAGATION = "bp"


class DecoderManager:
    """
    Manages QEC decoders.
    
    Provides:
    - Decoder selection
    - Performance comparison
    - Unified interface
    """
    
    def __init__(self):
        """Initialize decoder manager."""
        self.decoders: Dict[str, Any] = {}
        self.performance_stats: Dict[str, List[float]] = {}
    
    def register_decoder(
        self,
        name: str,
        decoder: Any
    ):
        """
        Register a decoder.
        
        Args:
            name: Decoder name
            decoder: Decoder instance
        """
        self.decoders[name] = decoder
        self.performance_stats[name] = []
    
    def decode(
        self,
        decoder_name: str,
        syndromes: List[Syndrome],
        **kwargs
    ) -> Any:
        """
        Decode using specified decoder.
        
        Args:
            decoder_name: Name of decoder to use
            syndromes: List of syndromes
            **kwargs: Additional decoder arguments
        
        Returns:
            Decoder output
        """
        if decoder_name not in self.decoders:
            raise KeyError(f"Decoder '{decoder_name}' not registered")
        
        decoder = self.decoders[decoder_name]
        
        # Time the decoding
        start_time = time.time()
        result = decoder.decode(syndromes, **kwargs)
        decode_time = time.time() - start_time
        
        # Record performance
        self.performance_stats[decoder_name].append(decode_time)
        
        return result
    
    def compare_decoders(
        self,
        syndromes: List[Syndrome],
        decoder_names: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Compare multiple decoders on same input.
        
        Args:
            syndromes: Syndromes to decode
            decoder_names: List of decoder names (all if None)
        
        Returns:
            Dictionary with comparison results
        """
        if decoder_names is None:
            decoder_names = list(self.decoders.keys())
        
        results = {}
        
        for name in decoder_names:
            if name not in self.decoders:
                continue
            
            start_time = time.time()
            corrections = self.decode(name, syndromes)
            decode_time = time.time() - start_time
            
            results[name] = {
                "corrections": corrections,
                "decode_time": decode_time,
                "num_corrections": len(corrections) if corrections else 0
            }
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Dict]:
        """
        Get performance statistics for all decoders.
        
        Returns:
            Dictionary with stats
        """
        stats = {}
        
        for name, times in self.performance_stats.items():
            if not times:
                stats[name] = {
                    "num_decodings": 0,
                    "avg_time": 0.0,
                    "min_time": 0.0,
                    "max_time": 0.0
                }
            else:
                stats[name] = {
                    "num_decodings": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        return stats
    
    def get_decoder_info(self, decoder_name: str) -> Dict:
        """
        Get information about a decoder.
        
        Args:
            decoder_name: Decoder name
        
        Returns:
            Decoder info dictionary
        """
        if decoder_name not in self.decoders:
            raise KeyError(f"Decoder '{decoder_name}' not registered")
        
        decoder = self.decoders[decoder_name]
        
        if hasattr(decoder, 'get_decoder_stats'):
            return decoder.get_decoder_stats()
        
        return {"name": decoder_name}
    
    def list_decoders(self) -> List[str]:
        """
        List all registered decoders.
        
        Returns:
            List of decoder names
        """
        return list(self.decoders.keys())
    
    def clear_stats(self):
        """Clear performance statistics."""
        for name in self.performance_stats:
            self.performance_stats[name] = []


def create_surface_code_decoders(distance: int) -> DecoderManager:
    """
    Create decoder manager with surface code decoders.
    
    Args:
        distance: Code distance
    
    Returns:
        DecoderManager with MWPM and Union-Find decoders
    """
    manager = DecoderManager()
    
    # MWPM decoder
    mwpm = MWPMDecoder(distance)
    manager.register_decoder("mwpm", mwpm)
    
    # Union-Find decoder
    uf = UnionFindDecoder(distance)
    manager.register_decoder("union_find", uf)
    
    return manager
