"""
Teleportation Planner

Plans optimal teleportation gate injection for fault-tolerant execution.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class TeleportationSite:
    """
    Represents a teleportation injection site.
    
    Attributes:
        site_id: Unique site identifier
        node_id: Node where teleportation occurs
        gate_type: Gate type requiring teleportation
        qubits: Qubits involved
        magic_state_type: Type of magic state needed
        cost: Estimated cost
        priority: Site priority
    """
    site_id: str
    node_id: str
    gate_type: str
    qubits: List[str]
    magic_state_type: str
    cost: float = 1.0
    priority: int = 0


@dataclass
class TeleportationPlan:
    """
    Complete teleportation plan for a graph.
    
    Attributes:
        plan_id: Unique plan identifier
        graph_id: Associated graph ID
        sites: Teleportation sites
        total_cost: Total plan cost
        magic_state_requirements: Magic state requirements
        execution_order: Optimal execution order
    """
    plan_id: str
    graph_id: str
    sites: List[TeleportationSite] = field(default_factory=list)
    total_cost: float = 0.0
    magic_state_requirements: Dict[str, int] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)


class TeleportationPlanner:
    """
    Plans teleportation gate injection.
    
    Provides:
    - Identification of non-Clifford gates
    - Magic state requirement calculation
    - Optimal injection site selection
    - Execution order optimization
    """
    
    # Gates requiring teleportation (non-Clifford)
    NON_CLIFFORD_GATES = {
        "T", "T_DAG", "RZ", "RY", "RX"
    }
    
    # Magic state types for gates
    MAGIC_STATE_MAP = {
        "T": "T_state",
        "T_DAG": "T_state",
        "RZ": "rotation_state",
        "RY": "rotation_state",
        "RX": "rotation_state"
    }
    
    def __init__(self):
        """Initialize teleportation planner."""
        self.plans: Dict[str, TeleportationPlan] = {}
        self.plan_counter = 0
        self.site_counter = 0
    
    def create_plan(
        self,
        graph_id: str,
        graph_nodes: List[Dict]
    ) -> TeleportationPlan:
        """
        Create teleportation plan for a graph.
        
        Args:
            graph_id: Graph identifier
            graph_nodes: List of graph nodes
        
        Returns:
            TeleportationPlan object
        """
        plan_id = f"tplan_{self.plan_counter}"
        self.plan_counter += 1
        
        plan = TeleportationPlan(
            plan_id=plan_id,
            graph_id=graph_id
        )
        
        # Identify teleportation sites
        for node in graph_nodes:
            if self._requires_teleportation(node):
                site = self._create_site(node)
                plan.sites.append(site)
        
        # Calculate requirements
        plan.magic_state_requirements = self._calculate_requirements(plan.sites)
        
        # Determine execution order
        plan.execution_order = self._optimize_execution_order(plan.sites)
        
        # Calculate total cost
        plan.total_cost = sum(site.cost for site in plan.sites)
        
        self.plans[plan_id] = plan
        
        return plan
    
    def _requires_teleportation(self, node: Dict) -> bool:
        """
        Check if node requires teleportation.
        
        Args:
            node: Graph node
        
        Returns:
            True if teleportation required
        """
        op = node.get("op", "")
        return op in self.NON_CLIFFORD_GATES
    
    def _create_site(self, node: Dict) -> TeleportationSite:
        """
        Create teleportation site for node.
        
        Args:
            node: Graph node
        
        Returns:
            TeleportationSite object
        """
        site_id = f"site_{self.site_counter}"
        self.site_counter += 1
        
        gate_type = node.get("op", "")
        magic_state = self.MAGIC_STATE_MAP.get(gate_type, "unknown")
        
        # Estimate cost based on gate type
        if gate_type in ["T", "T_DAG"]:
            cost = 1.0
        else:  # Rotation gates
            cost = 2.0
        
        site = TeleportationSite(
            site_id=site_id,
            node_id=node.get("node_id", ""),
            gate_type=gate_type,
            qubits=node.get("qubits", []),
            magic_state_type=magic_state,
            cost=cost
        )
        
        return site
    
    def _calculate_requirements(
        self,
        sites: List[TeleportationSite]
    ) -> Dict[str, int]:
        """
        Calculate magic state requirements.
        
        Args:
            sites: List of teleportation sites
        
        Returns:
            Dictionary of magic state counts
        """
        requirements = {}
        
        for site in sites:
            state_type = site.magic_state_type
            requirements[state_type] = requirements.get(state_type, 0) + 1
        
        return requirements
    
    def _optimize_execution_order(
        self,
        sites: List[TeleportationSite]
    ) -> List[str]:
        """
        Optimize execution order of teleportation sites.
        
        Args:
            sites: List of teleportation sites
        
        Returns:
            List of site IDs in optimal order
        """
        # Simple heuristic: execute in node order
        # In practice, would consider dependencies and resource availability
        return [site.site_id for site in sites]
    
    def optimize_plan(
        self,
        plan_id: str,
        optimization_goal: str = "minimize_cost"
    ) -> TeleportationPlan:
        """
        Optimize a teleportation plan.
        
        Args:
            plan_id: Plan identifier
            optimization_goal: Optimization goal
        
        Returns:
            Optimized TeleportationPlan
        """
        plan = self.get_plan(plan_id)
        
        if optimization_goal == "minimize_cost":
            # Sort sites by cost (lowest first)
            plan.sites.sort(key=lambda s: s.cost)
        elif optimization_goal == "minimize_latency":
            # Prioritize parallel execution
            plan.sites.sort(key=lambda s: s.priority, reverse=True)
        
        # Recalculate execution order
        plan.execution_order = self._optimize_execution_order(plan.sites)
        
        return plan
    
    def estimate_magic_state_throughput(
        self,
        plan: TeleportationPlan,
        factory_throughput: Dict[str, float]
    ) -> Dict:
        """
        Estimate magic state factory throughput requirements.
        
        Args:
            plan: Teleportation plan
            factory_throughput: Factory throughput rates (states/second)
        
        Returns:
            Dictionary with throughput analysis
        """
        requirements = plan.magic_state_requirements
        
        # Calculate time to produce required states
        production_times = {}
        for state_type, count in requirements.items():
            throughput = factory_throughput.get(state_type, 1.0)
            production_times[state_type] = count / throughput
        
        # Total time is max (bottleneck)
        total_time = max(production_times.values()) if production_times else 0
        
        return {
            "requirements": requirements,
            "production_times": production_times,
            "total_time": total_time,
            "bottleneck": max(production_times.items(), key=lambda x: x[1])[0] if production_times else None
        }
    
    def merge_plans(
        self,
        plan_ids: List[str]
    ) -> TeleportationPlan:
        """
        Merge multiple plans into one.
        
        Args:
            plan_ids: List of plan IDs
        
        Returns:
            Merged TeleportationPlan
        """
        plans = [self.get_plan(pid) for pid in plan_ids]
        
        merged_plan_id = f"tplan_{self.plan_counter}"
        self.plan_counter += 1
        
        merged_plan = TeleportationPlan(
            plan_id=merged_plan_id,
            graph_id="merged"
        )
        
        # Merge sites
        for plan in plans:
            merged_plan.sites.extend(plan.sites)
        
        # Recalculate requirements
        merged_plan.magic_state_requirements = self._calculate_requirements(
            merged_plan.sites
        )
        
        # Recalculate order
        merged_plan.execution_order = self._optimize_execution_order(
            merged_plan.sites
        )
        
        # Recalculate cost
        merged_plan.total_cost = sum(site.cost for site in merged_plan.sites)
        
        self.plans[merged_plan_id] = merged_plan
        
        return merged_plan
    
    def get_plan(self, plan_id: str) -> TeleportationPlan:
        """
        Get a plan.
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            TeleportationPlan object
        """
        if plan_id not in self.plans:
            raise KeyError(f"Plan '{plan_id}' not found")
        
        return self.plans[plan_id]
    
    def get_plan_statistics(self, plan_id: str) -> Dict:
        """
        Get statistics for a plan.
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Dictionary with statistics
        """
        plan = self.get_plan(plan_id)
        
        # Count by gate type
        by_gate_type = {}
        for site in plan.sites:
            by_gate_type[site.gate_type] = by_gate_type.get(site.gate_type, 0) + 1
        
        return {
            "total_sites": len(plan.sites),
            "total_cost": plan.total_cost,
            "magic_state_requirements": plan.magic_state_requirements,
            "by_gate_type": by_gate_type
        }
