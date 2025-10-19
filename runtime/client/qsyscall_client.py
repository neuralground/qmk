"""
QSyscall Client Library

Python client for the qSyscall ABI over Unix domain sockets.
"""

import json
import socket
from typing import Dict, List, Optional, Any


class QSyscallError(Exception):
    """Exception raised for qSyscall errors."""
    
    def __init__(self, code: int, message: str, data: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"[{code}] {message}")


class QSyscallClient:
    """
    Client for qSyscall ABI.
    
    Provides high-level interface to QMK kernel operations.
    """
    
    def __init__(self, socket_path: str = "/tmp/qmk.sock"):
        """
        Initialize client.
        
        Args:
            socket_path: Path to Unix domain socket
        """
        self.socket_path = socket_path
        self.request_id = 0
        self.session_id: Optional[str] = None
    
    def negotiate_capabilities(self, requested: List[str]) -> Dict:
        """
        Negotiate capabilities with the kernel.
        
        Args:
            requested: List of requested capabilities
        
        Returns:
            Dictionary with negotiation results
        """
        result = self._call("q_negotiate_caps", {"requested": requested})
        
        # Store session ID
        self.session_id = result["session_id"]
        
        return result
    
    def submit_job(
        self,
        graph: Dict,
        priority: int = 10,
        seed: Optional[int] = None,
        debug: bool = False
    ) -> str:
        """
        Submit a QVM graph for execution.
        
        Args:
            graph: QVM graph to execute
            priority: Job priority (higher = more urgent)
            seed: Optional random seed for deterministic execution
            debug: Enable debug logging
        
        Returns:
            Job ID
        
        Raises:
            QSyscallError: If submission fails
        """
        if not self.session_id:
            raise RuntimeError("Must negotiate capabilities first")
        
        policy = {
            "priority": priority,
            "debug": debug
        }
        
        if seed is not None:
            policy["seed"] = seed
        
        result = self._call("q_submit", {
            "graph": graph,
            "policy": policy,
            "session_id": self.session_id
        })
        
        return result["job_id"]
    
    def get_job_status(self, job_id: str) -> Dict:
        """
        Get job status.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job status dictionary
        """
        if not self.session_id:
            raise RuntimeError("Must negotiate capabilities first")
        
        return self._call("q_status", {
            "job_id": job_id,
            "session_id": self.session_id
        })
    
    def wait_for_job(self, job_id: str, timeout_ms: Optional[int] = None) -> Dict:
        """
        Wait for job completion.
        
        Args:
            job_id: Job identifier
            timeout_ms: Optional timeout in milliseconds
        
        Returns:
            Final job status
        """
        if not self.session_id:
            raise RuntimeError("Must negotiate capabilities first")
        
        params = {
            "job_id": job_id,
            "session_id": self.session_id
        }
        
        if timeout_ms is not None:
            params["timeout_ms"] = timeout_ms
        
        return self._call("q_wait", params)
    
    def cancel_job(self, job_id: str) -> Dict:
        """
        Cancel a job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Cancellation result
        """
        if not self.session_id:
            raise RuntimeError("Must negotiate capabilities first")
        
        return self._call("q_cancel", {
            "job_id": job_id,
            "session_id": self.session_id
        })
    
    def open_channel(
        self,
        vq_a: str,
        vq_b: str,
        fidelity: float = 0.99
    ) -> Dict:
        """
        Open an entanglement channel.
        
        Args:
            vq_a: First qubit ID
            vq_b: Second qubit ID
            fidelity: Target fidelity
        
        Returns:
            Channel information
        """
        if not self.session_id:
            raise RuntimeError("Must negotiate capabilities first")
        
        return self._call("q_open_chan", {
            "vq_a": vq_a,
            "vq_b": vq_b,
            "options": {"fidelity": fidelity},
            "session_id": self.session_id
        })
    
    def get_telemetry(self) -> Dict:
        """
        Get system telemetry.
        
        Returns:
            Telemetry data
        """
        if not self.session_id:
            raise RuntimeError("Must negotiate capabilities first")
        
        return self._call("q_get_telemetry", {
            "session_id": self.session_id
        })
    
    def submit_and_wait(
        self,
        graph: Dict,
        timeout_ms: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Submit a job and wait for completion.
        
        Args:
            graph: QVM graph to execute
            timeout_ms: Optional timeout in milliseconds
            **kwargs: Additional arguments for submit_job
        
        Returns:
            Final job status with results
        """
        job_id = self.submit_job(graph, **kwargs)
        return self.wait_for_job(job_id, timeout_ms)
    
    def _call(self, method: str, params: Dict) -> Any:
        """
        Make a JSON-RPC call.
        
        Args:
            method: Method name
            params: Parameters
        
        Returns:
            Result from the call
        
        Raises:
            QSyscallError: If the call fails
        """
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        # Connect to server
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            sock.connect(self.socket_path)
            
            # Send request
            request_data = json.dumps(request).encode('utf-8')
            sock.sendall(request_data)
            
            # Receive response
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                # Check if we have a complete JSON message
                try:
                    json.loads(response_data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue
            
            response = json.loads(response_data.decode('utf-8'))
            
            # Check for errors
            if "error" in response:
                error = response["error"]
                raise QSyscallError(
                    error["code"],
                    error["message"],
                    error.get("data")
                )
            
            return response["result"]
        
        finally:
            sock.close()
