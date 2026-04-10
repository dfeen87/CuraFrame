#ifndef CURAFRAME_FORMULATION_BUNDLE_HPP
#define CURAFRAME_FORMULATION_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include "../../constraint_core/ConstraintRegistry.hpp"
#include <sstream>

class FormulationBundle : public ConstraintBundle {
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

        // Solubility limits (high logP or high MW = low solubility)
        double insolubility = (logp * 2.0) + (mw / 100.0);
        if (insolubility > 10.0) {
            penalties["solubility_deficit"] = insolubility - 10.0;
            narrative << "Aqueous solubility falls below required delivery thresholds. ";
        }

        // Stability penalties
        double instability = (mw > 600.0) ? 5.0 : 1.0;
        if (instability > 3.0) {
            penalties["chemical_instability"] = instability;
            narrative << "Large molecular size risks aggregation and shelf-instability. ";
        }

        // Delivery-vector compatibility
        if (insolubility > 15.0) {
            penalties["vector_incompatibility"] = insolubility - 15.0;
            flags.push_back("FORMULATION_IMPOSSIBILITY");
            narrative << "Candidate properties strictly incompatible with standard delivery vectors. ";
        }

        if (narrative.str().empty()) {
            summary = "Formulation properties are highly tractable for standard delivery.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Formulation"}, {"version", "1.0"}, {"type", "physicochemical"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

REGISTER_CONSTRAINT_BUNDLE("Formulation", FormulationBundle)

#endif // CURAFRAME_FORMULATION_BUNDLE_HPP
