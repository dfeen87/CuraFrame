#ifndef CURAFRAME_ONCOLOGY_BUNDLE_HPP
#define CURAFRAME_ONCOLOGY_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class OncologyBundle : public ConstraintBundle {
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
        double dose_intensity = 150.0; // Proxy

        // Proliferative-pressure
        double proliferative_pressure = dose_intensity / (logp + 1.0);
        if (proliferative_pressure < 20.0) {
            penalties["sub_lethal_proliferative_pressure"] = 20.0 - proliferative_pressure;
            narrative << "Sub-lethal pressure fails to halt cellular proliferation. ";
        }

        // Off-target cytotoxicity
        double off_target_tox = (logp * 4.0);
        if (off_target_tox > 15.0) {
            penalties["off_target_cytotoxicity"] = off_target_tox - 15.0;
            flags.push_back("SYSTEMIC_CYTOTOXICITY_ALERT");
            narrative << "High lipophilicity drives dangerous off-target cytotoxicity. ";
        }

        // Therapeutic window alignment
        double window_alignment = off_target_tox / (proliferative_pressure + 0.1);
        if (window_alignment > 1.0) {
            penalties["inverted_therapeutic_window"] = window_alignment;
            flags.push_back("THERAPEUTIC_WINDOW_VIOLATION");
            narrative << "Therapeutic window inverted: toxicity outpaces efficacy. ";
        }

        if (narrative.str().empty()) {
            summary = "Oncology metrics demonstrate aligned anti-proliferative targeting.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Oncology"}, {"version", "1.0"}, {"type", "therapeutic_area"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_ONCOLOGY_BUNDLE_HPP
