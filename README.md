# ⚛️ Quantum Bridge IBC — Interference-Based Consensus

**Multi-agent consensus in milliseconds, not seconds.**

IBC uses quantum interference to resolve conflicts between autonomous agents. Instead of serial negotiation (A → B → conflict → backtrack), agents encode their goals as quantum states and find constructive overlap via interference circuits.

## Results

| Agents | Quantum Time | Classical Equivalent | Speedup |
|--------|-------------|---------------------|---------|
| 3 | 4ms | ~800ms | 200x |
| 5 | 1.6ms | ~4s | 2,500x |
| 10 | 7ms | ~18s | 2,500x |

## Quick Start

```bash
pip install pyqpanda numpy requests
```

### Direct Engine Use

```python
from ibc_engine import AgentState, IBCEngine

agents = [
    AgentState("Scheduler", [0.9, 0.1, 0.3, 0.2]),
    AgentState("CostOptimizer", [0.1, 0.9, 0.2, 0.1]),
    AgentState("LoadBalancer", [0.7, 0.3, 0.5, 0.2]),
]

engine = IBCEngine()
result = engine.find_consensus(agents, threshold=0.3)
print(f"Groups: {result['groups']}")
print(f"Time: {result['time_ms']}ms")
```

### Agent Connector (High-Level API)

```python
from agent_connector import AgentConsensus

ac = AgentConsensus(domain="gpu")
ac.add("price-scout", price=0.9, availability=0.3, performance=0.7, reliability=0.5)
ac.add("optimizer", price=0.2, availability=0.9, performance=0.3, reliability=0.4)
ac.add("risk-mgr", price=0.5, availability=0.6, performance=0.4, reliability=0.9)

print(ac.summary())
# ⚛️ Quantum Consensus — 3 agents, 4.3ms
#    Consensus groups: 1
#    Conflicts: 0
```

## Domains

Built-in feature dimensions for common use cases:

| Domain | Dimensions |
|--------|-----------|
| `gpu` | price, availability, performance, reliability |
| `energy` | cost, solar_output, grid_stability, storage |
| `market` | price, volume, trend, risk |
| `general` | priority, confidence, urgency, impact |

## How It Works

1. Each agent's goal becomes a normalized quantum state vector
2. Swap test circuits measure pairwise similarity via interference
3. Consensus matrix reveals natural groupings and conflicts
4. Results return in milliseconds — no iterative negotiation

Currently runs on PyQPanda quantum simulator. Ready for real quantum hardware.

## API Server

Run the IBC API server:

```bash
python api_server.py
# POST /api/consensus with {"agents": [...], "threshold": 0.3}
```

## License

MIT
