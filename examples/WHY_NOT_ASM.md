# Why Remaining Examples Cannot Be Written in Pure ASM

This document explains why each remaining Python example cannot be converted to pure ASM format.

---

## Framework Integration Examples (Moved to Subfolders)

### ✅ Organized into Subfolders

**Cirq:**
- `cirq/cirq_algorithms.py` - Requires Cirq framework

**Qiskit:**
- `qiskit/qiskit_algorithms.py` - Requires Qiskit framework

**Q#:**
- `qsharp/qsharp_algorithms.py` - Requires Q# compiler

**Reason:** These examples demonstrate integration with external quantum frameworks. They require framework-specific APIs and cannot be expressed in QVM ASM.

---

## QVM Examples That Cannot Be ASM

### Category 1: Already Using ASM ✅

#### 1. `simple_bell_state.py`
**Status:** Uses `bell_state.qasm`
**Why Not Pure ASM:** Python provides orchestration, telemetry display, and user interaction
**Python Role:**
- Client connection and capability negotiation
- Job submission and monitoring
- Result display and telemetry reporting
- Error handling

#### 2. `multi_qubit_entanglement.py`
**Status:** Uses `ghz_state.qasm` and `w_state.qasm`
**Why Not Pure ASM:** Python provides parameter calculation and result analysis
**Python Role:**
- Calculate W-state angles: `angle = 2 * math.asin(1 / math.sqrt(n_qubits - i))`
- Format qubit output lists
- Run multiple qubit counts (4, 6, 8 qubits)
- Analyze and display results

#### 3. `vqe_ansatz.py`
**Status:** Uses `vqe_ansatz.qasm`
**Why Not Pure ASM:** Python provides parameter sweeps and optimization
**Python Role:**
- Parameter sweeps (different theta values)
- Energy estimation from measurements
- Optimization loop (would be classical optimizer in real VQE)
- Result visualization

#### 4. `adaptive_circuit.py`
**Status:** Uses `adaptive_simple.qasm` and `adaptive_multi_round.qasm`
**Why Not Pure ASM:** Python provides orchestration and analysis
**Python Role:**
- Run multiple iterations with different seeds
- Analyze syndrome patterns
- Decode error correction results
- Display statistics

#### 5. `deutsch_jozsa.py`
**Status:** Uses `deutsch_jozsa.qasm` with `.param`
**Why Not Pure ASM:** Python provides testing and analysis
**Python Role:**
- Test all 5 oracle types
- Run 10 shots per oracle
- Statistical analysis (all measurements = |00⟩?)
- Success rate calculation
- Educational explanations

#### 6. `grovers_algorithm.py`
**Status:** Uses `grovers_search.qasm` with `.param`
**Why Not Pure ASM:** Python provides testing and analysis
**Python Role:**
- Test all 4 target states (00, 01, 10, 11)
- Run 50 shots per target
- Calculate success rates and probabilities
- Display histogram of results
- Scaling analysis

---

### Category 2: Complex Classical Processing

#### 7. `shors_algorithm.py`
**Why Not ASM:** Requires extensive classical computation
**Classical Components:**
```python
# Number theory
g = gcd(a, N)

# Classical period finding (verification)
def classical_period_finding(a, N):
    result = 1
    for r in range(1, N):
        result = (result * a) % N
        if result == 1:
            return r

# Factor extraction
def factor_from_period(N, a, r):
    if r % 2 != 0:
        return None, None
    x = pow(a, r // 2, N)
    if x == N - 1:
        return None, None
    factor1 = gcd(x + 1, N)
    factor2 = gcd(x - 1, N)
    return factor1, factor2
```

**Why Python Required:**
- GCD calculations (number theory)
- Modular exponentiation
- Period finding algorithm
- Factor extraction from period
- Classical pre/post-processing
- Educational explanations

**ASM Cannot:** Perform arbitrary classical computation, number theory, or complex control flow

---

#### 8. `advanced_qec_demo.py`
**Why Not ASM:** Requires error injection and statistical analysis
**Classical Components:**
```python
# Error injection
def inject_errors(circuit, error_rate):
    for qubit in circuit.qubits:
        if random.random() < error_rate:
            inject_error(qubit)

# Statistical analysis
def analyze_correction_success(results, n_trials):
    success_count = sum(1 for r in results if r['corrected'])
    success_rate = success_count / n_trials
    confidence_interval = calculate_ci(success_rate, n_trials)
    return {
        'success_rate': success_rate,
        'ci': confidence_interval,
        'trials': n_trials
    }

# Plot results
def plot_error_rates(data):
    plt.plot(error_rates, success_rates)
    plt.xlabel('Error Rate')
    plt.ylabel('Correction Success Rate')
    plt.show()
```

