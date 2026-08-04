// Licensed under the PolyForm Noncommercial License 1.0.0
#ifndef CURAFRAME_EVALUATION_REPORT_HPP
#define CURAFRAME_EVALUATION_REPORT_HPP

#include <string>
#include <vector>
#include <map>

// Unified structured output for multi-bundle evaluation
struct EvaluationReport {
    std::string candidate_id;

    // Aggregated penalty signals mapped by domain
    std::map<std::string, std::map<std::string, double>> domain_penalty_signals;

    // Aggregated falsification flags
    std::vector<std::string> falsification_flags;

    // Aggregated narrative summaries
    std::string combined_narrative;

    bool is_viable() const {
        return falsification_flags.empty();
    }
};

#endif // CURAFRAME_EVALUATION_REPORT_HPP
