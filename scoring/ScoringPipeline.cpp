// Licensed under the PolyForm Noncommercial License 1.0.0
#include "ScoringPipeline.hpp"

ScoringPipeline::ScoringPipeline(std::shared_ptr<WeightProfile> profile)
    : engine_(std::move(profile)) {}

ScoringReport ScoringPipeline::execute(const EvaluationReport& eval_report) const {
    // In a more complex pipeline, normalization or pre-processing could happen here
    // Currently, the WeightedScoringEngine handles everything deterministically
    return engine_.score(eval_report);
}
