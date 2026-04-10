#ifndef CURAFRAME_WEIGHT_PROFILE_HPP
#define CURAFRAME_WEIGHT_PROFILE_HPP

#include <string>
#include <map>
#include <memory>

class WeightProfile {
public:
    virtual ~WeightProfile() = default;

    virtual std::string name() const = 0;

    // Default fallback weight if a bundle or signal is not explicitly defined
    virtual double default_weight() const { return 1.0; }

    // Per-bundle weights
    virtual double bundle_weight(const std::string& bundle_name) const = 0;

    // Per-signal weights (can override bundle weights for specific signals)
    virtual double signal_weight(const std::string& bundle_name, const std::string& signal_name) const = 0;

    // Penalty and Bonus multipliers
    virtual double penalty_multiplier() const { return 1.0; }
    virtual double bonus_multiplier() const { return 1.0; }

    // Global scaling factor
    virtual double global_scaling_factor() const { return 1.0; }

    // Falsification penalty
    virtual double falsification_penalty() const { return 50.0; } // Heavy penalty for falsification
};

class DefaultResearchProfile : public WeightProfile {
public:
    std::string name() const override { return "DefaultResearchProfile"; }

    double bundle_weight(const std::string& bundle_name) const override {
        if (bundle_name == "Safety") return 1.5;
        return 1.0;
    }

    double signal_weight(const std::string& bundle_name, const std::string& signal_name) const override {
        return 1.0;
    }
};

class HighSafetyProfile : public WeightProfile {
public:
    std::string name() const override { return "HighSafetyProfile"; }

    double bundle_weight(const std::string& bundle_name) const override {
        if (bundle_name == "Safety" || bundle_name == "Cardiac" || bundle_name == "CNS" || bundle_name == "SystemicExposure") {
            return 2.0;
        }
        return 1.0;
    }

    double signal_weight(const std::string& bundle_name, const std::string& signal_name) const override {
        if (signal_name.find("toxicity") != std::string::npos || signal_name.find("risk") != std::string::npos) {
            return 1.5;
        }
        return 1.0;
    }

    double penalty_multiplier() const override { return 1.5; }
    double bonus_multiplier() const override { return 0.5; } // Conservative
    double falsification_penalty() const override { return 100.0; } // Immediate zero or near-zero
};

#endif // CURAFRAME_WEIGHT_PROFILE_HPP
