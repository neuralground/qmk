#!/usr/bin/env python3
"""
Comprehensive tests for capability mediation system.

Tests cover:
- Capability checking for all operations
- Missing capability detection
- Token verification integration
- Audit logging
- Statistics tracking
- Security properties
"""

import unittest
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kernel.security.capability_mediator import (
    CapabilityMediator,
    SecurityError,
    get_required_capabilities,
    operation_requires_capability,
    CAPABILITY_REQUIREMENTS
)


class TestCapabilityMediator(unittest.TestCase):
    """Test capability mediator basic functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_create_mediator(self):
        """Test creating capability mediator."""
        self.assertIsNotNone(self.mediator)
        self.assertTrue(self.mediator.audit_enabled)
        self.assertTrue(self.mediator.strict_mode)
    
    def test_create_token_via_mediator(self):
        """Test creating token via mediator."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        self.assertIsNotNone(token)
        self.assertEqual(token.capabilities, {'CAP_ALLOC'})


class TestCapabilityChecking(unittest.TestCase):
    """Test capability checking for operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_check_capability_allowed(self):
        """Test capability check that should be allowed."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        result = self.mediator.check_capability(token, 'ALLOC_LQ')
        
        self.assertTrue(result.allowed)
        self.assertEqual(result.operation, 'ALLOC_LQ')
        self.assertEqual(result.required_caps, {'CAP_ALLOC'})
        self.assertEqual(result.missing_caps, set())
    
    def test_check_capability_denied_missing_capability(self):
        """Test capability check denied due to missing capability."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        # Try to measure without CAP_MEASURE
        result = self.mediator.check_capability(token, 'MEASURE_Z')
        
        self.assertFalse(result.allowed)
        self.assertEqual(result.operation, 'MEASURE_Z')
        self.assertEqual(result.required_caps, {'CAP_MEASURE'})
        self.assertEqual(result.missing_caps, {'CAP_MEASURE'})
        self.assertIn('Missing capabilities', result.reason)
    
    def test_check_capability_denied_expired_token(self):
        """Test capability check denied due to expired token."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1',
            ttl=0  # Expires immediately
        )
        
        time.sleep(0.1)
        
        result = self.mediator.check_capability(token, 'ALLOC_LQ')
        
        self.assertFalse(result.allowed)
        self.assertIn('verification failed', result.reason.lower())
    
    def test_check_capability_denied_revoked_token(self):
        """Test capability check denied due to revoked token."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        self.mediator.revoke_token(token.token_id)
        
        result = self.mediator.check_capability(token, 'ALLOC_LQ')
        
        self.assertFalse(result.allowed)
    
    def test_require_capability_success(self):
        """Test require_capability with valid token."""
        token = self.mediator.create_token(
            capabilities={'CAP_COMPUTE'},
            tenant_id='tenant1'
        )
        
        # Should not raise exception
        self.mediator.require_capability(token, 'APPLY_H')
    
    def test_require_capability_raises_on_failure(self):
        """Test require_capability raises exception on failure."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        # Should raise SecurityError
        with self.assertRaises(SecurityError):
            self.mediator.require_capability(token, 'MEASURE_Z')