**Why Python Required:**
- Random error injection
- Statistical analysis (mean, variance, confidence intervals)
- Multiple trial orchestration
- Data visualization (plotting)
- Complex QEC protocol logic

**ASM Cannot:** Inject errors, perform statistics, or visualize data

---

### Category 3: Multi-Circuit Orchestration

#### 9. `architecture_exploration.py`
**Why Not ASM:** Compares multiple architectures
**Orchestration:**
```python
architectures = [
    "surface_code",
    "color_code", 
    "topological"
]

results = {}
for arch in architectures:
    circuit = create_circuit(arch)
    result = benchmark(circuit)
    results[arch] = result

# Comparative analysis
best_arch = max(results.items(), key=lambda x: x[1]['score'])
print(f"Best architecture: {best_arch[0]}")
```

**Why Python Required:**
- Create multiple circuit variants
- Run benchmarks on each
- Collect and compare results
- Generate comparison reports

**ASM Cannot:** Orchestrate multiple circuit executions or compare results

---

#### 10. `distributed_execution_demo.py`
**Why Not ASM:** Requires distributed computing
**Orchestration:**
```python
nodes = ["node1", "node2", "node3"]

# Distribute work
for i, node in enumerate(nodes):
    circuit_part = partition_circuit(circuit, i, len(nodes))
    submit_to_node(node, circuit_part)

# Gather results
results = []
for node in nodes:
    result = wait_for_node(node)
    results.append(result)

# Aggregate
final_result = aggregate_results(results)
```

**Why Python Required:**
- Network communication
- Work distribution
- Result aggregation
- Node coordination

**ASM Cannot:** Perform network operations or distributed coordination

---

#### 11. `compare_execution_paths.py`
**Why Not ASM:** Compares different execution backends
**Orchestration:**
```python
backends = [
    "simulator",
    "hardware_adapter",
    "qir_bridge"
]

for backend in backends:
    start = time.time()
    result = execute_on_backend(circuit, backend)
    elapsed = time.time() - start
    
    print(f"{backend}: {elapsed:.3f}s")
    verify_result(result)
```

**Why Python Required:**
- Backend selection and switching
- Timing measurements
- Result verification
- Comparative analysis

**ASM Cannot:** Switch backends or measure execution time

---

### Category 4: Infrastructure & Testing

#### 12. `benchmark.py`
**Why Not ASM:** Performance testing tool
**Infrastructure:**
```python
def benchmark_submission_latency(n_iterations=100):
    latencies = []
    for i in range(n_iterations):
        start = time.time()
        job_id = client.submit_job(graph)
        end = time.time()
        latencies.append((end - start) * 1000)
    
    print(f"Mean latency: {statistics.mean(latencies):.2f} ms")
    print(f"Median: {statistics.median(latencies):.2f} ms")
    print(f"Std dev: {statistics.stdev(latencies):.2f} ms")
```

**Why Python Required:**
- Timing measurements
- Statistical analysis
- Multiple iterations
- Performance reporting

**ASM Cannot:** Measure time or perform statistical analysis

---

#### 13. `asm_runner.py`
**Why Not ASM:** Utility for loading ASM files
**Infrastructure:**
```python
def load_asm_file(filename, params):
    filepath = asm_dir / filename
    with open(filepath, 'r') as f:
        asm = f.read()
    return asm

def assemble_file(filename, params):
    asm = load_asm_file(filename, params)
    return assemble(asm, str(filepath), params)
```

**Why Python Required:**
- File I/O
- Path resolution
- Parameter passing
- Error handling

**ASM Cannot:** Load other ASM files or perform file I/O

---

### Category 5: Advanced Features

#### 14. `hardware_adapters_demo.py`
**Why Not ASM:** Hardware backend integration
**Integration:**
```python
adapters = [
    IonTrapAdapter(),
    SuperconductingAdapter(),
    PhotonicAdapter()
]

for adapter in adapters:
    print(f"Testing {adapter.name}...")
    
    # Compile for specific hardware
    compiled = adapter.compile(circuit)
    
    # Execute on hardware
    result = adapter.execute(compiled)
    
    # Verify
    verify_result(result, adapter.constraints)
```

**Why Python Required:**
- Hardware-specific compilation
- Adapter pattern implementation
- Constraint checking
- Result verification

**ASM Cannot:** Interface with hardware adapters or compile for specific backends

---

#### 15. `jit_adaptivity_demo.py`
**Why Not ASM:** Just-in-time compilation
**JIT Logic:**
```python
def jit_compile_and_execute(circuit, runtime_data):
    # Analyze runtime data
    optimal_strategy = analyze_data(runtime_data)
    
    # Recompile circuit with optimizations
    optimized = jit_optimize(circuit, optimal_strategy)
    
    # Execute optimized version
    result = execute(optimized)
    
    return result
```

