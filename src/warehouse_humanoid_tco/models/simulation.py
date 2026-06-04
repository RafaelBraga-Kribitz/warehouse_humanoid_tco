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


def predict_utilisation(scenario: WarehouseScenario) -> float:
    """Predict the queueing utilisation rho = lambda * E[S] / c for `scenario`.

    Closes F-028: every simulation must compute the predicted utilisation
    *before* running so saturation (rho >= 1) is detected up front, not
    discovered after a 15-run × 5-scenario batch finishes with queues blowing
    up.

    For the heterogeneous M/G/c with proportional routing (orders dispatched
    to agent type t with probability count_t / total_count), the mean service
    time across the fleet is:

        E[S] = sum(count_t / total_count * mean_t)

    and the system service rate is c * (1 / E[S]), so:

        rho = lambda * E[S] / c

    where lambda is the arrival rate in the same units as 1/E[S] (per second).
    Returns 0.0 when the configuration has no eligible agents (degenerate),
    so callers always get a real float and don't have to special-case None.
    """
    eligible = [p for p in scenario.agent_profiles if p.count > 0]
    total_agents = sum(p.count for p in eligible)
    if total_agents == 0:
        return 0.0
    mean_service_seconds = sum((p.count / total_agents) * p.cycle_time_mean for p in eligible)
    arrival_rate_per_second = scenario.order_arrival_rate_per_hour / 3600.0
    return arrival_rate_per_second * mean_service_seconds / total_agents


RHO_WARN_THRESHOLD = 0.95
RHO_SATURATION_THRESHOLD = 1.0

# F-044: industrial-IE convention for "max sustainable" utilisation. At rho > 0.95
# the M/M/c mean queue length ~ rho/(1-rho) starts to explode; 0.85 leaves slack
# for arrival burstiness and service-time variability while still being a
# meaningful capacity ceiling, not just half-load.
DEFAULT_CAPACITY_CEILING_RHO = 0.85


def compute_capacity_ceiling(
    scenario: WarehouseScenario,
    target_rho: float = DEFAULT_CAPACITY_CEILING_RHO,
) -> dict[str, Any]:
    """Closed-form max-sustainable arrival rate under per-agent-type stability.

    Closes F-044. Under the proportional routing implemented in `run_scenario`
    (orders dispatched to agent type t with probability count_t / total_count),
    the per-type load is:

        lambda_t = lambda * (count_t / total_count)     # arrivals/sec to t
        rho_t    = lambda_t / (count_t / cycle_time_t)
                 = lambda * cycle_time_t / total_count

    The system is stable iff every per-type rho_t < 1; the binding constraint
    is therefore the slowest agent type:

        lambda_max = target_rho * total_count / max(cycle_time_t)

    `predict_utilisation` (F-028) uses the count-weighted mean cycle time and
    correctly reports the aggregate rho for saturation-gate purposes, but the
    weighted mean understates the bottleneck in heterogeneous mixes. For the
    capacity-ceiling chart we need the per-type bound; both formulas coincide
    when only one agent type is eligible (homogeneous scenarios).

    target_rho defaults to 0.85: standard industrial-IE design utilisation
    that bounds mean queue length while still calling the result a "capacity
    ceiling" rather than half-load. Pass 1.0 for the theoretical maximum at
    the cost of unbounded queue growth at the operating point.
    """
    eligible = [p for p in scenario.agent_profiles if p.count > 0]
    total_agents = sum(p.count for p in eligible)
    if total_agents == 0:
        return {
            "scenario_id": scenario.scenario_id,
            "target_rho": target_rho,
            "total_agents": 0,
            "bottleneck_agent_type": None,
            "bottleneck_cycle_time_seconds": 0.0,
            "lambda_max_per_hour": 0.0,
            "capacity_orders_per_shift": 0.0,
        }
    bottleneck = max(eligible, key=lambda p: p.cycle_time_mean)
    lambda_max_per_second = target_rho * total_agents / bottleneck.cycle_time_mean
    shift_seconds = scenario.shift_hours * 3600.0
    return {
        "scenario_id": scenario.scenario_id,
        "target_rho": target_rho,
        "total_agents": total_agents,
        "bottleneck_agent_type": bottleneck.agent_type,
        "bottleneck_cycle_time_seconds": float(bottleneck.cycle_time_mean),
        "lambda_max_per_hour": float(lambda_max_per_second * 3600.0),
        "capacity_orders_per_shift": float(lambda_max_per_second * shift_seconds),
    }


