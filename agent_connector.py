#!/usr/bin/env python3
"""
Agent → IBC Connector
======================
Bridges autonomous agents to the quantum consensus engine.
Each agent submits its recommendation as a feature vector,
IBC finds optimal consensus in ~2ms.

Usage:
    from agent_connector import AgentConsensus
    
    ac = AgentConsensus()
    ac.add("gpu-oracle", price=0.9, availability=0.3, performance=0.7, reliability=0.5)
    ac.add("cost-optimizer", price=0.2, availability=0.8, performance=0.4, reliability=0.6)
    ac.add("crypto-scout", price=0.6, availability=0.5, performance=0.3, reliability=0.2)
    result = ac.resolve()
"""

import requests
import time
import json

IBC_URL = "http://localhost:3800/api/consensus"

# Predefined feature dimensions for each domain
DOMAINS = {
    "gpu": ["price", "availability", "performance", "reliability"],
    "energy": ["cost", "solar_output", "grid_stability", "storage"],
    "market": ["price", "volume", "trend", "risk"],
    "general": ["priority", "confidence", "urgency", "impact"],
}


class AgentConsensus:
    def __init__(self, domain="general", threshold=0.3, ibc_url=IBC_URL):
        self.domain = domain
        self.dimensions = DOMAINS.get(domain, DOMAINS["general"])
        self.agents = []
        self.threshold = threshold
        self.ibc_url = ibc_url
    
    def add(self, name, **kwargs):
        """Add an agent's recommendation. kwargs should match domain dimensions."""
        features = []
        for dim in self.dimensions:
            val = kwargs.get(dim, 0.5)  # default to neutral
            features.append(max(0.0, min(1.0, float(val))))
        self.agents.append({"name": name, "features": features})
        return self
    
    def add_raw(self, name, features):
        """Add agent with raw feature vector."""
        self.agents.append({"name": name, "features": features})
        return self
    
    def resolve(self):
        """Send to IBC engine and get consensus."""
        if len(self.agents) < 2:
            return {"error": "Need at least 2 agents"}
        
        start = time.perf_counter()
        try:
            r = requests.post(self.ibc_url, json={
                "agents": self.agents,
                "threshold": self.threshold
            }, timeout=5)
            network_ms = (time.perf_counter() - start) * 1000
            
            if r.status_code != 200:
                return {"error": f"IBC returned {r.status_code}: {r.text}"}
            
            result = r.json()
            result["network_ms"] = round(network_ms, 2)
            result["total_ms"] = round(network_ms, 2)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def summary(self):
        """Human-readable consensus summary."""
        result = self.resolve()
        if "error" in result:
            return f"❌ Consensus failed: {result['error']}"
        
        q = result.get("quantum", {})
        lines = [
            f"⚛️ Quantum Consensus — {result['n_agents']} agents, {q.get('time_ms', '?')}ms",
            f"   Consensus groups: {len(q.get('groups', []))}",
            f"   Conflicts: {q.get('conflicts', 0)}",
        ]
        
        for i, group in enumerate(q.get("groups", [])):
            lines.append(f"   Group {i+1}: {', '.join(group)}")
        
        if q.get("conflict_details"):
            lines.append(f"   ⚠️ Conflicts:")
            for a, b, score in q["conflict_details"]:
                lines.append(f"      {a} ↔ {b} (similarity: {score})")
        
        return "\n".join(lines)


def test_gpu_consensus():
    """Test: 3 GPU agents find consensus on best deal."""
    print("=" * 50)
    print("TEST 1: GPU Deal Consensus")
    print("=" * 50)
    
    ac = AgentConsensus(domain="gpu")
    # GPU Oracle: found a cheap H100 with good perf
    ac.add("gpu-oracle", price=0.9, availability=0.3, performance=0.8, reliability=0.5)
    # Cost Optimizer: wants cheapest option regardless
    ac.add("cost-optimizer", price=0.2, availability=0.9, performance=0.3, reliability=0.4)
    # Crypto Scout: spotted a deal with high reliability
    ac.add("crypto-scout", price=0.5, availability=0.6, performance=0.4, reliability=0.9)
    
    print(ac.summary())
    print()


def test_energy_consensus():
    """Test: Energy agents decide power strategy."""
    print("=" * 50)
    print("TEST 2: Energy Grid Consensus")
    print("=" * 50)
    
    ac = AgentConsensus(domain="energy")
    ac.add("solar-optimizer", cost=0.8, solar_output=0.9, grid_stability=0.3, storage=0.4)
    ac.add("grid-manager", cost=0.3, solar_output=0.2, grid_stability=0.9, storage=0.5)
    ac.add("battery-agent", cost=0.5, solar_output=0.4, grid_stability=0.6, storage=0.9)
    ac.add("cost-agent", cost=0.9, solar_output=0.1, grid_stability=0.4, storage=0.2)
    
    print(ac.summary())
    print()


def test_market_consensus():
    """Test: Market agents agree on trading signal."""
    print("=" * 50)
    print("TEST 3: Market Signal Consensus")
    print("=" * 50)
    
    ac = AgentConsensus(domain="market", threshold=0.4)
    ac.add("trend-follower", price=0.8, volume=0.7, trend=0.9, risk=0.3)
    ac.add("contrarian", price=0.2, volume=0.3, trend=0.1, risk=0.8)
    ac.add("momentum", price=0.7, volume=0.9, trend=0.8, risk=0.4)
    ac.add("value-hunter", price=0.9, volume=0.2, trend=0.3, risk=0.5)
    ac.add("risk-manager", price=0.3, volume=0.4, trend=0.5, risk=0.9)
    
    print(ac.summary())
    print()


def test_speed():
    """Benchmark: how fast is consensus?"""
    print("=" * 50)
    print("TEST 4: Speed Benchmark (10 agents)")
    print("=" * 50)
    
    ac = AgentConsensus(domain="general")
    for i in range(10):
        import random
        ac.add(f"agent-{i}", 
               priority=random.random(),
               confidence=random.random(),
               urgency=random.random(),
               impact=random.random())
    
    result = ac.resolve()
    q = result.get("quantum", {})
    print(f"   Agents: {result.get('n_agents', '?')}")
    print(f"   Quantum time: {q.get('time_ms', '?')}ms")
    print(f"   Network roundtrip: {result.get('network_ms', '?')}ms")
    print(f"   Groups: {len(q.get('groups', []))}")
    print(f"   Conflicts: {q.get('conflicts', 0)}")
    print()


if __name__ == "__main__":
    test_gpu_consensus()
    test_energy_consensus()
    test_market_consensus()
    test_speed()
    print("🎉 All agent consensus tests complete!")
