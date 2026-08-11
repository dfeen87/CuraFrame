// Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
#ifndef CURAFRAME_PKPD_BUNDLE_HPP
#define CURAFRAME_PKPD_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class PKPDBundle : public ConstraintBundle {
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
        double clearance_rate = 50.0 / (logp + 1.0); // Simulated clearance

        // Dose-response curves
        double dose_escalation_risk = 10.0 / (clearance_rate + 0.1);
        if (dose_escalation_risk > 5.0) {
            penalties["steep_dose_response"] = dose_escalation_risk - 5.0;
            narrative << "Steep dose-response curve suggests narrow efficacy band. ";
        }

        // Saturation thresholds
        double pd_saturation = logp * 2.5;
        if (pd_saturation > 12.0) {
            penalties["receptor_saturation"] = pd_saturation - 12.0;
            narrative << "Receptor saturation occurs well below maximal efficacy. ";
        }

        // Effect-window alignment
        double effect_window = clearance_rate * 2.0;
        if (effect_window < 10.0) {
            penalties["misaligned_effect_window"] = 10.0 - effect_window;
            flags.push_back("PKPD_DECOUPLING");
            narrative << "PK profile drastically decoupled from PD required effect window. ";
        }

        if (narrative.str().empty()) {
            summary = "Pharmacokinetic and pharmacodynamic profiles are tightly coupled and predictable.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "PKPD"}, {"version", "1.0"}, {"type", "pharmacology"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_PKPD_BUNDLE_HPP
