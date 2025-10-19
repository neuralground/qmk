"""
Unit tests for Advanced QEC Decoders
"""

import unittest
import numpy as np
from kernel.qec import (
    MWPMDecoder, UnionFindDecoder, BeliefPropagationDecoder,
    SyndromeExtractor, DecoderManager, Syndrome, ParityCheck,
    create_surface_code_decoders
)


class TestMWPMDecoder(unittest.TestCase):
    """Test MWPM decoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.decoder = MWPMDecoder(distance=5)
    
    def test_initialization(self):
        """Test decoder initialization."""
        self.assertEqual(self.decoder.distance, 5)
        self.assertEqual(self.decoder.lattice_size, 5)
    
    def test_decode_empty_syndromes(self):
        """Test decoding with no syndromes."""
        corrections = self.decoder.decode([])
        self.assertEqual(len(corrections), 0)
    
    def test_decode_single_pair(self):
        """Test decoding single syndrome pair."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='X'),
            Syndrome(position=(1, 1), time=0, parity='X')
        ]
        
        corrections = self.decoder.decode(syndromes)
        
        self.assertEqual(len(corrections), 1)
        self.assertIn((0, 0), corrections[0])
        self.assertIn((1, 1), corrections[0])
    
    def test_decode_odd_syndromes(self):
        """Test decoding with odd number of syndromes."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='Z'),
            Syndrome(position=(1, 1), time=0, parity='Z'),
            Syndrome(position=(2, 2), time=0, parity='Z')
        ]
        
        corrections = self.decoder.decode(syndromes)
        
        # Should handle odd parity with boundary
        self.assertGreaterEqual(len(corrections), 1)
    
    def test_estimate_logical_error(self):
        """Test logical error probability estimation."""
        # Below threshold
        p_logical = self.decoder.estimate_logical_error_probability(0.001)
        self.assertLess(p_logical, 0.01)
        
        # Above threshold
        p_logical = self.decoder.estimate_logical_error_probability(0.02)
        self.assertEqual(p_logical, 1.0)
    
    def test_get_decoder_stats(self):
        """Test getting decoder statistics."""
        stats = self.decoder.get_decoder_stats()
        
        self.assertEqual(stats["decoder_type"], "MWPM")
        self.assertEqual(stats["distance"], 5)


class TestUnionFindDecoder(unittest.TestCase):
    """Test Union-Find decoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.decoder = UnionFindDecoder(distance=5)
    
    def test_initialization(self):
        """Test decoder initialization."""
        self.assertEqual(self.decoder.distance, 5)
        self.assertEqual(self.decoder.lattice_size, 5)
    
    def test_decode_empty_syndromes(self):
        """Test decoding with no syndromes."""
        corrections = self.decoder.decode([])
        self.assertEqual(len(corrections), 0)
    
    def test_decode_syndrome_pair(self):
        """Test decoding syndrome pair."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='X'),
            Syndrome(position=(2, 2), time=0, parity='X')
        ]
        
        corrections = self.decoder.decode(syndromes)
        
        self.assertGreaterEqual(len(corrections), 1)
    
    def test_union_find_operations(self):
        """Test union-find data structure."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='Z'),
            Syndrome(position=(1, 0), time=0, parity='Z')
        ]
        
        self.decoder._initialize_union_find(syndromes)
        
        # Test find
        root = self.decoder._find(syndromes[0])
        self.assertEqual(root, syndromes[0])
        
        # Test union
        self.decoder._union(syndromes[0], syndromes[1])
        root1 = self.decoder._find(syndromes[0])
        root2 = self.decoder._find(syndromes[1])
        self.assertEqual(root1, root2)
    
    def test_get_decoder_stats(self):
        """Test getting decoder statistics."""
        stats = self.decoder.get_decoder_stats()
        
        self.assertEqual(stats["decoder_type"], "Union-Find")
        self.assertEqual(stats["threshold"], 0.009)


