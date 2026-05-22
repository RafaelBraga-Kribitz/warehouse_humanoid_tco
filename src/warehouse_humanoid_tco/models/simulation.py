"""SimPy discrete-event simulation of warehouse operations.

Architecture-agnostic via WarehouseScenario config object.
See PROJECT_CHARTER.md §4 Module 2 and config/autostore_baseline.yaml.
ADR-0003: AutoStore is the only calibrated architecture in v1.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import simpy


@dataclass
class AgentProfile:
    agent_type: str
    cycle_time_mean: float
    cycle_time_std: float
    count: int
    seed: int = 42


@dataclass
class WarehouseScenario:
    scenario_id: str
    architecture: str
    total_agents: int
    agent_profiles: list[AgentProfile]
    order_arrival_rate_per_hour: float
    shift_hours: float = 8.0
    seed: int = 42
    metadata: dict[str, Any] = field(default_factory=dict)


def run_scenario(scenario: WarehouseScenario, run_id: int = 0) -> dict[str, Any]:
    """Run one simulation episode for a given scenario.

    Returns a dict matching SimulationRunSchema fields.
    """
    rng = np.random.default_rng(scenario.seed + run_id)
    env = simpy.Environment()

    completed_orders: list[float] = []
    queue_lengths: list[float] = []

    arrival_rate_per_second = scenario.order_arrival_rate_per_hour / 3600
    shift_seconds = scenario.shift_hours * 3600

    resources = {
        profile.agent_type: simpy.Resource(env, capacity=profile.count)
        for profile in scenario.agent_profiles
    }

    def pick_order(order_id: int) -> Any:
        eligible = [p for p in scenario.agent_profiles if p.count > 0]
        if not eligible:
            return

        weights = np.array([p.count for p in eligible], dtype=float)
        weights /= weights.sum()
        chosen_idx = int(rng.choice(len(eligible), p=weights))
        profile = eligible[chosen_idx]

        res = resources[profile.agent_type]
        with res.request() as req:
            queue_lengths.append(len(res.queue))
            yield req
            cycle_time = float(rng.normal(profile.cycle_time_mean, profile.cycle_time_std))
            cycle_time = max(cycle_time, 1.0)
            yield env.timeout(cycle_time)
        completed_orders.append(env.now)

    def order_generator() -> Any:
        order_id = 0
        while True:
            interarrival = float(rng.exponential(1.0 / arrival_rate_per_second))
            yield env.timeout(interarrival)
            env.process(pick_order(order_id))
            order_id += 1

    env.process(order_generator())
    env.run(until=shift_seconds)

    throughput = len(completed_orders)
    queue_mean = float(np.mean(queue_lengths)) if queue_lengths else 0.0

    utilizations: dict[str, float | None] = {}
    for profile in scenario.agent_profiles:
        key = f"utilization_{profile.agent_type}"
        utilizations[key] = None

    return {
        "scenario_id": scenario.scenario_id,
        "run_id": run_id,
        "throughput_orders_per_shift": float(throughput),
        "queue_length_mean": queue_mean,
        "pipeline_version": "0.1.0",
        "seed": scenario.seed + run_id,
        **utilizations,
    }
