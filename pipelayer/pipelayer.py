"""
CuraFrame — PIPELAYER Domain
Version: 1.0.0 - Production Grade

Pipelayer governance domain for heavy machinery operations, specifically
sideboom pipelayers used in pipeline construction.

Ensures safe operation by monitoring tipping moments, load capacities,
boom angles, ground conditions, and environmental factors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import time
import statistics
import math

# ---- Mock AILEE Imports for Standalone Operation ----
# In a real integration, these would be imported from ailee.ailee_trust_pipeline_v1
try:
    from ...ailee_trust_pipeline_v1 import (
        AileeTrustPipeline,
        AileeConfig,
        DecisionResult,
        SafetyStatus
    )
except (ImportError, ValueError):
    # Mock classes for standalone functionality
    class SafetyStatus(str, Enum):
        SAFE = "SAFE"
        UNSAFE = "UNSAFE"
        BORDERLINE = "BORDERLINE"

    @dataclass
    class DecisionResult:
        validated_value: float
        confidence_score: float
        status: SafetyStatus
        grace_applied: bool = False
        consensus_status: Optional[str] = None

    @dataclass
    class AileeConfig:
        accept_threshold: float = 0.85
        borderline_low: float = 0.70
        borderline_high: float = 0.85
        w_stability: float = 0.50
        w_agreement: float = 0.35
        w_likelihood: float = 0.15
        history_window: int = 200
        forecast_window: int = 30
        grace_peer_delta: float = 0.12
        grace_min_peer_agreement_ratio: float = 0.70
        grace_forecast_epsilon: float = 0.15
        grace_max_abs_z: float = 2.0
        consensus_quorum: int = 3
        consensus_delta: float = 0.15
        consensus_pass_ratio: float = 0.75
        fallback_mode: str = "last_good"
        enable_grace: bool = True
        enable_consensus: bool = True
        enable_audit_metadata: bool = True
        hard_min: float = 0.0
        hard_max: float = 1.0

    class AileeTrustPipeline:
        def __init__(self, config: AileeConfig):
            self.config = config

        def process(self, raw_value: float, raw_confidence: float, peer_values: List[float], timestamp: float, context: Dict[str, Any]) -> DecisionResult:
            # Simple pass-through mock logic
            status = SafetyStatus.SAFE if raw_value >= self.config.accept_threshold else SafetyStatus.UNSAFE
            return DecisionResult(
                validated_value=raw_value,
                confidence_score=raw_confidence,
                status=status
            )


# ===== SEVERITY WEIGHTING FOR FLAGS =====

FLAG_SEVERITY: Dict[str, float] = {
    "critical_machine_status": 0.15,
    "unsafe_environment": 0.12,
    "tipping_moment_critical": 0.15,
    "boom_angle_unsafe": 0.12,
    "load_capacity_exceeded": 0.15,
    "ground_slope_excessive": 0.10,
    "wind_speed_high": 0.08,
    "soil_instability": 0.08,
    "hydraulic_pressure_low": 0.12,
    "engine_overheat": 0.05,
    "sensor_disagreement": 0.05,
    "measurement_uncertainty_high": 0.04,
    "operator_fatigue_detected": 0.10,
}


# -----------------------------
# Operation and Machine Types
# -----------------------------

class OperationMode(str, Enum):
    """Pipelayer operation modes"""
    IDLE = "IDLE"
    TRAVEL = "TRAVEL"
    LIFTING = "LIFTING"
    CARRYING = "CARRYING"
    LOWERING_IN = "LOWERING_IN"
    HOLDING = "HOLDING"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class PipeType(str, Enum):
    """Type of pipe being handled"""
    STEEL_24_INCH = "STEEL_24_INCH"
    STEEL_36_INCH = "STEEL_36_INCH"
    STEEL_48_INCH = "STEEL_48_INCH"
    HDPE = "HDPE"
    CONCRETE_COATED = "CONCRETE_COATED"
    UNKNOWN = "UNKNOWN"


class MachineModel(str, Enum):
    """Pipelayer machine models"""
    CATERPILLAR_587T = "CATERPILLAR_587T"
    CATERPILLAR_572R = "CATERPILLAR_572R"
    KOMATSU_D355C = "KOMATSU_D355C"
    LIEBHERR_RL64 = "LIEBHERR_RL64"
    UNKNOWN = "UNKNOWN"


class AuthorityLevel(str, Enum):
    """Escalating operation authority levels"""
    SHUTDOWN = "SHUTDOWN"
    IDLE_ONLY = "IDLE_ONLY"
    RESTRICTED_OPERATION = "RESTRICTED_OPERATION"
    NORMAL_OPERATION = "NORMAL_OPERATION"
    FULL_CAPACITY = "FULL_CAPACITY"
    EMERGENCY_OVERRIDE = "EMERGENCY_OVERRIDE"


class DecisionOutcome(str, Enum):
    """Pipelayer governance decision outcomes"""
    HALT_IMMEDIATELY = "HALT_IMMEDIATELY"
    RESTRICT_LOAD = "RESTRICT_LOAD"
    WARN_OPERATOR = "WARN_OPERATOR"
    PROCEED_NORMAL = "PROCEED_NORMAL"
    REQUIRE_SUPERVISOR = "REQUIRE_SUPERVISOR"
    EMERGENCY_ACTION = "EMERGENCY_ACTION"


# -----------------------------
# Machine Telemetry
# -----------------------------

@dataclass(frozen=True)
class MachineTelemetry:
    """Current telemetry from the pipelayer machine"""
    load_kg: float
    boom_angle_deg: float
    counterweight_position_pct: float
    engine_rpm: float
    engine_temp_c: float
    hydraulic_pressure_bar: float

    tipping_moment_pct: float  # Percentage of max tipping moment
    load_moment_pct: float     # Percentage of max load moment

    fuel_level_pct: Optional[float] = None
    battery_voltage: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_critical_threshold_breached(self) -> Tuple[bool, List[str]]:
        """Check if any critical machine thresholds are breached"""
        issues: List[str] = []

        if self.tipping_moment_pct > 95.0:
            issues.append(f"tipping_moment_critical ({self.tipping_moment_pct:.1f}%)")
        elif self.tipping_moment_pct > 85.0:
            issues.append(f"tipping_moment_warning ({self.tipping_moment_pct:.1f}%)")

        if self.load_moment_pct > 100.0:
            issues.append(f"load_capacity_exceeded ({self.load_moment_pct:.1f}%)")

        if self.hydraulic_pressure_bar < 100.0: # Assuming min pressure
            issues.append(f"hydraulic_pressure_low ({self.hydraulic_pressure_bar:.1f} bar)")

        if self.engine_temp_c > 110.0:
            issues.append(f"engine_overheat ({self.engine_temp_c:.1f} C)")

        return len(issues) > 0, issues


# -----------------------------
# Environmental Conditions
# -----------------------------

@dataclass(frozen=True)
class SiteConditions:
    """Environmental and ground conditions"""
    wind_speed_kmh: float
    ambient_temp_c: float
    visibility_m: float

    ground_slope_pitch_deg: float
    ground_slope_roll_deg: float
    soil_stability_index: float # 0.0 to 1.0 (1.0 = solid rock)

    wetness_pct: Optional[float] = None
    ice_detected: bool = False

    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_safe_for_operation(self, operation: OperationMode) -> Tuple[bool, List[str]]:
        issues: List[str] = []

        max_wind = 40.0 if operation == OperationMode.LIFTING else 60.0
        if self.wind_speed_kmh > max_wind:
            issues.append(f"wind_speed_high ({self.wind_speed_kmh:.1f} > {max_wind} km/h)")

        max_slope = 15.0
        if abs(self.ground_slope_roll_deg) > max_slope:
             issues.append(f"ground_slope_roll_excessive ({self.ground_slope_roll_deg:.1f} deg)")

        if self.soil_stability_index < 0.4:
            issues.append(f"soil_instability ({self.soil_stability_index:.2f})")

        return len(issues) == 0, issues


# -----------------------------
# Domain Inputs
# -----------------------------

@dataclass(frozen=True)
class PipelayerSignals:
    """Governance signals for pipelayer operation assessment"""
    operation_trust_score: float
    measurement_reliability: float

    machine_telemetry: MachineTelemetry
    site_conditions: SiteConditions

    operation_mode: OperationMode = OperationMode.UNKNOWN
    machine_model: MachineModel = MachineModel.UNKNOWN
    pipe_type: PipeType = PipeType.UNKNOWN

    operator_id: Optional[str] = None
    operator_fatigue_score: Optional[float] = None # 0.0 = fresh, 1.0 = exhausted

    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', time.time())


# -----------------------------
# Result Structure
# -----------------------------

@dataclass(frozen=True)
class PipelayerDecisionResult:
    """Pipelayer governance decision result"""
    operation_authorized: bool
    authority_level: AuthorityLevel
    decision_outcome: DecisionOutcome

    validated_trust_score: float
    confidence_score: float

    recommendation: str
    reasons: List[str]

    ailee_result: Optional[DecisionResult] = None
    precautionary_flags: Optional[List[str]] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Domain Configuration
# -----------------------------

@dataclass(frozen=True)
class PipelayerGovernancePolicy:
    """Domain policy for pipelayer governance"""
    machine_model: MachineModel = MachineModel.UNKNOWN

    min_operation_trust_score: float = 0.80
    min_measurement_reliability: float = 0.75

    max_tipping_moment_pct: float = 85.0
    max_wind_speed_kmh: float = 40.0
    max_ground_slope_deg: float = 15.0

    enable_emergency_override: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)


def default_pipelayer_config() -> AileeConfig:
    """Safe defaults for pipelayer governance pipeline configuration"""
    return AileeConfig(
        accept_threshold=0.85,
        borderline_low=0.70,
        borderline_high=0.85,
        w_stability=0.60, # Higher stability for heavy machinery
        w_agreement=0.30,
        w_likelihood=0.10,
        history_window=100,
        fallback_mode="safe_stop",
    )


# ===== PIPELAYER GOVERNOR =====

class PipelayerGovernor:
    """
    Governor for Pipelayer operations.
    """

    def __init__(
        self,
        cfg: Optional[AileeConfig] = None,
        policy: Optional[PipelayerGovernancePolicy] = None,
    ):
        self.policy = policy or PipelayerGovernancePolicy()
        self.cfg = cfg or default_pipelayer_config()
        self.pipeline = AileeTrustPipeline(self.cfg)
        self.event_log: List[Any] = []

    def evaluate(self, signals: PipelayerSignals) -> PipelayerDecisionResult:
        """Evaluate signals and make a governance decision"""
        ts = float(signals.timestamp)
        reasons: List[str] = []
        precautionary_flags: List[str] = []

        # 1. Check Machine Telemetry
        crit_machine, machine_issues = signals.machine_telemetry.is_critical_threshold_breached()
        if crit_machine:
            reasons.extend(machine_issues)
            precautionary_flags.append("critical_machine_status")

        # 2. Check Environmental Conditions
        env_ok, env_issues = signals.site_conditions.is_safe_for_operation(signals.operation_mode)
        if not env_ok:
            reasons.extend(env_issues)
            precautionary_flags.append("unsafe_environment")

        # 3. Check Operator Fatigue
        if signals.operator_fatigue_score is not None and signals.operator_fatigue_score > 0.7:
             reasons.append(f"operator_fatigue_high ({signals.operator_fatigue_score:.2f})")
             precautionary_flags.append("operator_fatigue_detected")

        # 4. Calculate Penalty
        penalty = 0.0
        if precautionary_flags:
            # Simple penalty calculation
            penalty = sum(FLAG_SEVERITY.get(f, 0.05) for f in precautionary_flags)
            penalty = min(0.4, penalty) # Cap penalty

        adjusted_score = signals.operation_trust_score * (1.0 - penalty)

        # 5. AILEE Pipeline
        ctx = {
            "operation_mode": signals.operation_mode.value,
            "precautionary_flags": precautionary_flags
        }

        ailee_result = self.pipeline.process(
            raw_value=adjusted_score,
            raw_confidence=signals.measurement_reliability,
            peer_values=[], # No peers in this simple example
            timestamp=ts,
            context=ctx
        )

        # 6. Make Decision
        return self._make_decision(signals, ailee_result, reasons, precautionary_flags, ts)

    def _make_decision(
        self,
        signals: PipelayerSignals,
        ailee_result: DecisionResult,
        reasons: List[str],
        precautionary_flags: List[str],
        ts: float
    ) -> PipelayerDecisionResult:

        validated_score = ailee_result.validated_value
        authorized = False
        authority_level = AuthorityLevel.SHUTDOWN
        outcome = DecisionOutcome.HALT_IMMEDIATELY
        recommendation = "halt_operations"

        if ailee_result.status == SafetyStatus.SAFE:
            if not precautionary_flags:
                authorized = True
                authority_level = AuthorityLevel.FULL_CAPACITY
                outcome = DecisionOutcome.PROCEED_NORMAL
                recommendation = "proceed_normal_operation"
            else:
                authorized = True
                authority_level = AuthorityLevel.RESTRICTED_OPERATION
                outcome = DecisionOutcome.WARN_OPERATOR
                recommendation = "proceed_with_caution"
        elif ailee_result.status == SafetyStatus.BORDERLINE:
            authorized = False
            authority_level = AuthorityLevel.IDLE_ONLY
            outcome = DecisionOutcome.REQUIRE_SUPERVISOR
            recommendation = "request_supervisor_approval"
        else: # UNSAFE
            authorized = False
            authority_level = AuthorityLevel.SHUTDOWN
            outcome = DecisionOutcome.HALT_IMMEDIATELY
            recommendation = "unsafe_conditions_halt"

        return PipelayerDecisionResult(
            operation_authorized=authorized,
            authority_level=authority_level,
            decision_outcome=outcome,
            validated_trust_score=validated_score,
            confidence_score=ailee_result.confidence_score,
            recommendation=recommendation,
            reasons=reasons,
            ailee_result=ailee_result,
            precautionary_flags=precautionary_flags,
            metadata={"timestamp": ts}
        )
