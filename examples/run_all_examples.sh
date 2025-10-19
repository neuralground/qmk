#!/bin/bash
#
# Run All QMK Examples
#
# This script starts the QMK server and runs all example programs.
#

set -e

echo "=========================================="
echo "QMK Examples Runner"
echo "=========================================="
echo ""

# Check if server is already running
if [ -e /tmp/qmk.sock ]; then
    echo "⚠️  QMK server socket already exists at /tmp/qmk.sock"
    echo "   Attempting to connect..."
    echo ""
else
    echo "Starting QMK server..."
    python -m kernel.qmk_server &
    SERVER_PID=$!
    echo "Server PID: $SERVER_PID"
    
    # Wait for server to start
    echo "Waiting for server to initialize..."
    sleep 2
    
    # Check if server is running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "❌ Failed to start server"
        exit 1
    fi
    
    echo "✅ Server started successfully"
    echo ""
fi

# Function to run an example
run_example() {
    local name=$1
    local script=$2
    
    echo "=========================================="
    echo "Running: $name"
    echo "=========================================="
    echo ""
    
    if python "$script"; then
        echo ""
        echo "✅ $name completed successfully"
    else
        echo ""
        echo "❌ $name failed"
        return 1
    fi
    
    echo ""
    echo "Press Enter to continue..."
    read
    echo ""
}

# Run examples
run_example "Simple Bell State" "examples/simple_bell_state.py"
run_example "VQE-Style Ansatz" "examples/vqe_ansatz.py"
run_example "Multi-Qubit Entanglement" "examples/multi_qubit_entanglement.py"
run_example "Adaptive Circuit" "examples/adaptive_circuit.py"

echo "=========================================="
echo "All Examples Completed!"
echo "=========================================="
echo ""

# Clean up server if we started it
if [ ! -z "$SERVER_PID" ]; then
    echo "Stopping QMK server (PID: $SERVER_PID)..."
    kill $SERVER_PID
    wait $SERVER_PID 2>/dev/null || true
    rm -f /tmp/qmk.sock
    echo "✅ Server stopped"
fi

echo ""
echo "Done!"
