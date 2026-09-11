class SeverityMapper:
    """Maps integer risk scores (0-100) to 5 explicit severity bands."""

    @staticmethod
    def map_score_to_severity(score: int) -> str:
        s = max(0, min(100, score))
        if s <= 19:
            return "Informational"
        elif s <= 39:
            return "Low"
        elif s <= 59:
            return "Medium"
        elif s <= 79:
            return "High"
        else:
            return "Critical"
