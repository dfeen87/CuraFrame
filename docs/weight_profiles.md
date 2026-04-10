# Weight Profiles (v3.0.0)

## Design and Intent

Weight Profiles allow the CuraFrame Scoring Engine to view candidates under different lenses of scrutiny. Instead of hardcoded aggregation metrics, `WeightProfile` provides a configurable approach to amplifying certain domains (e.g., Cardiac or CNS safety) based on the context of the evaluation.

## Built-in Profiles

### 1. `DefaultResearchProfile`
- A balanced, general-purpose profile.
- Mildly emphasizes safety parameters but treats most domains with an equal base weight.

### 2. `HighSafetyProfile`
- Designed for late-stage conservative screening.
- Applies heavy multipliers to `Safety`, `Cardiac`, `CNS`, and `SystemicExposure` domains.
- Heavily amplifies specific toxicity signals.
- Punishes falsification flags almost entirely zeroing out candidate viability.

## Extending Weight Profiles

To create a new weight profile, inherit from the `WeightProfile` abstract base class and implement the necessary configuration hooks.

```cpp
class PediatricSafetyProfile : public WeightProfile {
public:
    std::string name() const override { return "PediatricSafetyProfile"; }

    double bundle_weight(const std::string& bundle_name) const override {
        // Significantly amplify systemic exposure and safety for pediatric focus
        if (bundle_name == "SystemicExposure" || bundle_name == "Safety") return 3.0;
        return 1.0;
    }

    double signal_weight(const std::string& bundle_name, const std::string& signal_name) const override {
        if (signal_name.find("clearance") != std::string::npos) return 2.0;
        return 1.0;
    }

    double falsification_penalty() const override { return 100.0; }
};
```
