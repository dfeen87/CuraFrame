"""
CuraFrame Comparators

Pure comparison functions used by Constraint objects.

This module contains NO domain knowledge, NO biological assumptions,
and NO optimization logic. It exists solely to provide transparent,
reusable comparison semantics for constraint evaluation.

All functions in this module are:
- Pure (no side effects)
- Stateless (no hidden state)
- Transparent (behavior is obvious from signature)
- Domain-agnostic (usable for any constraint type)
"""

from typing import Any, Tuple, Callable, Union
import math


# -----------------------------
# Basic scalar comparators
# -----------------------------

def less_than(value: Any, threshold: Any) -> bool:
    """
    value < threshold
    
    Raises:
        TypeError: If value and threshold cannot be compared
    """
    return value < threshold


def less_than_or_equal(value: Any, threshold: Any) -> bool:
    """
    value ≤ threshold
    
    Raises:
        TypeError: If value and threshold cannot be compared
    """
    return value <= threshold


def greater_than(value: Any, threshold: Any) -> bool:
    """
    value > threshold
    
    Raises:
        TypeError: If value and threshold cannot be compared
    """
    return value > threshold


def greater_than_or_equal(value: Any, threshold: Any) -> bool:
    """
    value ≥ threshold
    
    Raises:
        TypeError: If value and threshold cannot be compared
    """
    return value >= threshold


def equal_to(value: Any, threshold: Any) -> bool:
    """
    value == threshold
    
    Note: Uses Python's default equality semantics.
    For floating point, consider approximately_equal_to instead.
    
    Raises:
        TypeError: If value and threshold cannot be compared
    """
    return value == threshold


def not_equal_to(value: Any, threshold: Any) -> bool:
    """
    value ≠ threshold
    
    Raises:
        TypeError: If value and threshold cannot be compared
    """
    return value != threshold


# -----------------------------
# Floating-point aware comparators
# -----------------------------

def approximately_equal_to(
    value: float,
    threshold: Union[float, Tuple[float, float]]
) -> bool:
    """
    Check approximate equality within tolerance.
    
    Args:
        value: Value to test
        threshold: Either target_value or (target_value, epsilon)
    
    Returns:
        True if |value - target| < epsilon
    
    Examples:
        >>> approximately_equal_to(1.0001, (1.0, 0.001))
        True
        >>> approximately_equal_to(1.01, (1.0, 0.001))
        False
    """
    if isinstance(threshold, tuple):
        target, epsilon = threshold
    else:
        target = threshold
        epsilon = 1e-9  # Default tolerance
    
    return abs(value - target) < epsilon


def significantly_greater_than(
    value: float,
    threshold: Union[float, Tuple[float, float]]
) -> bool:
    """
    Check if value > threshold + epsilon (avoids floating point edge cases).
    
    Args:
        value: Value to test
        threshold: Either limit or (limit, epsilon)
    
    Returns:
        True if value significantly exceeds threshold
    """
    if isinstance(threshold, tuple):
        limit, epsilon = threshold
    else:
        limit = threshold
        epsilon = 1e-9
    
    return value > (limit + epsilon)


def significantly_less_than(
    value: float,
    threshold: Union[float, Tuple[float, float]]
) -> bool:
    """
    Check if value < threshold - epsilon (avoids floating point edge cases).
    
    Args:
        value: Value to test
        threshold: Either limit or (limit, epsilon)
    
    Returns:
        True if value significantly below threshold
    """
    if isinstance(threshold, tuple):
        limit, epsilon = threshold
    else:
        limit = threshold
        epsilon = 1e-9
    
    return value < (limit - epsilon)


# -----------------------------
# Range-based comparators
# -----------------------------

def within_range(
    value: float,
    bounds: Tuple[float, float],
    inclusive: bool = True
) -> bool:
    """
    Check whether value lies within [min, max] or (min, max).

    Args:
        value: Numeric value to evaluate
        bounds: (min_value, max_value)
        inclusive: Whether bounds are inclusive (default: True)

    Returns:
        True if value lies within bounds
    
    Raises:
        ValueError: If bounds are invalid (min > max)
    
    Examples:
        >>> within_range(5.0, (1.0, 10.0))
        True
        >>> within_range(10.0, (1.0, 10.0), inclusive=False)
        False
    """
    lower, upper = bounds
    
    if lower > upper:
        raise ValueError(f"Invalid bounds: lower ({lower}) > upper ({upper})")
    
    if math.isnan(value):
        return False
    
    if inclusive:
        return lower <= value <= upper
    return lower < value < upper


