
def calculate_priority(candidate):

    criticality_weights = {
        "critical": 100,
        "high": 70,
        "medium": 40,
        "low": 20,
    }

    urgency_weights = {
        "high": 50,
        "medium": 25,
        "low": 10,
    }

    criticality = str(
        candidate["criticality"]
    ).strip().lower()

    urgency = str(
        candidate["urgency"]
    ).strip().lower()

    risk = float(
        candidate["predicted_failure_probability"]
    )

    criticality_score = criticality_weights.get(
        criticality, 0
    )

    urgency_score = urgency_weights.get(
        urgency, 0
    )

    risk_score = round(risk * 100)

    total_score = (
        criticality_score
        + urgency_score
        + risk_score
    )

    return total_score


def calculate_candidate_scores(candidates):

    return [
        calculate_priority(candidate)
        for candidate in candidates
    ]
