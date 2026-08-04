// Licensed under the PolyForm Noncommercial License 1.0.0
#ifndef CURAFRAME_CANDIDATE_HPP
#define CURAFRAME_CANDIDATE_HPP

#include <string>
#include <map>

// Fictional representation of a therapeutic candidate
struct Candidate {
    std::string id;
    std::string structure_smiles;
    double molecular_weight;
    double logp;

    // Additional domain-specific properties can be mapped here
    std::map<std::string, double> properties;

    Candidate(std::string id = "unknown") : id(id), molecular_weight(0.0), logp(0.0) {}
};

#endif // CURAFRAME_CANDIDATE_HPP