def outside_range(
    value: float,
    bounds: Tuple[float, float],
    inclusive: bool = True
) -> bool:
    """
    Check whether value lies outside [min, max] or (min, max).
    
    Inverse of within_range.
    
    Args:
        value: Numeric value to evaluate
        bounds: (min_value, max_value)
        inclusive: Whether bounds are inclusive (default: True)
    
    Returns:
        True if value lies outside bounds
    
    Examples:
        >>> outside_range(15.0, (1.0, 10.0))
        True
        >>> outside_range(5.0, (1.0, 10.0))
        False
    """
    return not within_range(value, bounds, inclusive=inclusive)


def within_tolerance(
    value: float,
    target: float,
    tolerance: float,
    relative: bool = False
) -> bool:
    """
    Check if value is within tolerance of target.
    
    Args:
        value: Value to test
        target: Target value
        tolerance: Absolute or relative tolerance
        relative: If True, tolerance is relative (percentage)
    
    Returns:
        True if value within tolerance of target
    
    Examples:
        >>> within_tolerance(10.5, 10.0, 1.0)  # Absolute
        True
        >>> within_tolerance(10.5, 10.0, 0.1, relative=True)  # 10% relative
        False
    """
    if relative:
        actual_tolerance = abs(target * tolerance)
    else:
        actual_tolerance = tolerance
    
    return abs(value - target) <= actual_tolerance


# -----------------------------
# Ratio and selectivity
# -----------------------------

def ratio_greater_than(
    ratio: float,
    threshold: Union[float, Tuple[float, float]]
) -> bool:
    """
    Check if a ratio exceeds a required threshold.

    Args:
        ratio: Observed ratio value (e.g., Kd_offtarget / Kd_ontarget)
        threshold: Either required_ratio or (required_ratio, epsilon)

    Returns:
        True if ratio > threshold
    
    Notes:
        Epsilon prevents numerical instability near threshold.
        For selectivity constraints like "100x selective for β₁ over β₂",
        pass the calculated ratio and required minimum.
    
    Examples:
        >>> ratio_greater_than(150.0, 100.0)  # 150x selectivity > 100x required
        True
        >>> ratio_greater_than(99.9, (100.0, 0.1))  # Just below threshold
        False
    """
    if isinstance(threshold, tuple):
        required_ratio, epsilon = threshold
    else:
        required_ratio = threshold
        epsilon = 0.0
    
    if math.isnan(ratio) or math.isinf(ratio):
        return False
    
    return ratio > (required_ratio + epsilon)


def ratio_less_than(
    ratio: float,
    threshold: Union[float, Tuple[float, float]]
) -> bool:
    """
    Check if a ratio is below a maximum allowed threshold.
    
    Args:
        ratio: Observed ratio value
        threshold: Either max_ratio or (max_ratio, epsilon)
    
    Returns:
        True if ratio < threshold
    
    Examples:
        >>> ratio_less_than(0.5, 1.0)  # Ratio below max
        True
    """
    if isinstance(threshold, tuple):
        max_ratio, epsilon = threshold
    else:
        max_ratio = threshold
        epsilon = 0.0
    
    if math.isnan(ratio) or math.isinf(ratio):
        return False
    
    return ratio < (max_ratio - epsilon)


