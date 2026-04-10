#include "WeightedScoringEngine.hpp"
#include <sstream>
#include <algorithm>
#include <iostream>
#include <cmath>

WeightedScoringEngine::WeightedScoringEngine(std::shared_ptr<WeightProfile> profile)
    : profile_(std::move(profile)) {}

ScoringReport WeightedScoringEngine::score(const EvaluationReport& eval_report) const {
    ScoringReport report;
    report.weight_profile_name = profile_->name();

    double total_penalties = 0.0;
    double total_bonuses = 0.0;

    // Process penalties per domain
    for (const auto& domain_pair : eval_report.domain_penalty_signals) {
        const std::string& domain_name = domain_pair.first;
        double bundle_weight = profile_->bundle_weight(domain_name);

        double domain_penalty_sum = 0.0;

        for (const auto& signal_pair : domain_pair.second) {
            const std::string& signal_name = signal_pair.first;
            double raw_value = signal_pair.second;

            double signal_weight = profile_->signal_weight(domain_name, signal_name);

            if (raw_value > 0) {
                // It's a penalty
                double weighted_penalty = raw_value * bundle_weight * signal_weight * profile_->penalty_multiplier();
                report.penalty_breakdown[domain_name + "::" + signal_name] = weighted_penalty;
                domain_penalty_sum += weighted_penalty;
            } else if (raw_value < 0) {
                // It's a bonus (represented as negative penalty in some contexts, or we can handle it directly)
                double weighted_bonus = std::abs(raw_value) * bundle_weight * signal_weight * profile_->bonus_multiplier();
                report.bonus_breakdown[domain_name + "::" + signal_name] = weighted_bonus;
                total_bonuses += weighted_bonus;
            }
        }

        report.bundle_contributions[domain_name] = domain_penalty_sum;
        total_penalties += domain_penalty_sum;
    }

    // Process falsification flags
    report.falsification_flags = eval_report.falsification_flags;
    if (!report.falsification_flags.empty()) {
        report.falsification_impact = profile_->falsification_penalty() * report.falsification_flags.size();
    }

    // Base score is 100. We subtract penalties and falsifications, add bonuses.
    double base_score = 100.0;
    double raw_score = base_score - total_penalties - report.falsification_impact + total_bonuses;

    // Apply global scaling factor
    raw_score *= profile_->global_scaling_factor();

    // Clamp between 0 and 100
    report.composite_score = std::max(0.0, std::min(100.0, raw_score));

    report.narrative_summary = generate_narrative(report, eval_report);

    return report;
}

std::string WeightedScoringEngine::generate_narrative(const ScoringReport& report, const EvaluationReport& eval_report) const {
    std::ostringstream oss;

    oss << "Scoring Summary (Profile: " << report.weight_profile_name << "):\n";
    oss << "Composite Stability Score: " << report.composite_score << "/100\n";

    if (!report.falsification_flags.empty()) {
        oss << "CRITICAL: Candidate was falsified. " << report.falsification_flags.size() << " flags raised, contributing to a massive penalty of " << report.falsification_impact << ".\n";
    }

    std::string max_penalty_domain = "";
    double max_penalty = -1.0;
    for (const auto& pair : report.bundle_contributions) {
        if (pair.second > max_penalty) {
            max_penalty = pair.second;
            max_penalty_domain = pair.first;
        }
    }

    if (max_penalty > 0) {
        oss << "The highest risk burden originated from the " << max_penalty_domain << " bundle (" << max_penalty << " weighted penalty).\n";
    } else {
        oss << "No significant domain penalties were recorded.\n";
    }

    if (!report.bonus_breakdown.empty()) {
        oss << "Bonuses were applied which mitigated some risk factors.\n";
    }

    if (report.weight_profile_name == "HighSafetyProfile") {
        oss << "The HighSafetyProfile heavily penalized safety and toxicity signals, resulting in a conservative stability score.\n";
    }

    return oss.str();
}
