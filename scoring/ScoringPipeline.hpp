// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#ifndef CURAFRAME_SCORING_PIPELINE_HPP
#define CURAFRAME_SCORING_PIPELINE_HPP

#include "../constraint_core/EvaluationReport.hpp"
#include "ScoringReport.hpp"
#include "WeightedScoringEngine.hpp"
#include "WeightProfile.hpp"
#include <memory>

class ScoringPipeline {
public:
    ScoringPipeline(std::shared_ptr<WeightProfile> profile);

    ScoringReport execute(const EvaluationReport& eval_report) const;

private:
    WeightedScoringEngine engine_;
};

#endif // CURAFRAME_SCORING_PIPELINE_HPP