def selectivity_satisfied(
    Kd_ontarget: float,
    Kd_offtarget: float,
    min_selectivity: float
) -> bool:
    """
    Check if off-target/on-target selectivity meets minimum requirement.
    
    Args:
        Kd_ontarget: Dissociation constant at desired target (lower = tighter)
        Kd_offtarget: Dissociation constant at off-target (higher = weaker)
        min_selectivity: Minimum required selectivity ratio
    
    Returns:
        True if Kd_offtarget / Kd_ontarget >= min_selectivity
    
    Notes:
        For pharmacology: higher Kd = weaker binding.
        A 100x selective drug has Kd_offtarget = 100 × Kd_ontarget.
    
    Examples:
        >>> selectivity_satisfied(1e-9, 100e-9, 100.0)  # 100x selective
        True
        >>> selectivity_satisfied(1e-9, 50e-9, 100.0)   # Only 50x, fails
        False
    """
    if Kd_ontarget <= 0 or Kd_offtarget <= 0:
        raise ValueError("Kd values must be positive")
    
    actual_selectivity = Kd_offtarget / Kd_ontarget
    return actual_selectivity >= min_selectivity


# -----------------------------
# Uncertainty-aware comparators
# -----------------------------

def conservative_upper_bound(
    value_with_uncertainty: Tuple[float, float, float],
    threshold: float
) -> bool:
    """
    Compare using the worst-case (upper) bound.
    
    Use this when the constraint represents a MAXIMUM allowed value,
    and you want to ensure even the upper uncertainty bound satisfies it.

    Args:
        value_with_uncertainty: (nominal, lower_bound, upper_bound)
        threshold: Maximum allowed value

    Returns:
        True if upper_bound ≤ threshold
    
    Philosophy:
        Conservative = assume the worst case.
        For safety-critical constraints, this prevents optimistic assumptions.
    
    Examples:
        >>> conservative_upper_bound((10.0, 9.0, 11.0), 12.0)  # Upper = 11 < 12
        True
        >>> conservative_upper_bound((10.0, 9.0, 13.0), 12.0)  # Upper = 13 > 12
        False
    """
    _, _, upper = value_with_uncertainty
    
    if math.isnan(upper) or math.isinf(upper):
        return False
    
    return upper <= threshold


def conservative_lower_bound(
    value_with_uncertainty: Tuple[float, float, float],
    threshold: float
) -> bool:
    """
    Compare using the worst-case (lower) bound.
    
    Use this when the constraint represents a MINIMUM required value,
    and you want to ensure even the lower uncertainty bound satisfies it.

    Args:
        value_with_uncertainty: (nominal, lower_bound, upper_bound)
        threshold: Minimum required value
    
    Returns:
        True if lower_bound ≥ threshold
    
    Philosophy:
        Conservative = assume the worst case.
        For efficacy constraints, this prevents optimistic assumptions.
    
    Examples:
        >>> conservative_lower_bound((10.0, 9.0, 11.0), 8.0)  # Lower = 9 > 8
        True
        >>> conservative_lower_bound((10.0, 7.0, 11.0), 8.0)  # Lower = 7 < 8
        False
    """
    _, lower, _ = value_with_uncertainty
    
    if math.isnan(lower) or math.isinf(lower):
        return False
    
    return lower >= threshold


def optimistic_nominal(
    value_with_uncertainty: Tuple[float, float, float],
    threshold: float,
    comparison: Callable[[float, float], bool]
) -> bool:
    """
    Compare using the nominal (expected) value, ignoring uncertainty.
    
    Use with caution: only appropriate when uncertainty is well-characterized
    and downstream validation will catch edge cases.
    
    Args:
        value_with_uncertainty: (nominal, lower_bound, upper_bound)
        threshold: Threshold value
        comparison: Comparison function (e.g., greater_than)
    
    Returns:
        True if comparison(nominal, threshold)
    
    Warning:
        This is NOT conservative. Use conservative_upper_bound or
        conservative_lower_bound for safety-critical constraints.
    """
    nominal, _, _ = value_with_uncertainty
    return comparison(nominal, threshold)


