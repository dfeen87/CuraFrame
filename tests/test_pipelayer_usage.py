# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
"""
Verification script for Pipelayer Domain.
"""

from pipelayer import (
    PipelayerGovernor,
    PipelayerSignals,
    MachineTelemetry,
    SiteConditions,
    OperationMode,
    PipeType,
    MachineModel,
)

def test_pipelayer_usage():
    print("Testing Pipelayer Domain usage...")

    # 1. Create Governor
    governor = PipelayerGovernor()
    print("Governor created.")

    # 2. Create sample signals
    signals = PipelayerSignals(
        operation_trust_score=0.9,
        measurement_reliability=0.95,
        machine_telemetry=MachineTelemetry(
            load_kg=15000.0,
            boom_angle_deg=45.0,
            counterweight_position_pct=80.0,
            engine_rpm=2200.0,
            engine_temp_c=90.0,
            hydraulic_pressure_bar=150.0,
            tipping_moment_pct=60.0,
            load_moment_pct=70.0,
        ),
        site_conditions=SiteConditions(
            wind_speed_kmh=15.0,
            ambient_temp_c=25.0,
            visibility_m=1000.0,
            ground_slope_pitch_deg=2.0,
            ground_slope_roll_deg=1.0,
            soil_stability_index=0.9,
        ),
        operation_mode=OperationMode.LIFTING,
        machine_model=MachineModel.CATERPILLAR_587T,
        pipe_type=PipeType.STEEL_36_INCH,
    )
    print("Signals created.")

    # 3. Evaluate
    result = governor.evaluate(signals)
    print("Evaluation result:", result)

    assert result.operation_authorized is True
    assert result.authority_level.name == "FULL_CAPACITY" or result.authority_level.name == "NORMAL_OPERATION"

    print("\n--- TEST PASSED: Safe Operation ---")

    # 4. Create UNSAFE signals
    unsafe_signals = PipelayerSignals(
        operation_trust_score=0.5,
        measurement_reliability=0.6,
        machine_telemetry=MachineTelemetry(
            load_kg=25000.0,
            boom_angle_deg=15.0,
            counterweight_position_pct=100.0,
            engine_rpm=2500.0,
            engine_temp_c=115.0, # Overheat
            hydraulic_pressure_bar=90.0, # Low pressure
            tipping_moment_pct=96.0, # Critical tipping
            load_moment_pct=105.0, # Overload
        ),
        site_conditions=SiteConditions(
            wind_speed_kmh=65.0, # High wind
            ambient_temp_c=35.0,
            visibility_m=200.0,
            ground_slope_pitch_deg=5.0,
            ground_slope_roll_deg=20.0, # Excessive slope
            soil_stability_index=0.3, # Unstable soil
        ),
        operation_mode=OperationMode.LIFTING,
        machine_model=MachineModel.CATERPILLAR_587T,
        pipe_type=PipeType.STEEL_36_INCH,
    )

    unsafe_result = governor.evaluate(unsafe_signals)
    print("Unsafe Evaluation result:", unsafe_result)

    assert unsafe_result.operation_authorized is False
    assert unsafe_result.authority_level.name == "SHUTDOWN"

    print("\n--- TEST PASSED: Unsafe Operation ---")


def test_pipelayer_restricted_operation():
    """
    Governor authorises operation at RESTRICTED_OPERATION when machine telemetry is
    healthy but an environmental issue (wind speed exceeding the lifting threshold)
    is detected.  The AILEE pipeline promotes the adjusted trust score via its grace
    mechanism, yielding a SAFE verdict; the presence of a precautionary flag then
    selects RESTRICTED_OPERATION rather than FULL_CAPACITY.
    """
    governor = PipelayerGovernor()

    # Wind at 50 km/h exceeds the 40 km/h LIFTING limit → unsafe_environment flag.
    # Machine telemetry is fully healthy so no critical_machine_status flag.
    # trust=0.95 → adjusted after 0.12 penalty → 0.836 (in grace window) → SAFE.
    restricted_signals = PipelayerSignals(
        operation_trust_score=0.95,
        measurement_reliability=0.95,
        machine_telemetry=MachineTelemetry(
            load_kg=10000.0,
            boom_angle_deg=45.0,
            counterweight_position_pct=75.0,
            engine_rpm=2000.0,
            engine_temp_c=85.0,
            hydraulic_pressure_bar=150.0,
            tipping_moment_pct=50.0,
            load_moment_pct=60.0,
        ),
        site_conditions=SiteConditions(
            wind_speed_kmh=50.0,   # > 40 km/h for LIFTING → unsafe_environment
            ambient_temp_c=25.0,
            visibility_m=1000.0,
            ground_slope_pitch_deg=2.0,
            ground_slope_roll_deg=1.0,
            soil_stability_index=0.9,
        ),
        operation_mode=OperationMode.LIFTING,
        machine_model=MachineModel.CATERPILLAR_587T,
        pipe_type=PipeType.STEEL_36_INCH,
    )

    result = governor.evaluate(restricted_signals)
    print("Restricted Evaluation result:", result)

    assert result.operation_authorized is True
    assert result.authority_level.name == "RESTRICTED_OPERATION"
    assert "unsafe_environment" in (result.precautionary_flags or [])

    print("\n--- TEST PASSED: Restricted Operation ---")


if __name__ == "__main__":
    test_pipelayer_usage()
    test_pipelayer_restricted_operation()