class TestMeasurementProtection(unittest.TestCase):
    """Test that measurements are protected by CAP_MEASURE (CRITICAL!)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_measure_z_requires_cap_measure(self):
        """Test that MEASURE_Z requires CAP_MEASURE."""
        token = self.mediator.create_token(
            capabilities={'CAP_COMPUTE'},  # No CAP_MEASURE!
            tenant_id='tenant1'
        )
        
        result = self.mediator.check_capability(token, 'MEASURE_Z')
        
        self.assertFalse(result.allowed)
        self.assertIn('CAP_MEASURE', result.missing_caps)
    
    def test_measure_x_requires_cap_measure(self):
        """Test that MEASURE_X requires CAP_MEASURE."""
        token = self.mediator.create_token(
            capabilities={'CAP_COMPUTE'},
            tenant_id='tenant1'
        )
        
        result = self.mediator.check_capability(token, 'MEASURE_X')
        
        self.assertFalse(result.allowed)
        self.assertIn('CAP_MEASURE', result.missing_caps)
    
    def test_measure_y_requires_cap_measure(self):
        """Test that MEASURE_Y requires CAP_MEASURE."""
        token = self.mediator.create_token(
            capabilities={'CAP_COMPUTE'},
            tenant_id='tenant1'
        )
        
        result = self.mediator.check_capability(token, 'MEASURE_Y')
        
        self.assertFalse(result.allowed)
        self.assertIn('CAP_MEASURE', result.missing_caps)
    
    def test_measure_bell_requires_cap_measure(self):
        """Test that MEASURE_BELL requires CAP_MEASURE."""
        token = self.mediator.create_token(
            capabilities={'CAP_COMPUTE'},
            tenant_id='tenant1'
        )
        
        result = self.mediator.check_capability(token, 'MEASURE_BELL')
        
        self.assertFalse(result.allowed)
        self.assertIn('CAP_MEASURE', result.missing_caps)
    
    def test_measurements_allowed_with_cap_measure(self):
        """Test that measurements are allowed with CAP_MEASURE."""
        token = self.mediator.create_token(
            capabilities={'CAP_MEASURE'},
            tenant_id='tenant1'
        )
        
        # All measurements should be allowed
        self.assertTrue(self.mediator.check_capability(token, 'MEASURE_Z').allowed)
        self.assertTrue(self.mediator.check_capability(token, 'MEASURE_X').allowed)
        self.assertTrue(self.mediator.check_capability(token, 'MEASURE_Y').allowed)
        self.assertTrue(self.mediator.check_capability(token, 'MEASURE_BELL').allowed)


class TestAllOperationsCovered(unittest.TestCase):
    """Test that all operations have capability requirements."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_all_qubit_operations_covered(self):
        """Test that all qubit operations have requirements."""
        operations = ['ALLOC_LQ', 'FREE_LQ', 'RESET_LQ']
        
        for op in operations:
            self.assertIn(op, CAPABILITY_REQUIREMENTS)
            self.assertGreater(len(CAPABILITY_REQUIREMENTS[op]), 0)
    
    def test_all_measurements_covered(self):
        """Test that all measurements have requirements."""
        operations = ['MEASURE_Z', 'MEASURE_X', 'MEASURE_Y', 'MEASURE_BELL']
        
        for op in operations:
            self.assertIn(op, CAPABILITY_REQUIREMENTS)
            self.assertEqual(CAPABILITY_REQUIREMENTS[op], {'CAP_MEASURE'})
    
    def test_all_single_qubit_gates_covered(self):
        """Test that all single-qubit gates have requirements."""
        operations = [
            'APPLY_H', 'APPLY_X', 'APPLY_Y', 'APPLY_Z',
            'APPLY_S', 'APPLY_T', 'APPLY_RZ', 'APPLY_RY'
        ]
        
        for op in operations:
            self.assertIn(op, CAPABILITY_REQUIREMENTS)
            self.assertEqual(CAPABILITY_REQUIREMENTS[op], {'CAP_COMPUTE'})
    
    def test_all_two_qubit_gates_covered(self):
        """Test that all two-qubit gates have requirements."""
        operations = ['APPLY_CNOT', 'APPLY_CZ', 'APPLY_SWAP']
        
        for op in operations:
            self.assertIn(op, CAPABILITY_REQUIREMENTS)
            self.assertEqual(CAPABILITY_REQUIREMENTS[op], {'CAP_COMPUTE'})
    
    def test_all_channel_operations_covered(self):
        """Test that all channel operations have requirements."""
        operations = ['OPEN_CHAN', 'CLOSE_CHAN', 'SEND_QUBIT', 'RECV_QUBIT']
        
        for op in operations:
            self.assertIn(op, CAPABILITY_REQUIREMENTS)
            self.assertGreater(len(CAPABILITY_REQUIREMENTS[op]), 0)
    
    def test_all_advanced_operations_covered(self):
        """Test that all advanced operations have requirements."""
        operations = ['TELEPORT_CNOT', 'INJECT_T_STATE']
        
        for op in operations:
            self.assertIn(op, CAPABILITY_REQUIREMENTS)
            self.assertGreater(len(CAPABILITY_REQUIREMENTS[op]), 0)


