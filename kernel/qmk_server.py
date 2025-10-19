"""
QMK Server - Main entry point for the Quantum Microkernel

Integrates all components and starts the RPC server.
"""

from kernel.session_manager import SessionManager
from kernel.job_manager import JobManager
from kernel.rpc_server import RPCServer
from kernel.simulator.enhanced_resource_manager import EnhancedResourceManager
from kernel.simulator.enhanced_executor import EnhancedExecutor
from kernel.syscalls import (
    handle_negotiate_caps,
    handle_submit,
    handle_status,
    handle_wait,
    handle_cancel,
    handle_open_chan,
    handle_get_telemetry,
)


class QMKServer:
    """
    Main QMK server that integrates all components.
    """
    
    def __init__(self, socket_path: str = "/tmp/qmk.sock"):
        """
        Initialize QMK server.
        
        Args:
            socket_path: Path to Unix domain socket
        """
        # Initialize core components
        self.session_manager = SessionManager()
        self.resource_manager = EnhancedResourceManager()
        self.executor = EnhancedExecutor(self.resource_manager)
        self.job_manager = JobManager(executor=self.executor)
        
        # Initialize RPC server
        self.rpc_server = RPCServer(socket_path)
        
        # Register syscall handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all syscall handlers with the RPC server."""
        
        # q_negotiate_caps
        self.rpc_server.register_handler(
            "q_negotiate_caps",
            lambda params: handle_negotiate_caps(params, self.session_manager)
        )
        
        # q_submit
        self.rpc_server.register_handler(
            "q_submit",
            lambda params: handle_submit(
                params, self.session_manager, self.job_manager
            )
        )
        
        # q_status
        self.rpc_server.register_handler(
            "q_status",
            lambda params: handle_status(
                params, self.session_manager, self.job_manager
            )
        )
        
        # q_wait
        self.rpc_server.register_handler(
            "q_wait",
            lambda params: handle_wait(
                params, self.session_manager, self.job_manager
            )
        )
        
        # q_cancel
        self.rpc_server.register_handler(
            "q_cancel",
            lambda params: handle_cancel(
                params, self.session_manager, self.job_manager
            )
        )
        
        # q_open_chan
        self.rpc_server.register_handler(
            "q_open_chan",
            lambda params: handle_open_chan(
                params, self.session_manager, self.resource_manager
            )
        )
        
        # q_get_telemetry
        self.rpc_server.register_handler(
            "q_get_telemetry",
            lambda params: handle_get_telemetry(
                params, self.session_manager, self.resource_manager
            )
        )
    
    def start(self):
        """Start the QMK server."""
        print(f"Starting QMK server on {self.rpc_server.socket_path}")
        self.rpc_server.start()
        print("QMK server started")
    
    def stop(self):
        """Stop the QMK server."""
        print("Stopping QMK server")
        self.rpc_server.stop()
        print("QMK server stopped")
    
    def run(self):
        """Run the server (blocking)."""
        self.start()
        
        try:
            # Keep server running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="QMK Server")
    parser.add_argument(
        "--socket",
        default="/tmp/qmk.sock",
        help="Unix domain socket path"
    )
    
    args = parser.parse_args()
    
    server = QMKServer(socket_path=args.socket)
    server.run()


if __name__ == "__main__":
    main()
