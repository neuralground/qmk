"""
Unit tests for Audit Logger
"""

import unittest
import time
from kernel.security.audit_logger import AuditLogger, AuditEventType, AuditSeverity


class TestAuditLogger(unittest.TestCase):
    """Test audit logging."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = AuditLogger()
    
    def test_log_event(self):
        """Test logging an event."""
        event = self.logger.log_event(
            event_type=AuditEventType.SESSION_CREATED,
            tenant_id="tenant_1",
            session_id="sess_1",
            severity=AuditSeverity.INFO
        )
        
        self.assertIsNotNone(event.event_id)
        self.assertEqual(event.event_type, AuditEventType.SESSION_CREATED)
        self.assertEqual(event.tenant_id, "tenant_1")
        self.assertEqual(event.session_id, "sess_1")
    
    def test_query_events_by_tenant(self):
        """Test querying events by tenant."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1")
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_2")
        self.logger.log_event(AuditEventType.JOB_SUBMITTED, "tenant_1")
        
        events = self.logger.query_events(tenant_id="tenant_1")
        
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.tenant_id == "tenant_1" for e in events))
    
    def test_query_events_by_type(self):
        """Test querying events by type."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1")
        self.logger.log_event(AuditEventType.JOB_SUBMITTED, "tenant_1")
        self.logger.log_event(AuditEventType.JOB_SUBMITTED, "tenant_2")
        
        events = self.logger.query_events(event_type=AuditEventType.JOB_SUBMITTED)
        
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.event_type == AuditEventType.JOB_SUBMITTED for e in events))
    
    def test_query_events_by_severity(self):
        """Test querying events by severity."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1", 
                            severity=AuditSeverity.INFO)
        self.logger.log_event(AuditEventType.QUOTA_EXCEEDED, "tenant_1",
                            severity=AuditSeverity.WARNING)
        self.logger.log_event(AuditEventType.UNAUTHORIZED_ACCESS, "tenant_1",
                            severity=AuditSeverity.ERROR)
        
        warnings = self.logger.query_events(severity=AuditSeverity.WARNING)
        
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].severity, AuditSeverity.WARNING)
    
    def test_query_events_with_time_range(self):
        """Test querying events with time range."""
        start_time = time.time()
        
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1")
        time.sleep(0.1)
        mid_time = time.time()
        time.sleep(0.1)
        self.logger.log_event(AuditEventType.JOB_SUBMITTED, "tenant_1")
        
        # Query events after mid_time
        events = self.logger.query_events(start_time=mid_time)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, AuditEventType.JOB_SUBMITTED)
    
    def test_query_events_limit(self):
        """Test query limit."""
        for i in range(10):
            self.logger.log_event(AuditEventType.JOB_SUBMITTED, "tenant_1")
        
        events = self.logger.query_events(limit=5)
        
        self.assertEqual(len(events), 5)
    
    def test_get_event_stats(self):
        """Test getting event statistics."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1",
                            severity=AuditSeverity.INFO)
        self.logger.log_event(AuditEventType.JOB_SUBMITTED, "tenant_1",
                            severity=AuditSeverity.INFO)
        self.logger.log_event(AuditEventType.QUOTA_EXCEEDED, "tenant_2",
                            severity=AuditSeverity.WARNING)
        
        stats = self.logger.get_event_stats()
        
        self.assertEqual(stats["total_events"], 3)
        self.assertEqual(stats["by_severity"]["info"], 2)
        self.assertEqual(stats["by_severity"]["warning"], 1)
        self.assertEqual(stats["by_tenant"]["tenant_1"], 2)
    
    def test_export_events_json(self):
        """Test exporting events as JSON."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1")
        
        json_export = self.logger.export_events(format="json", tenant_id="tenant_1")
        
        self.assertIn("session_created", json_export)
        self.assertIn("tenant_1", json_export)
    
    def test_export_events_csv(self):
        """Test exporting events as CSV."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1")
        
        csv_export = self.logger.export_events(format="csv", tenant_id="tenant_1")
        
        self.assertIn("event_id", csv_export)
        self.assertIn("session_created", csv_export)
    
    def test_clear_events(self):
        """Test clearing events."""
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_1")
        self.logger.log_event(AuditEventType.SESSION_CREATED, "tenant_2")
        
        self.logger.clear_events(tenant_id="tenant_1")
        
        events = self.logger.query_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].tenant_id, "tenant_2")


if __name__ == "__main__":
    unittest.main()
