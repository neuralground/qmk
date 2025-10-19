"""
Distributed Executor

Executes QVM graphs across multiple compute nodes.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import time
import threading

from .graph_partitioner import GraphPartitioner, PartitionPlan, Partition
from .node_manager import NodeManager, ComputeNode


@dataclass
class ExecutionTask:
    """
    Execution task for a partition.
    
    Attributes:
        task_id: Task identifier
        partition: Partition to execute
        assigned_node: Node assigned to this task
        status: Task status
        start_time: Start time
        end_time: End time
        result: Execution result
    """
    task_id: str
    partition: Partition
    assigned_node: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    start_time: float = 0.0
    end_time: float = 0.0
    result: Optional[Dict] = None


class DistributedExecutor:
    """
    Executes QVM graphs across distributed nodes.
    
    Provides:
    - Graph partitioning
    - Task scheduling
    - Distributed execution
    - Result aggregation
    """
    
    def __init__(
        self,
        node_manager: NodeManager,
        num_partitions: int = 4
    ):
        """
        Initialize distributed executor.
        
        Args:
            node_manager: Node manager instance
            num_partitions: Number of partitions
        """
        self.node_manager = node_manager
        self.partitioner = GraphPartitioner(num_partitions)
        self.active_executions: Dict[str, Dict] = {}
    
    def execute_distributed(
        self,
        job_id: str,
        graph: Dict,
        partition_strategy: str = "balanced"
    ) -> Dict:
        """
        Execute graph in distributed manner.
        
        Args:
            job_id: Job identifier
            graph: QVM graph
            partition_strategy: Partitioning strategy
        
        Returns:
            Execution result
        """
        # Partition graph
        if partition_strategy == "qubit":
            plan = self.partitioner.partition_by_qubits(graph, f"{job_id}_plan")
        elif partition_strategy == "time":
            plan = self.partitioner.partition_by_time(graph, f"{job_id}_plan")
        else:  # balanced
            plan = self.partitioner.partition_balanced(graph, f"{job_id}_plan")
        
        # Create execution tasks
        tasks = self._create_tasks(job_id, plan)
        
        # Schedule and execute tasks
        result = self._execute_tasks(job_id, tasks, plan)
        
        return result
    
    def _create_tasks(
        self,
        job_id: str,
        plan: PartitionPlan
    ) -> List[ExecutionTask]:
        """Create execution tasks from partition plan."""
        tasks = []
        
        for idx, partition in enumerate(plan.partitions):
            task = ExecutionTask(
                task_id=f"{job_id}_task_{idx}",
                partition=partition
            )
            tasks.append(task)
        
        return tasks
    
    def _execute_tasks(
        self,
        job_id: str,
        tasks: List[ExecutionTask],
        plan: PartitionPlan
    ) -> Dict:
        """
        Execute tasks with dependency management.
        
        Args:
            job_id: Job identifier
            tasks: List of tasks
            plan: Partition plan
        
        Returns:
            Aggregated result
        """
        # Track execution
        self.active_executions[job_id] = {
            "tasks": tasks,
            "plan": plan,
            "start_time": time.time(),
            "status": "running"
        }
        
        # Build task dependency graph
        task_deps = self._build_task_dependencies(tasks)
        
        # Execute tasks in dependency order
        completed_tasks = set()
        results = {}
        max_iterations = len(tasks) * 10  # Prevent infinite loops
        iteration = 0
        
        while len(completed_tasks) < len(tasks) and iteration < max_iterations:
            iteration += 1
            
            # Find ready tasks
            ready_tasks = [
                task for task in tasks
                if task.status == "pending" and
                task_deps[task.task_id].issubset(completed_tasks)
            ]
            
            if not ready_tasks:
                # Check for failures
                failed = [t for t in tasks if t.status == "failed"]
                if failed:
                    break
                
                # Check if any tasks are running
                running = [t for t in tasks if t.status == "running"]
                if not running:
                    # No ready, no running, no failed = deadlock
                    break
                
                # Wait for running tasks
                time.sleep(0.01)
                continue
            
            # Execute ready tasks in parallel
            threads = []
            for task in ready_tasks:
                thread = threading.Thread(
                    target=self._execute_task,
                    args=(task, results)
                )
                thread.start()
                threads.append(thread)
            
            # Wait for completion with timeout
            for thread in threads:
                thread.join(timeout=5.0)  # 5 second timeout per task
            
            # Update completed set
            for task in ready_tasks:
                if task.status == "completed":
                    completed_tasks.add(task.task_id)
        
        # Aggregate results
        execution_time = time.time() - self.active_executions[job_id]["start_time"]
        
        self.active_executions[job_id]["status"] = "completed"
        self.active_executions[job_id]["end_time"] = time.time()
        
        return {
            "job_id": job_id,
            "status": "completed",
            "execution_time": execution_time,
            "num_partitions": len(tasks),
            "parallelism": plan.parallelism,
            "communication_cost": plan.communication_cost,
            "results": results
        }
    
    def _execute_task(
        self,
        task: ExecutionTask,
        results: Dict
    ):
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            results: Shared results dictionary
        """
        # Select node
        node = self.node_manager.select_best_node({
            "qubits": len(task.partition.qubits)
        })
        
        if not node:
            task.status = "failed"
            return
        
        task.assigned_node = node.node_id
        task.status = "running"
        task.start_time = time.time()
        
        # Assign job to node
        self.node_manager.assign_job(node.node_id, task.task_id)
        
        # Simulate execution
        # In real implementation, would send partition to node via RPC
        time.sleep(task.partition.estimated_time)
        
        # Mark complete
        task.status = "completed"
        task.end_time = time.time()
        
        # Store result
        results[task.task_id] = {
            "partition_id": task.partition.partition_id,
            "node_id": node.node_id,
            "execution_time": task.end_time - task.start_time,
            "num_nodes": len(task.partition.nodes)
        }
        
        # Complete job on node
        self.node_manager.complete_job(node.node_id, task.task_id)
    
    def _build_task_dependencies(
        self,
        tasks: List[ExecutionTask]
    ) -> Dict[str, Set[str]]:
        """Build task dependency graph."""
        # Map partition ID to task ID
        partition_to_task = {
            task.partition.partition_id: task.task_id
            for task in tasks
        }
        
        # Build dependencies
        task_deps = {}
        
        for task in tasks:
            deps = set()
            for dep_partition_id in task.partition.dependencies:
                if dep_partition_id in partition_to_task:
                    deps.add(partition_to_task[dep_partition_id])
            task_deps[task.task_id] = deps
        
        return task_deps
    
    def get_execution_status(self, job_id: str) -> Optional[Dict]:
        """
        Get execution status.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Status dictionary or None
        """
        if job_id not in self.active_executions:
            return None
        
        execution = self.active_executions[job_id]
        tasks = execution["tasks"]
        
        return {
            "job_id": job_id,
            "status": execution["status"],
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for t in tasks if t.status == "completed"),
            "running_tasks": sum(1 for t in tasks if t.status == "running"),
            "failed_tasks": sum(1 for t in tasks if t.status == "failed")
        }
    
    def get_execution_stats(self) -> Dict:
        """
        Get execution statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "active_executions": len([
                e for e in self.active_executions.values()
                if e["status"] == "running"
            ]),
            "completed_executions": len([
                e for e in self.active_executions.values()
                if e["status"] == "completed"
            ]),
            "total_executions": len(self.active_executions)
        }
