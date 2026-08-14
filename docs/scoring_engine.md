# CuraFrame Weighted Multi-Constraint Scoring Engine (v5.0.0)

## Overview

The Weighted Multi-Constraint Scoring Engine is a subsystem added in v5.0.0 that sits above the existing constraint bundles.

This system does not alter or modify the underlying deterministic bundle evaluation logic. Instead, it aggregates results and applies domain-specific weighting, penalties, and bonuses to produce a nuanced report of therapeutic candidate viability.

## Architecture

1. **WeightProfile (`scoring/WeightProfile.hpp`)**: An interface (with default implementations) that defines the weights, penalties, multipliers, and scaling factors for different domains and specific signals.
2. **WeightedScoringEngine (`scoring/WeightedScoringEngine.hpp/.cpp`)**: The core engine that ingests the outputs from all bundles (`EvaluationReport`), applies the provided `WeightProfile`, computes the final score, and generates a structured summary.
3. **ScoringPipeline (`scoring/ScoringPipeline.hpp/.cpp`)**: A wrapper pipeline managing the execution of the scoring engine with a specified weight profile.
4. **ScoringReport (`scoring/ScoringReport.hpp`)**: The structured output structure, detailing penalty breakdowns, bonus breakdowns, falsification impacts, and a narrative summary.

## Composite Stability Score

The Composite Stability Score is a numerical representation of candidate stability scaled between 0 and 100:
- **100**: Perfect theoretical safety baseline, zero constraint violations or penalized signals.
- **< 100**: Progressive deterioration of the score based on domain-weighted penalties, amplified by specific severity levels, or falsification flags.
- **Falsification impact**: Candidate falsification triggers massive penalty deductions (configurable per weight profile), severely lowering the final score.

Higher scores indicate more stable candidates, and lower scores indicate more risk-burdened candidates.

## Example Report Execution

```cpp
MultiBundleEvaluator evaluator;
EvaluationReport eval_report = evaluator.evaluate(candidate);

// Generate standard composite scoring
ScoringReport score = evaluator.score(eval_report);

// Generate with an aggressive safety profile
ScoringReport safety_score = evaluator.score_with_profile(eval_report, std::make_shared<HighSafetyProfile>());
```
