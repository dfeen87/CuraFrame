# Unified Evaluation Pipeline

The C++ subsystem introduces a streamlined, non-breaking evaluation pipeline designed to apply all active constraint bundles against a candidate structure in a single pass.

## Evaluation Flow
1. **Candidate Construction:** A `Candidate` structure is instantiated (e.g., via SMILES, MW, logP).
2. **Registry Invocation:** `ConstraintRegistry::instance()` automatically resolves and constructs all compiled `ConstraintBundle` implementations.
3. **Multi-Bundle Execution:** `MultiBundleEvaluator` traverses the bundles, injecting the `Candidate` into each `evaluate()` method.
4. **Aggregation:**
    - `penalty_signals()` are mapped by domain into a nested matrix.
    - `falsification_flags()` are aggregated into a linear vector indicating hard failures.
    - `narrative_summary()` strings are concatenated into a human-readable diagnostic report.
5. **Report Generation:** Produces a deterministic `EvaluationReport`.

## Example
```cpp
#include "constraint_core/Candidate.hpp"
#include "constraint_core/MultiBundleEvaluator.hpp"
#include <iostream>

int main() {
    Candidate c("MOL-123");
    c.molecular_weight = 480.5;
    c.logp = 4.2;

    MultiBundleEvaluator evaluator;
    EvaluationReport report = evaluator.evaluate(c);

    if (!report.is_viable()) {
        std::cout << "Candidate Falsified. Triggers:\n";
        for (const auto& flag : report.falsification_flags) {
            std::cout << "- " << flag << "\n";
        }
    }

    std::cout << "\nNarrative Summary:\n" << report.combined_narrative << "\n";
    return 0;
}
```