class TestAuditLogging(unittest.TestCase):
    """Test audit logging of capability checks."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_audit_log_records_checks(self):
        """Test that audit log records capability checks."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        self.mediator.check_capability(token, 'ALLOC_LQ')
        
        log = self.mediator.get_audit_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0].operation, 'ALLOC_LQ')
    
    def test_audit_log_records_allowed_and_denied(self):
        """Test that audit log records both allowed and denied checks."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        # Allowed check
        self.mediator.check_capability(token, 'ALLOC_LQ')
        
        # Denied check
        self.mediator.check_capability(token, 'MEASURE_Z')
        
        log = self.mediator.get_audit_log()
        self.assertEqual(len(log), 2)
        self.assertTrue(log[0].allowed)
        self.assertFalse(log[1].allowed)
    
    def test_audit_log_filtering(self):
        """Test audit log filtering."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        # Multiple checks
        self.mediator.check_capability(token, 'ALLOC_LQ')  # Allowed
        self.mediator.check_capability(token, 'MEASURE_Z')  # Denied
        self.mediator.check_capability(token, 'FREE_LQ')  # Allowed
        
        allowed_log = self.mediator.get_audit_log(allowed_only=True)
        self.assertEqual(len(allowed_log), 2)
        
        denied_log = self.mediator.get_audit_log(denied_only=True)
        self.assertEqual(len(denied_log), 1)


class TestStatistics(unittest.TestCase):
    """Test capability check statistics."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC'},
            tenant_id='tenant1'
        )
        
        # Perform checks
        self.mediator.check_capability(token, 'ALLOC_LQ')  # Allowed
        self.mediator.check_capability(token, 'MEASURE_Z')  # Denied
        self.mediator.check_capability(token, 'FREE_LQ')  # Allowed
        
        stats = self.mediator.get_statistics()
        
        self.assertEqual(stats['checks_performed'], 3)
        self.assertEqual(stats['checks_allowed'], 2)
        self.assertEqual(stats['checks_denied'], 1)
        self.assertAlmostEqual(stats['allow_rate'], 2/3)
        self.assertAlmostEqual(stats['deny_rate'], 1/3)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""
    
    def test_get_required_capabilities(self):
        """Test get_required_capabilities function."""
        caps = get_required_capabilities('MEASURE_Z')
        self.assertEqual(caps, {'CAP_MEASURE'})
        
        caps = get_required_capabilities('APPLY_H')
        self.assertEqual(caps, {'CAP_COMPUTE'})
    
    def test_operation_requires_capability(self):
        """Test operation_requires_capability function."""
        self.assertTrue(operation_requires_capability('MEASURE_Z', 'CAP_MEASURE'))
        self.assertFalse(operation_requires_capability('MEASURE_Z', 'CAP_COMPUTE'))
        
        self.assertTrue(operation_requires_capability('APPLY_H', 'CAP_COMPUTE'))
        self.assertFalse(operation_requires_capability('APPLY_H', 'CAP_MEASURE'))


class TestSecurityProperties(unittest.TestCase):
    """Test security properties of capability mediation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secret_key = b'test_secret_key_12345'
        self.mediator = CapabilityMediator(self.secret_key)
    
    def test_complete_mediation_all_operations_checked(self):
        """Test that all operations require capability checks."""
        # Every operation should have requirements
        self.assertGreater(len(CAPABILITY_REQUIREMENTS), 20)
        
        # All operations should require at least one capability
        for op, caps in CAPABILITY_REQUIREMENTS.items():
            self.assertGreater(len(caps), 0, f"Operation {op} has no requirements")
    
    def test_fail_safe_defaults(self):
        """Test that unknown operations are denied in strict mode."""
        token = self.mediator.create_token(
            capabilities={'CAP_ALLOC', 'CAP_COMPUTE', 'CAP_MEASURE'},
            tenant_id='tenant1'
        )
        
        # Unknown operation should be denied
        result = self.mediator.check_capability(token, 'UNKNOWN_OPERATION')
        
        self.assertFalse(result.allowed)
    
    def test_least_privilege_enforcement(self):
        """Test that operations require minimum necessary capabilities."""
        # Measurements should only require CAP_MEASURE, not CAP_ADMIN
        self.assertEqual(
            get_required_capabilities('MEASURE_Z'),
            {'CAP_MEASURE'}
        )
        
        # Gates should only require CAP_COMPUTE
        self.assertEqual(
            get_required_capabilities('APPLY_H'),
            {'CAP_COMPUTE'}
        )
    
    def test_defense_in_depth_multiple_checks(self):
        """Test that multiple validation layers exist."""
        token = self.mediator.create_token(
            capabilities={'CAP_MEASURE'},
            tenant_id='tenant1',
            ttl=0  # Expired
        )
        
        time.sleep(0.1)
        
        # Should fail on token verification, not just capability check
        result = self.mediator.check_capability(token, 'MEASURE_Z')
        
        self.assertFalse(result.allowed)
        self.assertIn('verification', result.reason.lower())


if __name__ == '__main__':
    unittest.main()