def probabilistic_satisfaction(
    value_with_uncertainty: Tuple[float, float, float],
    threshold: float,
    confidence_level: float = 0.95
) -> bool:
    """
    Check if constraint is satisfied with specified confidence.
    
    Assumes uniform distribution over [lower, upper].
    For normal distributions, use a specialized comparator.
    
    Args:
        value_with_uncertainty: (nominal, lower_bound, upper_bound)
        threshold: Maximum allowed value
        confidence_level: Required probability of satisfaction (0-1)
    
    Returns:
        True if P(value ≤ threshold) ≥ confidence_level
    
    Examples:
        >>> # Value uniform in [8, 12], threshold = 10
        >>> # P(value ≤ 10) = 0.5, so fails at 95% confidence
        >>> probabilistic_satisfaction((10.0, 8.0, 12.0), 10.0, 0.95)
        False
    """
    nominal, lower, upper = value_with_uncertainty
    
    if upper <= threshold:
        return True  # 100% probability
    
    if lower > threshold:
        return False  # 0% probability
    
    # Uniform distribution: fraction below threshold
    prob_satisfied = (threshold - lower) / (upper - lower)
    return prob_satisfied >= confidence_level


# -----------------------------
# Logical combinators
# -----------------------------

def all_of(*comparators: Callable[[Any, Any], bool]) -> Callable[[Any, Any], bool]:
    """
    Combine multiple comparator functions using logical AND.
    
    Args:
        *comparators: Variable number of comparator functions
    
    Returns:
        A comparator that returns True only if ALL comparators pass.
    
    Examples:
        >>> combined = all_of(greater_than, less_than_or_equal)
        >>> combined(5, (4, 10))  # 4 < 5 <= 10
        True
    
    Notes:
        Short-circuits on first False (efficient for expensive checks).
    """
    def _combined(value: Any, threshold: Any) -> bool:
        return all(comp(value, threshold) for comp in comparators)
    
    _combined.__name__ = f"all_of({', '.join(c.__name__ for c in comparators)})"
    return _combined


def any_of(*comparators: Callable[[Any, Any], bool]) -> Callable[[Any, Any], bool]:
    """
    Combine multiple comparator functions using logical OR.
    
    Args:
        *comparators: Variable number of comparator functions
    
    Returns:
        A comparator that returns True if ANY comparator passes.
    
    Examples:
        >>> combined = any_of(less_than, greater_than)
        >>> combined(15, (10, 20))  # Outside [10, 20]
        True
    
    Notes:
        Short-circuits on first True.
    """
    def _combined(value: Any, threshold: Any) -> bool:
        return any(comp(value, threshold) for comp in comparators)
    
    _combined.__name__ = f"any_of({', '.join(c.__name__ for c in comparators)})"
    return _combined


def none_of(*comparators: Callable[[Any, Any], bool]) -> Callable[[Any, Any], bool]:
    """
    Combine multiple comparator functions using logical NOR.
    
    Args:
        *comparators: Variable number of comparator functions
    
    Returns:
        A comparator that returns True only if NO comparators pass.
    
    Examples:
        >>> combined = none_of(less_than, greater_than)
        >>> combined(15, (10, 20))  # Within [10, 20], so neither < 10 nor > 20
        False
    """
    def _combined(value: Any, threshold: Any) -> bool:
        return not any(comp(value, threshold) for comp in comparators)
    
    _combined.__name__ = f"none_of({', '.join(c.__name__ for c in comparators)})"
    return _combined


# -----------------------------
# Null-safe wrappers
# -----------------------------

def null_safe(
    comparator: Callable[[Any, Any], bool],
    default: bool = False
) -> Callable[[Any, Any], bool]:
    """
    Wrap a comparator to handle None values gracefully.
    
    Args:
        comparator: Base comparator function
        default: Return value when value is None
    
    Returns:
        Null-safe version of comparator
    
    Examples:
        >>> safe_gt = null_safe(greater_than, default=False)
        >>> safe_gt(None, 10)
        False
        >>> safe_gt(15, 10)
        True
    """
    def _null_safe(value: Any, threshold: Any) -> bool:
        if value is None:
            return default
        return comparator(value, threshold)
    
    _null_safe.__name__ = f"null_safe({comparator.__name__})"
    return _null_safe


# -----------------------------
# Validation helpers
# -----------------------------

def is_finite(value: float) -> bool:
    """Check if value is finite (not NaN or Inf)."""
    return not (math.isnan(value) or math.isinf(value))


def is_positive(value: float) -> bool:
    """Check if value is strictly positive."""
    return is_finite(value) and value > 0


def is_non_negative(value: float) -> bool:
    """Check if value is non-negative."""
    return is_finite(value) and value >= 0
