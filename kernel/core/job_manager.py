"""
Job Manager for QMK Kernel

Manages asynchronous job submission, execution, and tracking.
"""

import secrets
import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class JobState(Enum):
    """Job execution states."""
    QUEUED = "QUEUED"              # Waiting for resources
    VALIDATING = "VALIDATING"      # Graph validation in progress
    RUNNING = "RUNNING"            # Executing on quantum hardware
    COMPLETED = "COMPLETED"        # Successfully completed
    FAILED = "FAILED"              # Execution failed
    CANCELLED = "CANCELLED"        # Cancelled by user


@dataclass
class JobPolicy:
    """Job execution policy."""
    priority: int = 10              # Priority (higher = more urgent)
    deadline_epochs: Optional[int] = None  # Deadline in epochs
    seed: Optional[int] = None      # Random seed for deterministic execution
    debug: bool = False             # Enable debug logging
    timeout_ms: Optional[int] = None  # Execution timeout


@dataclass
class JobProgress:
    """Job execution progress."""
    current_epoch: int = 0
    total_epochs: int = 0
    nodes_executed: int = 0
    nodes_total: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "nodes_executed": self.nodes_executed,
            "nodes_total": self.nodes_total,
        }


@dataclass
class Job:
    """
    Represents a submitted quantum job.
    
    Tracks:
    - Job ID and session ID
    - QVM graph and execution policy
    - Current state and progress
    - Measurement events and telemetry
    - Error information (if failed)
    """
    job_id: str
    session_id: str
    graph: Dict
    policy: JobPolicy
    state: JobState = JobState.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # Execution results
    progress: JobProgress = field(default_factory=JobProgress)
    events: Dict[str, Any] = field(default_factory=dict)
    telemetry: Dict[str, Any] = field(default_factory=dict)
    peak_resources: Dict[str, Any] = field(default_factory=dict)
    
    # Error information
    error: Optional[Dict] = None
    
    # Cancellation tracking
    cancelled_at_epoch: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary representation."""
        result = {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "progress": self.progress.to_dict(),
        }
        
        if self.started_at:
            result["started_at"] = self.started_at
        
        if self.completed_at:
            result["completed_at"] = self.completed_at
        
        if self.events:
            result["events"] = self.events
        
        if self.telemetry:
            result["telemetry"] = self.telemetry
        
        if self.peak_resources:
            result["peak_resources"] = self.peak_resources
        
        if self.error:
            result["error"] = self.error
        
        if self.cancelled_at_epoch is not None:
            result["cancelled_at_epoch"] = self.cancelled_at_epoch
        
        return result


class JobManager:
    """
    Manages job lifecycle and execution.
    
    Responsibilities:
    - Job submission and validation
    - Asynchronous execution
    - State tracking and progress updates
    - Job cancellation
    - Result collection
    """
    
    def __init__(self, executor=None):
        """
        Initialize job manager.
        
        Args:
            executor: Optional executor instance for running jobs
        """
        self.executor = executor
        
        # Job tracking
        self.jobs: Dict[str, Job] = {}
        
        # Session -> jobs mapping
        self.session_jobs: Dict[str, Set[str]] = {}
        
        # Lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Condition variable for waiting on job completion
        self._job_conditions: Dict[str, threading.Condition] = {}
    
    def submit_job(
        self,
        session_id: str,
        graph: Dict,
        policy: Optional[Dict] = None
    ) -> Dict:
        """
        Submit a job for execution.
        
        Args:
            session_id: Session identifier
            graph: QVM graph to execute
            policy: Optional execution policy
        
        Returns:
            Dictionary with:
            - job_id: New job identifier
            - state: Initial job state
            - estimated_epochs: Estimated execution time
        """
        with self._lock:
            # Generate job ID
            job_id = self._generate_job_id()
            
            # Parse policy
            job_policy = JobPolicy()
            if policy:
                if "priority" in policy:
                    job_policy.priority = policy["priority"]
                if "deadline_epochs" in policy:
                    job_policy.deadline_epochs = policy["deadline_epochs"]
                if "seed" in policy:
                    job_policy.seed = policy["seed"]
                if "debug" in policy:
                    job_policy.debug = policy["debug"]
                if "timeout_ms" in policy:
                    job_policy.timeout_ms = policy["timeout_ms"]
            
            # Create job
            job = Job(
                job_id=job_id,
                session_id=session_id,
                graph=graph,
                policy=job_policy,
                state=JobState.QUEUED
            )
            
            # Register job
            self.jobs[job_id] = job
            
            if session_id not in self.session_jobs:
                self.session_jobs[session_id] = set()
            self.session_jobs[session_id].add(job_id)
            
            # Create condition variable for waiting
            self._job_conditions[job_id] = threading.Condition(self._lock)
            
            # Estimate epochs (simple heuristic: count nodes)
            estimated_epochs = len(graph.get("nodes", []))
            
            # Start execution asynchronously
            if self.executor:
                threading.Thread(
                    target=self._execute_job,
                    args=(job_id,),
                    daemon=True
                ).start()
            
            return {
                "job_id": job_id,
                "state": job.state.value,
                "estimated_epochs": estimated_epochs
            }
    
    def get_job_status(self, job_id: str, session_id: str) -> Dict:
        """
        Get job status.
        
        Args:
            job_id: Job identifier
            session_id: Session identifier (for access control)
        
        Returns:
            Dictionary with job status
        
        Raises:
            KeyError: If job not found
            PermissionError: If job belongs to different session
        """
        with self._lock:
            if job_id not in self.jobs:
                raise KeyError(f"Job '{job_id}' not found")
            
            job = self.jobs[job_id]
            
            # Check session access
            if job.session_id != session_id:
                raise PermissionError(
                    f"Job '{job_id}' belongs to different session"
                )
            
            return job.to_dict()
    
    def wait_for_job(
        self,
        job_id: str,
        session_id: str,
        timeout_ms: Optional[int] = None
    ) -> Dict:
        """
        Wait for job completion.
        
        Args:
            job_id: Job identifier
            session_id: Session identifier
            timeout_ms: Optional timeout in milliseconds
        
        Returns:
            Dictionary with final job status
        
        Raises:
            KeyError: If job not found
            PermissionError: If job belongs to different session
            TimeoutError: If timeout exceeded
        """
        # First check job exists and session has access
        with self._lock:
            if job_id not in self.jobs:
                raise KeyError(f"Job '{job_id}' not found")
            
            job = self.jobs[job_id]
            
            if job.session_id != session_id:
                raise PermissionError(
                    f"Job '{job_id}' belongs to different session"
                )
            
            # If already in terminal state, return immediately
            if job.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
                return job.to_dict()
            
            # Wait for completion
            condition = self._job_conditions[job_id]
            timeout_sec = timeout_ms / 1000.0 if timeout_ms else None
            
            if not condition.wait(timeout=timeout_sec):
                raise TimeoutError(f"Job '{job_id}' did not complete within timeout")
            
            return job.to_dict()
    
    def cancel_job(self, job_id: str, session_id: str) -> Dict:
        """
        Cancel a job.
        
        Args:
            job_id: Job identifier
            session_id: Session identifier
        
        Returns:
            Dictionary with cancellation result
        
        Raises:
            KeyError: If job not found
            PermissionError: If job belongs to different session
            RuntimeError: If job already completed
        """
        with self._lock:
            if job_id not in self.jobs:
                raise KeyError(f"Job '{job_id}' not found")
            
            job = self.jobs[job_id]
            
            if job.session_id != session_id:
                raise PermissionError(
                    f"Job '{job_id}' belongs to different session"
                )
            
            if job.state in [JobState.COMPLETED, JobState.FAILED]:
                raise RuntimeError(f"Job '{job_id}' already completed")
            
            if job.state == JobState.CANCELLED:
                # Already cancelled
                return job.to_dict()
            
            # Mark as cancelled
            job.state = JobState.CANCELLED
            job.completed_at = time.time()
            job.cancelled_at_epoch = job.progress.current_epoch
            
            # Notify waiters
            if job_id in self._job_conditions:
                self._job_conditions[job_id].notify_all()
            
            return job.to_dict()
    
    def get_session_jobs(self, session_id: str) -> List[str]:
        """
        Get all jobs for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of job IDs
        """
        with self._lock:
            return list(self.session_jobs.get(session_id, set()))
    
    def cleanup_session_jobs(self, session_id: str):
        """
        Clean up jobs for a closed session.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id not in self.session_jobs:
                return
            
            job_ids = list(self.session_jobs[session_id])
            
            for job_id in job_ids:
                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    
                    # Cancel running jobs
                    if job.state in [JobState.QUEUED, JobState.VALIDATING, JobState.RUNNING]:
                        job.state = JobState.CANCELLED
                        job.completed_at = time.time()
                    
                    # Clean up condition variable
                    if job_id in self._job_conditions:
                        del self._job_conditions[job_id]
                    
                    del self.jobs[job_id]
            
            del self.session_jobs[session_id]
    
    def _execute_job(self, job_id: str):
        """
        Execute a job asynchronously.
        
        Args:
            job_id: Job identifier
        """
        try:
            with self._lock:
                if job_id not in self.jobs:
                    return
                
                job = self.jobs[job_id]
                
                # Check if already cancelled
                if job.state == JobState.CANCELLED:
                    return
                
                # Move to validating state
                job.state = JobState.VALIDATING
            
            # Validate graph (outside lock)
            # In production, this would call the validator
            
            with self._lock:
                if job.state == JobState.CANCELLED:
                    return
                
                # Move to running state
                job.state = JobState.RUNNING
                job.started_at = time.time()
            
            # Execute graph
            if self.executor:
                result = self.executor.execute(job.graph)
                
                with self._lock:
                    if job.state == JobState.CANCELLED:
                        return
                    
                    # Update job with results
                    job.state = JobState.COMPLETED
                    job.completed_at = time.time()
                    job.events = result.get("events", {})
                    job.telemetry = result.get("telemetry", {})
                    job.peak_resources = result.get("peak_resources", {})
                    job.progress.nodes_executed = len(job.graph.get("nodes", []))
                    job.progress.nodes_total = len(job.graph.get("nodes", []))
            else:
                # No executor - just mark as completed
                with self._lock:
                    job.state = JobState.COMPLETED
                    job.completed_at = time.time()
        
        except Exception as e:
            # Handle execution errors
            with self._lock:
                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    job.state = JobState.FAILED
                    job.completed_at = time.time()
                    job.error = {
                        "message": str(e),
                        "type": type(e).__name__
                    }
        
        finally:
            # Notify waiters
            with self._lock:
                if job_id in self._job_conditions:
                    self._job_conditions[job_id].notify_all()
    
    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        return f"job_{secrets.token_hex(8)}"
