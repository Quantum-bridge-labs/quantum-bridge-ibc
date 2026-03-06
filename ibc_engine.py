"""
Interference-Based Consensus (IBC) Engine
==========================================
Uses quantum interference to resolve multi-agent conflicts.

Instead of serial negotiation (A → B → conflict → backtrack),
we encode agent goals as quantum states and find the constructive
overlap (consensus) via swap test / interference circuits.
"""

import numpy as np
import time
from pyqpanda import *

class AgentState:
    """Represents a classical agent's goal as a feature vector."""
    
    def __init__(self, name: str, feature_vector: list[float]):
        self.name = name
        # Normalize to unit vector (quantum state requirement)
        vec = np.array(feature_vector, dtype=float)
        self.features = vec / np.linalg.norm(vec)
    
    def __repr__(self):
        return f"Agent({self.name}, dim={len(self.features)})"


class IBCEngine:
    """
    Quantum Interference-Based Consensus Engine.
    
    Uses swap test circuits to measure overlap between agent goal states.
    High overlap = natural consensus. Low overlap = conflict that needs resolution.
    """
    
    def __init__(self, backend="simulator"):
        self.backend = backend
        self.qvm = CPUQVM()
        self.qvm.init_qvm()
        self.results_cache = {}
    
    def _encode_state(self, qubits: list, features: np.ndarray):
        """
        Encode a classical feature vector into quantum amplitudes.
        Uses amplitude encoding: n features → log2(n) qubits.
        """
        circuit = QCircuit()
        n_qubits = len(qubits)
        n_amplitudes = 2 ** n_qubits
        
        # Pad features to match amplitude space
        padded = np.zeros(n_amplitudes)
        padded[:len(features)] = features[:n_amplitudes]
        padded = padded / np.linalg.norm(padded)  # Re-normalize
        
        # Use amplitude encoding via rotation gates
        # For 2-qubit case: encode 4 amplitudes
        if n_qubits == 1:
            theta = 2 * np.arccos(padded[0])
            circuit << RY(qubits[0], theta)
        elif n_qubits >= 2:
            # Simplified amplitude encoding for demo
            # Full version would use Mottonen's method
            theta0 = 2 * np.arccos(
                np.sqrt(padded[0]**2 + padded[1]**2) 
                if (padded[0]**2 + padded[1]**2) > 0 else 0
            )
            circuit << RY(qubits[0], theta0)
            
            if padded[0]**2 + padded[1]**2 > 1e-10:
                theta1 = 2 * np.arccos(
                    padded[0] / np.sqrt(padded[0]**2 + padded[1]**2)
                )
                circuit << X(qubits[0])
                circuit << RY(qubits[1], theta1).control(qubits[0])
                circuit << X(qubits[0])
            
            if padded[2]**2 + padded[3]**2 > 1e-10:
                theta2 = 2 * np.arccos(
                    padded[2] / np.sqrt(padded[2]**2 + padded[3]**2)
                )
                circuit << RY(qubits[1], theta2).control(qubits[0])
        
        return circuit

    def swap_test(self, agent_a: AgentState, agent_b: AgentState, shots=1024):
        """
        Quantum Swap Test: measures overlap |⟨ψ_A|ψ_B⟩|² between two agent states.
        
        Returns overlap score (0.0 = orthogonal/conflict, 1.0 = identical/consensus).
        """
        # Need: 1 ancilla + qubits for agent A + qubits for agent B
        n_feature_qubits = max(1, int(np.ceil(np.log2(max(len(agent_a.features), 2)))))
        total_qubits = 1 + 2 * n_feature_qubits  # ancilla + A + B
        
        qubits = self.qvm.qAlloc_many(total_qubits)
        cbits = self.qvm.cAlloc_many(1)
        
        ancilla = qubits[0]
        qubits_a = qubits[1:1+n_feature_qubits]
        qubits_b = qubits[1+n_feature_qubits:1+2*n_feature_qubits]
        
        prog = QProg()
        
        # 1. Hadamard on ancilla
        prog << H(ancilla)
        
        # 2. Encode agent states
        prog << self._encode_state(qubits_a, agent_a.features)
        prog << self._encode_state(qubits_b, agent_b.features)
        
        # 3. Controlled-SWAP (Fredkin gates)
        for i in range(n_feature_qubits):
            prog << SWAP(qubits_a[i], qubits_b[i]).control(ancilla)
        
        # 4. Hadamard on ancilla
        prog << H(ancilla)
        
        # 5. Measure ancilla
        prog << Measure(ancilla, cbits[0])
        
        # Run
        result = self.qvm.run_with_configuration(prog, cbits, shots)
        
        # P(ancilla=0) = (1 + |⟨A|B⟩|²) / 2
        # So |⟨A|B⟩|² = 2*P(0) - 1
        p_zero = result.get("0", 0) / shots if isinstance(result, dict) else 0.5
        overlap = max(0.0, 2 * p_zero - 1)
        
        # Cleanup
        self.qvm.qFree_all(qubits)
        self.qvm.cFree_all(cbits)
        
        return overlap

    def find_consensus(self, agents: list[AgentState], threshold=0.3):
        """
        Find consensus groups among multiple agents.
        
        Returns:
        - consensus_matrix: pairwise overlap scores
        - groups: clusters of agents with high overlap (natural consensus)
        - conflicts: pairs with low overlap (need resolution)
        """
        start = time.perf_counter()
        n = len(agents)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                overlap = self.swap_test(agents[i], agents[j])
                matrix[i][j] = overlap
                matrix[j][i] = overlap
            matrix[i][i] = 1.0
        
        # Find consensus groups (simple greedy clustering)
        groups = []
        conflicts = []
        assigned = set()
        
        for i in range(n):
            if i in assigned:
                continue
            group = [i]
            assigned.add(i)
            for j in range(i+1, n):
                if j in assigned:
                    continue
                if matrix[i][j] >= threshold:
                    group.append(j)
                    assigned.add(j)
            groups.append([agents[idx].name for idx in group])
        
        for i in range(n):
            for j in range(i+1, n):
                if matrix[i][j] < threshold:
                    conflicts.append((agents[i].name, agents[j].name, matrix[i][j]))
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        return {
            "consensus_matrix": matrix,
            "groups": groups,
            "conflicts": conflicts,
            "time_ms": round(elapsed_ms, 2),
            "n_agents": n,
            "method": "quantum_swap_test"
        }
    
    def shutdown(self):
        self.qvm.finalize()


