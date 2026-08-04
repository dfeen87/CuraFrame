// Licensed under the PolyForm Noncommercial License 1.0.0
#ifndef CURAFRAME_SAFETY_BUNDLE_HPP
#define CURAFRAME_SAFETY_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class SafetyBundle : public ConstraintBundle {
private:
    std::map<std::string, double> penalties;
    std::vector<std::string> flags;
    std::string summary;

public:
    void evaluate(const Candidate& c) override {
        penalties.clear();
        flags.clear();
        std::ostringstream narrative;

        double logp = c.logp != 0 ? c.logp : 3.5;
        double mw = c.molecular_weight > 0 ? c.molecular_weight : 450.0;

        // Multi-organ stress proxy (aggregated proxy metric)
        double multi_organ_stress = (logp * 1.5) + (mw / 100.0);
        if (multi_organ_stress > 12.0) {
            penalties["multi_organ_stress"] = multi_organ_stress - 12.0;
            narrative << "Baseline parameters indicate diffuse multi-organ stress. ";
        }

        // Systemic penalties
        double systemic_penalty = multi_organ_stress * 1.2;
        if (systemic_penalty > 15.0) {
            penalties["global_systemic_toxicity"] = systemic_penalty - 15.0;
            narrative << "Global systemic toxicity thresholds breached. ";
        }

        // Aggregated risk flags
        if (multi_organ_stress > 18.0) {
            flags.push_back("CATASTROPHIC_SAFETY_FAILURE");
            narrative << "Catastrophic safety profile: multi-system failure expected. ";
        }

        if (narrative.str().empty()) {
            summary = "Global safety metrics fall within conservative operational bounds.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Safety"}, {"version", "1.0"}, {"type", "global"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_SAFETY_BUNDLE_HPP
