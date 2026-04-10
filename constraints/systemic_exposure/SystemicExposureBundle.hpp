#ifndef CURAFRAME_SYSTEMIC_EXPOSURE_BUNDLE_HPP
#define CURAFRAME_SYSTEMIC_EXPOSURE_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include "../../constraint_core/ConstraintRegistry.hpp"
#include <sstream>

class SystemicExposureBundle : public ConstraintBundle {
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
        double dose_proxy = 100.0; // Simulated dose proxy

        // Exposure window
        double exposure_window = dose_proxy / (logp + 1.0);
        if (exposure_window < 10.0) {
            penalties["narrow_exposure_window"] = 10.0 - exposure_window;
            narrative << "Therapeutic exposure window is perilously narrow. ";
        }

        // Distribution pressure
        double distribution_pressure = logp * 3.0;
        if (distribution_pressure > 12.0) {
            penalties["distribution_pressure"] = distribution_pressure - 12.0;
            narrative << "High distribution pressure indicating systemic sequestration. ";
        }

        // Cumulative toxicity
        double cumulative_tox = (distribution_pressure * 0.8) + (exposure_window * 0.2);
        if (cumulative_tox > 15.0) {
            penalties["cumulative_toxicity"] = cumulative_tox - 15.0;
            flags.push_back("SYSTEMIC_TOXICITY_ACCUMULATION");
            narrative << "Cumulative toxicity risks identified over repeated dosing. ";
        }

        // Systemic overload flags
        if (cumulative_tox > 20.0 || distribution_pressure > 18.0) {
            flags.push_back("SYSTEMIC_OVERLOAD");
            narrative << "Critical systemic overload thresholds breached. ";
        }

        if (narrative.str().empty()) {
            summary = "Systemic exposure parameters show stable pharmacokinetic distribution.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "SystemicExposure"}, {"version", "1.0"}, {"type", "pharmacokinetic"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

REGISTER_CONSTRAINT_BUNDLE("SystemicExposure", SystemicExposureBundle)

#endif // CURAFRAME_SYSTEMIC_EXPOSURE_BUNDLE_HPP
