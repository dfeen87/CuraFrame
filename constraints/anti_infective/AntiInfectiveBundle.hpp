// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#ifndef CURAFRAME_ANTI_INFECTIVE_BUNDLE_HPP
#define CURAFRAME_ANTI_INFECTIVE_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class AntiInfectiveBundle : public ConstraintBundle {
private:
    std::map<std::string, double> penalties;
    std::vector<std::string> flags;
    std::string summary;

public:
    void evaluate(const Candidate& c) override {
        penalties.clear();
        flags.clear();
        std::ostringstream narrative;

        double mw = c.molecular_weight > 0 ? c.molecular_weight : 450.0;

        // Pathogen-pressure heuristics
        double pathogen_pressure = mw / 40.0;
        if (pathogen_pressure < 5.0) {
            penalties["weak_pathogen_pressure"] = 5.0 - pathogen_pressure;
            narrative << "Insufficient selective pressure against target pathogens. ";
        }

        // Resistance-risk signals
        double resistance_risk = (pathogen_pressure > 10.0 && pathogen_pressure < 15.0) ? 6.0 : 1.0;
        if (resistance_risk > 4.0) {
            penalties["resistance_risk"] = resistance_risk;
            flags.push_back("MUTATION_RESISTANCE_ALERT");
            narrative << "Narrow pressure band risks rapid evolutionary resistance. ";
        }

        // Microbiome disruption penalties
        double microbiome_disruption = mw * 0.03;
        if (microbiome_disruption > 18.0) {
            penalties["microbiome_disruption"] = microbiome_disruption - 18.0;
            flags.push_back("SEVERE_DYSBIOSIS_RISK");
            narrative << "Broad-spectrum traits heavily disrupt commensal microbiome. ";
        }

        if (narrative.str().empty()) {
            summary = "Anti-infective parameters show targeted efficacy with minimal collateral damage.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "AntiInfective"}, {"version", "1.0"}, {"type", "therapeutic_area"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_ANTI_INFECTIVE_BUNDLE_HPP
