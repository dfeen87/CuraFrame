#ifndef CURAFRAME_IMMUNOLOGIC_BUNDLE_HPP
#define CURAFRAME_IMMUNOLOGIC_BUNDLE_HPP

#include "../../constraint_core/ConstraintBundle.hpp"
#include "../../constraint_core/ConstraintRegistry.hpp"
#include <sstream>

class ImmunologicBundle : public ConstraintBundle {
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

        // Large molecules act as potential immunogens
        double immunogenicity = mw / 100.0;

        // Immune-activation thresholds
        if (immunogenicity > 6.0) {
            penalties["immune_activation"] = immunogenicity - 6.0;
            narrative << "High molecular weight triggers baseline immune activation. ";
        }

        // Cytokine-storm risk
        double cytokine_storm_risk = (immunogenicity > 8.0) ? 7.0 : 1.0;
        if (cytokine_storm_risk > 5.0) {
            penalties["cytokine_storm_risk"] = cytokine_storm_risk;
            flags.push_back("CYTOKINE_STORM_ALERT");
            narrative << "Runaway systemic inflammation (cytokine storm) risk detected. ";
        }

        // Tolerance-breakdown heuristics
        double tolerance_breakdown = immunogenicity * 1.5;
        if (tolerance_breakdown > 12.0) {
            penalties["tolerance_breakdown"] = tolerance_breakdown - 12.0;
            flags.push_back("AUTOIMMUNE_TOLERANCE_BREAK");
            narrative << "Self-tolerance breakdown threatening autoimmune response. ";
        }

        if (narrative.str().empty()) {
            summary = "Immunologic profile is inert and well-tolerated.";
        } else {
            summary = narrative.str();
        }
    }

    std::map<std::string, std::string> bundle_metadata() const override {
        return {{"domain", "Immunologic"}, {"version", "1.0"}, {"type", "systemic"}};
    }

    std::map<std::string, double> penalty_signals() const override { return penalties; }
    std::vector<std::string> falsification_flags() const override { return flags; }
    std::string narrative_summary() const override { return summary; }
};

REGISTER_CONSTRAINT_BUNDLE("Immunologic", ImmunologicBundle)

#endif // CURAFRAME_IMMUNOLOGIC_BUNDLE_HPP
