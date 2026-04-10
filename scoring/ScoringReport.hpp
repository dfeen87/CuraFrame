#ifndef CURAFRAME_SCORING_REPORT_HPP
#define CURAFRAME_SCORING_REPORT_HPP

#include <string>
#include <vector>
#include <map>

struct ScoringReport {
    double composite_score = 0.0; // 0 to 100

    // Per-bundle weighted contributions
    std::map<std::string, double> bundle_contributions;

    // Breakdowns
    std::map<std::string, double> penalty_breakdown;
    std::map<std::string, double> bonus_breakdown;

    // Falsification
    std::vector<std::string> falsification_flags;
    double falsification_impact = 0.0;

    // Metadata
    std::string weight_profile_name;

    // Narrative summary
    std::string narrative_summary;
};

#endif // CURAFRAME_SCORING_REPORT_HPP
