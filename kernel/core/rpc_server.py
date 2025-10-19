"""
JSON-RPC 2.0 Server for qSyscall ABI

Implements the RPC server over Unix domain sockets.
"""

import json
import socket
import threading
import os
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class JSONRPCError:
    """JSON-RPC 2.0 error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom error codes (qSyscall-specific)
    AUTH_FAILED = -32100
    TENANT_SUSPENDED = -32101
    INSUFFICIENT_CAPS = -32001
    INVALID_GRAPH = -32200
    QUOTA_EXCEEDED = -32201
    RESOURCE_EXHAUSTED = -32202
    JOB_NOT_FOUND = -32300
    ACCESS_DENIED = -32301
    TIMEOUT = -32302
    ALREADY_COMPLETED = -32303


class RPCServer:
    """
    JSON-RPC 2.0 server over Unix domain sockets.
    
    Handles:
    - Request parsing and validation
    - Method routing
    - Error response formatting
    - Connection management
    """
    
    def __init__(self, socket_path: str = "/tmp/qmk.sock"):
        """
        Initialize RPC server.
        
        Args:
            socket_path: Path to Unix domain socket
        """
        self.socket_path = socket_path
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.server_thread: Optional[threading.Thread] = None
    
    def register_handler(self, method: str, handler: Callable):
        """
        Register a handler for a specific method.
        
        Args:
            method: Method name (e.g., "q_submit")
            handler: Handler function that takes params dict and returns result dict
        """
        self.handlers[method] = handler
    
    def start(self):
        """Start the RPC server."""
        if self.running:
            return
        
        # Remove existing socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        # Create Unix domain socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        
        self.running = True
        
        # Start server thread
        self.server_thread = threading.Thread(target=self._serve, daemon=True)
        self.server_thread.start()
    
    def stop(self):
        """Stop the RPC server."""
        if not self.running:
            return
        
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
    
    def _serve(self):
        """Main server loop."""
        while self.running:
            try:
                client_socket, _ = self.server_socket.accept()
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
            
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket):
        """
        Handle a client connection.
        
        Args:
            client_socket: Client socket
        """
        try:
            # Read request
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete JSON message
                try:
                    json.loads(data.decode('utf-8'))
                    break
                except json.JSONDecodeError:
                    continue
            
            if not data:
                return
            
            # Process request
            response = self._process_request(data.decode('utf-8'))
            
            # Send response
            client_socket.sendall(response.encode('utf-8'))
        
        except Exception as e:
            error_response = self._format_error(
                None,
                JSONRPCError.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )
            client_socket.sendall(error_response.encode('utf-8'))
        
        finally:
            client_socket.close()
    
    def _process_request(self, request_data: str) -> str:
        """
        Process a JSON-RPC request.
        
        Args:
            request_data: JSON-RPC request string
        
        Returns:
            JSON-RPC response string
        """
        try:
            request = json.loads(request_data)
        except json.JSONDecodeError:
            return self._format_error(None, JSONRPCError.PARSE_ERROR, "Parse error")
        
        # Validate request
        if not isinstance(request, dict):
            return self._format_error(None, JSONRPCError.INVALID_REQUEST, "Invalid request")
        
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            return self._format_error(
                request.get("id"),
                JSONRPCError.INVALID_REQUEST,
                "Invalid JSON-RPC version"
            )
        
        if "method" not in request:
            return self._format_error(
                request.get("id"),
                JSONRPCError.INVALID_REQUEST,
                "Missing method"
            )
        
        method = request["method"]
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Check if method exists
        if method not in self.handlers:
            return self._format_error(
                request_id,
                JSONRPCError.METHOD_NOT_FOUND,
                f"Method '{method}' not found"
            )
        
        # Call handler
        try:
            handler = self.handlers[method]
            result = handler(params)
            
            return self._format_success(request_id, result)
        
        except ValueError as e:
            return self._format_error(
                request_id,
                JSONRPCError.INVALID_PARAMS,
                str(e)
            )
        
        except KeyError as e:
            return self._format_error(
                request_id,
                JSONRPCError.JOB_NOT_FOUND,
                str(e)
            )
        
        except PermissionError as e:
            return self._format_error(
                request_id,
                JSONRPCError.ACCESS_DENIED,
                str(e)
            )
        
        except RuntimeError as e:
            error_msg = str(e).lower()
            
            if "quota" in error_msg:
                code = JSONRPCError.QUOTA_EXCEEDED
            elif "insufficient" in error_msg:
                code = JSONRPCError.RESOURCE_EXHAUSTED
            elif "capability" in error_msg or "capabilities" in error_msg:
                code = JSONRPCError.INSUFFICIENT_CAPS
            else:
                code = JSONRPCError.INTERNAL_ERROR
            
            return self._format_error(request_id, code, str(e))
        
        except TimeoutError as e:
            return self._format_error(
                request_id,
                JSONRPCError.TIMEOUT,
                str(e)
            )
        
        except Exception as e:
            return self._format_error(
                request_id,
                JSONRPCError.INTERNAL_ERROR,
                f"Internal error: {str(e)}"
            )
    
    def _format_success(self, request_id: Any, result: Dict) -> str:
        """
        Format a successful JSON-RPC response.
        
        Args:
            request_id: Request ID
            result: Result dictionary
        
        Returns:
            JSON-RPC response string
        """
        response = {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
        
        return json.dumps(response)
    
    def _format_error(
        self,
        request_id: Any,
        code: int,
        message: str,
        data: Optional[Dict] = None
    ) -> str:
        """
        Format a JSON-RPC error response.
        
        Args:
            request_id: Request ID
            code: Error code
            message: Error message
            data: Optional additional error data
        
        Returns:
            JSON-RPC error response string
        """
        error = {
            "code": code,
            "message": message
        }
        
        if data:
            error["data"] = data
        
        response = {
            "jsonrpc": "2.0",
            "error": error,
            "id": request_id
        }
        
        return json.dumps(response)
    
    def call_local(self, method: str, params: Dict) -> Dict:
        """
        Call a method locally (for testing).
        
        Args:
            method: Method name
            params: Parameters
        
        Returns:
            Result dictionary
        
        Raises:
            ValueError: If method not found
        """
        if method not in self.handlers:
            raise ValueError(f"Method '{method}' not found")
        
        return self.handlers[method](params)
