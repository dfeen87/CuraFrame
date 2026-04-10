#ifndef CURAFRAME_RENAL_BUNDLE_HPP
#define CURAFRAME_RENAL_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include <sstream>

class RenalBundle : public ConstraintBundle {
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

        // Filtration pressure
        double filtration_pressure = mw / 50.0; // simplistic heuristic
        if (filtration_pressure > 15.0) {
            penalties["filtration_pressure"] = filtration_pressure - 15.0;
            narrative << "Glomerular filtration pressure elevated due to size. ";
        }

        // Nephrotoxicity heuristics
        double nephrotox_risk = (logp < 1.0 && mw > 300.0) ? 5.0 : 0.5;
        if (nephrotox_risk > 3.0) {
            penalties["nephrotoxicity_risk"] = nephrotox_risk;
            flags.push_back("NEPHROTOXICITY_ALERT");
            narrative << "Hydrophilic properties suggest tubular concentration risks. ";
        }

        // Solute-load thresholds
        double solute_load = (mw * 0.01) + (5.0 - logp); // Lower logp = higher renal load
        if (solute_load > 10.0) {
            penalties["solute_load"] = solute_load - 10.0;
            flags.push_back("RENAL_SOLUTE_OVERLOAD");
            narrative << "Renal solute load threshold exceeded, risking acute injury. ";
        }

        if (narrative.str().empty()) {
            summary = "Renal clearance parameters suggest normal functioning.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Renal"}, {"version", "1.0"}, {"type", "organ_specific"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

#endif // CURAFRAME_RENAL_BUNDLE_HPP
