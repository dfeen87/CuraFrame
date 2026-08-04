// Licensed under the PolyForm Noncommercial License 1.0.0
#ifndef CURAFRAME_CARDIAC_BUNDLE_HPP
#define CURAFRAME_CARDIAC_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class CardiacBundle : public ConstraintBundle {
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

        // QT-risk heuristics
        double qt_risk = (logp * 1.2) + (mw * 0.005);
        if (qt_risk > 7.0) {
            penalties["qt_prolongation_risk"] = qt_risk - 7.0;
            narrative << "hERG binding proxy indicates QT-prolongation risk. ";
        }

        // Conduction-instability signals
        double conduction_instability = (qt_risk > 9.0) ? 5.0 : 1.0;
        if (conduction_instability > 3.0) {
            penalties["conduction_instability"] = conduction_instability;
            flags.push_back("CARDIAC_CONDUCTION_ALERT");
            narrative << "Severe conduction instability signals detected. ";
        }

        // Perfusion-pressure penalties
        double perfusion_pressure = logp * 2.5;
        if (perfusion_pressure > 15.0) {
            penalties["perfusion_pressure"] = perfusion_pressure - 15.0;
            flags.push_back("ISCHEMIC_RISK");
            narrative << "Elevated perfusion pressure raises ischemic risk profile. ";
        }

        if (narrative.str().empty()) {
            summary = "Cardiac electrical and mechanical constraints satisfied.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Cardiac"}, {"version", "1.0"}, {"type", "organ_specific"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_CARDIAC_BUNDLE_HPP
