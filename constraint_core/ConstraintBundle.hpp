#ifndef CURAFRAME_CONSTRAINT_BUNDLE_HPP
#define CURAFRAME_CONSTRAINT_BUNDLE_HPP

#include "Candidate.hpp"
#include <string>
#include <map>
#include <vector>

// Base interface for all constraint bundles
class ConstraintBundle {
public:
    virtual ~ConstraintBundle() = default;

    // Evaluates the candidate against this bundle's specific constraints
    virtual void evaluate(const Candidate& c) = 0;

    // Returns a map of metadata for this bundle (e.g. domain, version)
    virtual std::map<std::string, std::string> bundle_metadata() const = 0;

    // Returns the calculated penalty signals
    virtual std::map<std::string, double> penalty_signals() const = 0;

    // Returns any falsification flags triggered during evaluation
    virtual std::vector<std::string> falsification_flags() const = 0;

    // Returns a short, domain-specific narrative reasoning summary
    virtual std::string narrative_summary() const = 0;
};

#endif // CURAFRAME_CONSTRAINT_BUNDLE_HPP
