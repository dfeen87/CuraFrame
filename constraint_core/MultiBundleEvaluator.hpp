#ifndef CURAFRAME_MULTI_BUNDLE_EVALUATOR_HPP
#define CURAFRAME_MULTI_BUNDLE_EVALUATOR_HPP

#include "Candidate.hpp"
#include "EvaluationReport.hpp"
#include "ConstraintRegistry.hpp"
#include <sstream>

// Unified Evaluation Layer
class MultiBundleEvaluator {
public:
    EvaluationReport evaluate(const Candidate& candidate) {
        EvaluationReport report;
        report.candidate_id = candidate.id;

        auto bundles = ConstraintRegistry::instance().create_all_bundles();
        std::ostringstream combined_narrative;

        for (const auto& pair : bundles) {
            const std::string& domain_name = pair.first;
            auto& bundle = pair.second;

            bundle->evaluate(candidate);

            // Collect metadata if needed (for later extension)
            auto metadata = bundle->bundle_metadata();

            // Collect penalty signals
            report.domain_penalty_signals[domain_name] = bundle->penalty_signals();

            // Collect falsification flags
            auto flags = bundle->falsification_flags();
            report.falsification_flags.insert(
                report.falsification_flags.end(),
                flags.begin(),
                flags.end()
            );

            // Collect narrative summary
            std::string summary = bundle->narrative_summary();
            if (!summary.empty()) {
                combined_narrative << "[" << domain_name << "] " << summary << "\n";
            }
        }

        report.combined_narrative = combined_narrative.str();
        return report;
    }
};

#endif // CURAFRAME_MULTI_BUNDLE_EVALUATOR_HPP