**Why Python Required:**
- Runtime analysis
- Dynamic optimization
- JIT compilation
- Adaptive execution

**ASM Cannot:** Perform JIT compilation or runtime optimization

---

#### 16. `measurement_bases_demo.py`
**Why Not ASM:** Low-level simulator demonstration
**Direct Simulator Access:**
```python
from kernel.simulator.logical_qubit import LogicalQubit

# Direct qubit manipulation
qubit = LogicalQubit("q0", profile, seed=42)
qubit.state = LogicalState.ZERO
qubit.apply_gate("H", 0.0)
outcome = qubit.measure("Z", 0.0)
```

**Why Python Required:**
- Direct simulator API access
- Low-level qubit manipulation
- Educational demonstration
- Not a circuit-based example

**ASM Cannot:** Access simulator internals or manipulate qubits directly

---

#### 17. `reversibility_demo.py`
**Why Not ASM:** Demonstrates reversible computing
**Reversibility Analysis:**
```python
def test_reversibility(circuit):
    # Forward execution
    forward_result = execute(circuit)
    
    # Generate inverse
    inverse_circuit = generate_inverse(circuit)
    
    # Backward execution
    backward_result = execute(inverse_circuit)
    
    # Verify reversibility
    assert forward_result == backward_result
    
    print("Circuit is reversible!")
```

**Why Python Required:**
- Circuit inversion
- Forward/backward execution
- Result comparison
- Reversibility verification

**ASM Cannot:** Generate inverse circuits or verify reversibility

---

#### 18. `qir_bridge_demo.py`
**Why Not ASM:** QIR integration demonstration
**QIR Bridge:**
```python
from kernel.qir_bridge.optimizer.converters import IRToQVMConverter

# Convert QIR to QVM
qir_circuit = load_qir("circuit.ll")
converter = IRToQVMConverter()
qvm_graph = converter.convert(qir_circuit)

# Execute
result = execute(qvm_graph)
```

**Why Python Required:**
- QIR parsing
- IR conversion
- Format translation
- Integration testing

**ASM Cannot:** Parse QIR or convert between IR formats

---

#### 19. `azure_qre_example.py`
**Why Not ASM:** Azure cloud integration
**Cloud Integration:**
```python
from azure.quantum import Workspace

# Connect to Azure
workspace = Workspace(
    resource_id="...",
    location="..."
)

# Submit to cloud
job = workspace.submit_job(circuit)
result = job.get_results()
```

**Why Python Required:**
- Cloud authentication
- Network communication
- Job submission to cloud
- Result retrieval

**ASM Cannot:** Perform network operations or cloud authentication

---

## Summary

### Files Organized into Subfolders (3)
- `cirq/cirq_algorithms.py` - Cirq framework
- `qiskit/qiskit_algorithms.py` - Qiskit framework
- `qsharp/qsharp_algorithms.py` - Q# framework

### QVM Examples That Cannot Be Pure ASM (19)

**Already Using ASM (6):**
- `simple_bell_state.py` - Orchestration
- `multi_qubit_entanglement.py` - Parameter calculation
- `vqe_ansatz.py` - Parameter sweeps
- `adaptive_circuit.py` - Analysis
- `deutsch_jozsa.py` - Testing
- `grovers_algorithm.py` - Testing

**Complex Classical Processing (2):**
- `shors_algorithm.py` - Number theory, GCD, modular arithmetic
- `advanced_qec_demo.py` - Error injection, statistics

**Multi-Circuit Orchestration (3):**
- `architecture_exploration.py` - Compare architectures
- `distributed_execution_demo.py` - Distributed computing
- `compare_execution_paths.py` - Backend comparison

**Infrastructure & Testing (2):**
- `benchmark.py` - Performance testing
- `asm_runner.py` - File loading utility

**Advanced Features (6):**
- `hardware_adapters_demo.py` - Hardware integration
- `jit_adaptivity_demo.py` - JIT compilation
- `measurement_bases_demo.py` - Low-level simulator
- `reversibility_demo.py` - Reversibility verification
- `qir_bridge_demo.py` - QIR integration
- `azure_qre_example.py` - Cloud integration

---

## Conclusion

**All remaining Python examples require capabilities beyond circuit description:**
- Classical computation (GCD, statistics, optimization)
- Orchestration (multiple executions, parameter sweeps)
- Integration (frameworks, hardware, cloud)
- Infrastructure (testing, benchmarking, utilities)
- Advanced features (JIT, reversibility, low-level access)

**ASM is perfect for:** Circuit description, parameterization, conditional logic
**Python is essential for:** Orchestration, analysis, integration, infrastructure

**Result:** Clean separation of concerns with appropriate tool for each task ✅
