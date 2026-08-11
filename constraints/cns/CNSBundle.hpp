// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#ifndef CURAFRAME_CNS_BUNDLE_HPP
#define CURAFRAME_CNS_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class CNSBundle : public ConstraintBundle {
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

        // BBB penetration heuristic
        double bbb_penetration = (logp > 2.0 && mw < 500.0) ? (logp * 2.0) : (logp * 0.5);
        if (bbb_penetration > 8.0) {
            penalties["bbb_hyper_penetration"] = bbb_penetration - 8.0;
            narrative << "Excessive Blood-Brain Barrier (BBB) penetration detected. ";
        }

        // Neuro-instability
        double neuro_instability = (bbb_penetration > 10.0) ? 6.0 : 1.0;
        if (neuro_instability > 4.0) {
            penalties["neuro_instability"] = neuro_instability;
            flags.push_back("NEURO_INSTABILITY_ALERT");
            narrative << "High neuro-instability risks linked to over-exposure. ";
        }

        // Excitotoxicity flags
        double excitotox = (logp * 1.5) + (mw * 0.01);
        if (excitotox > 12.0) {
            penalties["excitotoxicity"] = excitotox - 12.0;
            flags.push_back("EXCITOTOXICITY_RISK");
            narrative << "Receptor overstimulation thresholds suggest excitotoxicity. ";
        }

        if (narrative.str().empty()) {
            summary = "Central Nervous System safety profile is benign.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "CNS"}, {"version", "1.0"}, {"type", "organ_specific"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_CNS_BUNDLE_HPP
