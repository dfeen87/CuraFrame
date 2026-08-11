// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#ifndef CURAFRAME_WEIGHTED_SCORING_ENGINE_HPP
#define CURAFRAME_WEIGHTED_SCORING_ENGINE_HPP

#include "../constraint_core/EvaluationReport.hpp"
#include "ScoringReport.hpp"
#include "WeightProfile.hpp"
#include <memory>
#include <string>

class WeightedScoringEngine {
public:
    WeightedScoringEngine(std::shared_ptr<WeightProfile> profile);

    // Ingest the evaluation report and produce a scoring report
    ScoringReport score(const EvaluationReport& eval_report) const;

private:
    std::shared_ptr<WeightProfile> profile_;

    std::string generate_narrative(const ScoringReport& report, const EvaluationReport& eval_report) const;
};

#endif // CURAFRAME_WEIGHTED_SCORING_ENGINE_HPP