def simulate_at_capacity(
    scenario: WarehouseScenario,
    target_rho: float = DEFAULT_CAPACITY_CEILING_RHO,
    n_runs: int = 5,
    run_id_offset: int = 1000,
) -> dict[str, Any]:
    """Run `scenario` at lambda_max(target_rho) to validate the closed-form ceiling.

    Closes F-044. Returns the dict from compute_capacity_ceiling plus the
    observed throughput moments across `n_runs` finite-horizon shifts at the
    stressed arrival rate. Validation is essential because the closed form
    assumes steady state; an 8-hour shift at rho = 0.85 still leaves orders
    in queue at end-of-shift, so observed_throughput_mean is typically a few
    percent below capacity_orders_per_shift.

    run_id_offset avoids seed collisions with the baseline `run_scenario`
    sweep — those use run_id in [0, n_runs), this uses [offset, offset+n_runs).
    """
    ceiling = compute_capacity_ceiling(scenario, target_rho=target_rho)
    if ceiling["total_agents"] == 0:
        return {
            **ceiling,
            "observed_throughput_mean": 0.0,
            "observed_throughput_std": 0.0,
            "n_runs_at_ceiling": 0,
        }
    stressed = WarehouseScenario(
        scenario_id=scenario.scenario_id,
        architecture=scenario.architecture,
        total_agents=scenario.total_agents,
        agent_profiles=scenario.agent_profiles,
        order_arrival_rate_per_hour=ceiling["lambda_max_per_hour"],
        shift_hours=scenario.shift_hours,
        seed=scenario.seed,
        metadata=dict(scenario.metadata) if scenario.metadata else {},
    )
    throughputs = [
        run_scenario(stressed, run_id=run_id_offset + i)["throughput_orders_per_shift"]
        for i in range(n_runs)
    ]
    arr = np.array(throughputs, dtype=float)
    return {
        **ceiling,
        "observed_throughput_mean": float(arr.mean()),
        "observed_throughput_std": float(arr.std(ddof=1)) if n_runs > 1 else 0.0,
        "n_runs_at_ceiling": n_runs,
    }


def _sample_service_time(rng: np.random.Generator, mean: float, std: float) -> float:
    """Draw one per-line service time from a lognormal preserving (mean, std).

    Industrial-IE standard for pick-time distributions is right-skewed (lognormal
    or Weibull); the previous naive ``rng.normal(...) clipped at 1.0`` folded the
    left tail into a point mass, biasing the empirical mean below the
    parameterised mean and inflating throughput. See ADR-0010 for derivation.

    Given target mean M and std S (CV = S/M), the underlying Normal parameters
    of ln(X) are ``sigma^2 = ln(1 + (S/M)^2)`` and ``mu = ln(M) - sigma^2 / 2``,
    which makes ``E[X] = M`` and ``Var[X] = S^2`` exactly.
    """
    if mean <= 0:
        return 1.0
    if std <= 0:
        return float(mean)
    cv2 = (std / mean) ** 2
    sigma2 = float(np.log1p(cv2))
    mu = float(np.log(mean)) - 0.5 * sigma2
    return float(rng.lognormal(mu, np.sqrt(sigma2)))


def run_scenario(scenario: WarehouseScenario, run_id: int = 0) -> dict[str, Any]:
    """Run one simulation episode for a given scenario.

    Returns a dict matching SimulationRunSchema fields. Refuses to run if the
    predicted M/G/c utilisation rho exceeds RHO_SATURATION_THRESHOLD — that
    regime has unbounded queue length under steady-state queueing theory and
    is not a meaningful operating point.
    """
    rho = predict_utilisation(scenario)
    if rho >= RHO_SATURATION_THRESHOLD:
        raise ValueError(
            f"Scenario {scenario.scenario_id!r} predicts rho = {rho:.3f} "
            f">= {RHO_SATURATION_THRESHOLD} — saturated M/G/c. "
            "Reduce order_arrival_rate_per_hour, increase agent count, or "
            "lower mean cycle time before re-running."
        )

    rng = np.random.default_rng(scenario.seed + run_id)
    env = simpy.Environment()

    completed_orders: list[float] = []
    queue_lengths: list[float] = []
    busy_time: dict[str, float] = {p.agent_type: 0.0 for p in scenario.agent_profiles}

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
            cycle_time = _sample_service_time(rng, profile.cycle_time_mean, profile.cycle_time_std)
            busy_time[profile.agent_type] += cycle_time
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

    utilizations: dict[str, float] = {}
    for profile in scenario.agent_profiles:
        key = f"utilization_{profile.agent_type}"
        total_capacity = profile.count * shift_seconds
        utilizations[key] = (
            busy_time[profile.agent_type] / total_capacity if total_capacity > 0 else 0.0
        )

    return {
        "scenario_id": scenario.scenario_id,
        "run_id": run_id,
        "throughput_orders_per_shift": float(throughput),
        "queue_length_mean": queue_mean,
        "rho_predicted": rho,
        "pipeline_version": "0.1.0",
        "seed": scenario.seed + run_id,
        **utilizations,
    }
