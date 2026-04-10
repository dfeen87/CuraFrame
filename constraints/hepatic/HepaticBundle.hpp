#ifndef CURAFRAME_HEPATIC_BUNDLE_HPP
#define CURAFRAME_HEPATIC_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class HepaticBundle : public ConstraintBundle {
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

        // Enzyme saturation
        double enzyme_saturation = (logp * 1.5) + (mw * 0.005);
        if (enzyme_saturation > 8.0) {
            penalties["enzyme_saturation"] = enzyme_saturation - 8.0;
            narrative << "Hepatic enzyme pathways approaching saturation. ";
        }

        // Hepatotoxicity heuristics
        double hepatotox_risk = (logp > 4.5 && mw > 400.0) ? 6.0 : 1.0;
        if (hepatotox_risk > 4.0) {
            penalties["hepatotoxicity_risk"] = hepatotox_risk;
            flags.push_back("HEPATOTOXICITY_ALERT");
            narrative << "Significant hepatotoxicity structural alerts detected. ";
        }

        // Bile-clearance pressure
        double bile_clearance = mw * 0.02;
        if (bile_clearance > 12.0) {
            penalties["bile_clearance_pressure"] = bile_clearance - 12.0;
            flags.push_back("BILIARY_OBSTRUCTION_RISK");
            narrative << "High molecular weight poses biliary clearance obstruction risks. ";
        }

        if (narrative.str().empty()) {
            summary = "Hepatic processing parameters are within safe physiological limits.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Hepatic"}, {"version", "1.0"}, {"type", "organ_specific"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_HEPATIC_BUNDLE_HPP