class TestBeliefPropagationDecoder(unittest.TestCase):
    """Test Belief Propagation decoder."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create simple parity checks
        checks = [
            ParityCheck(qubits=[0, 1, 2], parity='X'),
            ParityCheck(qubits=[1, 2, 3], parity='X'),
            ParityCheck(qubits=[2, 3, 4], parity='X')
        ]
        self.decoder = BeliefPropagationDecoder(checks, max_iterations=10)
    
    def test_initialization(self):
        """Test decoder initialization."""
        self.assertEqual(self.decoder.num_qubits, 5)
        self.assertEqual(self.decoder.num_checks, 3)
    
    def test_decode_no_errors(self):
        """Test decoding with no errors."""
        syndrome = np.array([0, 0, 0])
        error = self.decoder.decode(syndrome)
        
        self.assertEqual(len(error), 5)
    
    def test_decode_with_syndrome(self):
        """Test decoding with syndrome."""
        syndrome = np.array([1, 0, 1])
        error = self.decoder.decode(syndrome)
        
        self.assertEqual(len(error), 5)
        # Should find some error
        self.assertGreaterEqual(np.sum(error), 0)
    
    def test_get_decoder_stats(self):
        """Test getting decoder statistics."""
        stats = self.decoder.get_decoder_stats()
        
        self.assertEqual(stats["decoder_type"], "Belief Propagation")
        self.assertEqual(stats["num_qubits"], 5)
        self.assertEqual(stats["num_checks"], 3)


class TestSyndromeExtractor(unittest.TestCase):
    """Test syndrome extractor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = SyndromeExtractor(
            code_distance=5,
            measurement_error_rate=0.01
        )
    
    def test_initialization(self):
        """Test extractor initialization."""
        self.assertEqual(self.extractor.code_distance, 5)
        self.assertEqual(self.extractor.measurement_error_rate, 0.01)
    
    def test_extract_syndrome(self):
        """Test syndrome extraction."""
        errors = [(1, 1), (2, 2)]
        
        syndrome_round = self.extractor.extract_syndrome(errors, round_num=0)
        
        self.assertEqual(syndrome_round.round_num, 0)
        self.assertGreaterEqual(len(syndrome_round.syndromes), 0)
    
    def test_extract_multiple_rounds(self):
        """Test multiple extraction rounds."""
        errors = [(0, 0)]
        
        rounds = self.extractor.extract_multiple_rounds(errors, num_rounds=3)
        
        self.assertEqual(len(rounds), 3)
        for i, round in enumerate(rounds):
            self.assertEqual(round.round_num, i)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        errors = [(1, 1)]
        self.extractor.extract_multiple_rounds(errors, num_rounds=5)
        
        stats = self.extractor.get_syndrome_statistics()
        
        self.assertEqual(stats["total_rounds"], 5)
        self.assertGreaterEqual(stats["total_syndromes"], 0)
    
    def test_clear_history(self):
        """Test clearing history."""
        errors = [(1, 1)]
        self.extractor.extract_syndrome(errors)
        
        self.extractor.clear_history()
        
        stats = self.extractor.get_syndrome_statistics()
        self.assertEqual(stats["total_rounds"], 0)


class TestDecoderManager(unittest.TestCase):
    """Test decoder manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = create_surface_code_decoders(distance=5)
    
    def test_initialization(self):
        """Test manager initialization."""
        decoders = self.manager.list_decoders()
        
        self.assertIn("mwpm", decoders)
        self.assertIn("union_find", decoders)
    
    def test_decode_with_decoder(self):
        """Test decoding with specific decoder."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='X'),
            Syndrome(position=(1, 1), time=0, parity='X')
        ]
        
        corrections = self.manager.decode("mwpm", syndromes)
        
        self.assertIsNotNone(corrections)
    
    def test_compare_decoders(self):
        """Test comparing multiple decoders."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='Z'),
            Syndrome(position=(2, 2), time=0, parity='Z')
        ]
        
        results = self.manager.compare_decoders(syndromes)
        
        self.assertIn("mwpm", results)
        self.assertIn("union_find", results)
        self.assertIn("decode_time", results["mwpm"])
    
    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        syndromes = [
            Syndrome(position=(0, 0), time=0, parity='X'),
            Syndrome(position=(1, 1), time=0, parity='X')
        ]
        
        # Decode a few times
        for _ in range(3):
            self.manager.decode("mwpm", syndromes)
        
        stats = self.manager.get_performance_stats()
        
        self.assertEqual(stats["mwpm"]["num_decodings"], 3)
        self.assertGreater(stats["mwpm"]["avg_time"], 0)
    
    def test_get_decoder_info(self):
        """Test getting decoder info."""
        info = self.manager.get_decoder_info("mwpm")
        
        self.assertEqual(info["decoder_type"], "MWPM")
        self.assertEqual(info["distance"], 5)


if __name__ == "__main__":
    unittest.main()
