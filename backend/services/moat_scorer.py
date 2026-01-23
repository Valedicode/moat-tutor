"""
Moat Scoring and Validation Logic

This module provides utilities to validate moat assessments and ensure
consistency between dimension scores, overall score, and categorical rating.
"""

from typing import Tuple
from api.models.responses import MoatAssessment


def calculate_overall_score(assessment: MoatAssessment) -> float:
    """
    Calculate the overall moat score as the average of all dimension scores.
    
    Args:
        assessment: MoatAssessment with dimension scores
        
    Returns:
        Average score (0-5)
    """
    scores = [
        assessment.switching_costs.score,
        assessment.network_effects.score,
        assessment.intangible_assets.score,
        assessment.cost_advantages.score,
        assessment.regulatory_barriers.score,
        assessment.ecosystem_lockin.score,
    ]
    return round(sum(scores) / len(scores), 2)


def determine_rating_from_scores(
    overall_score: float,
    dimension_scores: list[float],
    overall_confidence: str
) -> str:
    """
    Determine the appropriate Wide/Narrow/None rating based on scores.
    
    Logic:
    - Wide: overall ≥ 4.0 AND (2+ dimensions ≥ 4.0 OR 1 dimension = 5.0) AND confidence ≠ Low
    - Narrow: overall 2.5-3.9 OR (overall ≥ 4.0 but only 1 strong dimension) OR confidence = Low
    - None: overall < 2.5 OR all dimensions < 3.0
    
    Args:
        overall_score: Average of dimension scores
        dimension_scores: List of individual dimension scores
        overall_confidence: Low, Medium, or High
        
    Returns:
        "Wide", "Narrow", or "None"
    """
    # Count strong dimensions
    strong_dimensions = sum(1 for score in dimension_scores if score >= 4.0)
    exceptional_dimensions = sum(1 for score in dimension_scores if score >= 5.0)
    
    # None conditions
    if overall_score < 2.5:
        return "None"
    if all(score < 3.0 for score in dimension_scores):
        return "None"
    
    # Wide conditions
    if overall_score >= 4.0 and overall_confidence != "Low":
        if strong_dimensions >= 2 or exceptional_dimensions >= 1:
            return "Wide"
    
    # Narrow (default for scores 2.5-3.9 or ambiguous cases)
    return "Narrow"


def validate_moat_assessment(assessment: MoatAssessment) -> Tuple[bool, str]:
    """
    Validate that a moat assessment is internally consistent.
    
    Checks:
    1. Overall score matches average of dimension scores
    2. Overall rating is consistent with scores and confidence
    3. All scores are within valid range (0-5)
    4. Direction and confidence values are valid
    
    Args:
        assessment: MoatAssessment to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if assessment passes all checks
        - error_message: Empty string if valid, otherwise describes the issue
    """
    # Check score ranges
    dimension_scores = [
        assessment.switching_costs.score,
        assessment.network_effects.score,
        assessment.intangible_assets.score,
        assessment.cost_advantages.score,
        assessment.regulatory_barriers.score,
        assessment.ecosystem_lockin.score,
    ]
    
    for i, score in enumerate(dimension_scores):
        if not (0 <= score <= 5):
            return False, f"Dimension score {i} is out of range: {score} (must be 0-5)"
    
    if not (0 <= assessment.overall_score <= 5):
        return False, f"Overall score is out of range: {assessment.overall_score} (must be 0-5)"
    
    # Check overall score calculation (allow small rounding difference)
    calculated_overall = calculate_overall_score(assessment)
    if abs(calculated_overall - assessment.overall_score) > 0.1:
        return False, (f"Overall score {assessment.overall_score} does not match "
                      f"average of dimensions {calculated_overall}")
    
    # Check direction values
    valid_directions = {"Strengthening", "Stable", "Weakening"}
    dimensions = [
        assessment.switching_costs,
        assessment.network_effects,
        assessment.intangible_assets,
        assessment.cost_advantages,
        assessment.regulatory_barriers,
        assessment.ecosystem_lockin,
    ]
    
    for dim in dimensions:
        if dim.direction not in valid_directions:
            return False, f"Invalid direction: {dim.direction} (must be Strengthening, Stable, or Weakening)"
    
    # Check confidence values
    valid_confidence = {"Low", "Medium", "High"}
    for dim in dimensions:
        if dim.confidence not in valid_confidence:
            return False, f"Invalid confidence: {dim.confidence} (must be Low, Medium, or High)"
    
    if assessment.overall_confidence not in valid_confidence:
        return False, f"Invalid overall confidence: {assessment.overall_confidence}"
    
    # Check rating consistency with scores
    expected_rating = determine_rating_from_scores(
        assessment.overall_score,
        dimension_scores,
        assessment.overall_confidence
    )
    
    if assessment.overall_rating not in {"Wide", "Narrow", "None"}:
        return False, f"Invalid overall rating: {assessment.overall_rating} (must be Wide, Narrow, or None)"
    
    # Warn but don't fail if rating doesn't match expected
    # (allow some agent discretion, but log it)
    if assessment.overall_rating != expected_rating:
        # This is a soft warning - we'll log it but not fail validation
        import logging
        logging.warning(
            f"Rating mismatch: agent said '{assessment.overall_rating}' "
            f"but scores suggest '{expected_rating}' "
            f"(overall={assessment.overall_score}, strong_dims={sum(1 for s in dimension_scores if s >= 4.0)})"
        )
    
    return True, ""


def get_rating_explanation(assessment: MoatAssessment) -> str:
    """
    Generate a human-readable explanation of why the rating was assigned.
    
    Args:
        assessment: MoatAssessment with scores and rating
        
    Returns:
        Explanation string
    """
    dimension_scores = [
        ("Switching Costs", assessment.switching_costs.score),
        ("Network Effects", assessment.network_effects.score),
        ("Intangible Assets", assessment.intangible_assets.score),
        ("Cost Advantages", assessment.cost_advantages.score),
        ("Regulatory Barriers", assessment.regulatory_barriers.score),
        ("Ecosystem Lock-in", assessment.ecosystem_lockin.score),
    ]
    
    strong_dims = [(name, score) for name, score in dimension_scores if score >= 4.0]
    moderate_dims = [(name, score) for name, score in dimension_scores if 3.0 <= score < 4.0]
    
    explanation = f"Overall rating: {assessment.overall_rating} (score: {assessment.overall_score}/5.0)\n"
    
    if strong_dims:
        explanation += f"Strong dimensions ({len(strong_dims)}): "
        explanation += ", ".join([f"{name} ({score:.1f})" for name, score in strong_dims])
        explanation += "\n"
    
    if moderate_dims:
        explanation += f"Moderate dimensions ({len(moderate_dims)}): "
        explanation += ", ".join([f"{name} ({score:.1f})" for name, score in moderate_dims])
        explanation += "\n"
    
    explanation += f"Confidence: {assessment.overall_confidence}"
    
    return explanation