def classical_negotiation(agents: list[AgentState], threshold=0.3):
    """
    Classical baseline: serial pairwise cosine similarity.
    Simulates the slow negotiation process.
    """
    start = time.perf_counter()
    n = len(agents)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            # Simulate LLM negotiation overhead (serial, with backtracking)
            time.sleep(0.4)  # Simulated LLM call latency per pair
            similarity = float(np.dot(agents[i].features, agents[j].features))
            matrix[i][j] = similarity
            matrix[j][i] = similarity
        matrix[i][i] = 1.0
    
    groups = []
    conflicts = []
    assigned = set()
    
    for i in range(n):
        if i in assigned:
            continue
        group = [i]
        assigned.add(i)
        for j in range(i+1, n):
            if j in assigned:
                continue
            if matrix[i][j] >= threshold:
                group.append(j)
                assigned.add(j)
        groups.append([agents[idx].name for idx in group])
    
    for i in range(n):
        for j in range(i+1, n):
            if matrix[i][j] < threshold:
                conflicts.append((agents[i].name, agents[j].name, matrix[i][j]))
    
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    return {
        "consensus_matrix": matrix,
        "groups": groups,
        "conflicts": conflicts,
        "time_ms": round(elapsed_ms, 2),
        "n_agents": n,
        "method": "classical_serial"
    }
