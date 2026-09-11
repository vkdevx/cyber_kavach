class ConfidenceEngine:
    """Calculates model agreement and data sufficiency confidence score (0.0 to 1.0)."""

    @staticmethod
    def calculate_confidence(rf_prob: float, if_score: float, packet_count: int) -> float:
        # Base confidence from model concordance
        concordance = 1.0 - abs(rf_prob - if_score)
        base_conf = (rf_prob + concordance) / 2.0

        # Data sufficiency boost: more packets in flow window yield higher confidence
        data_sufficiency = min(1.0, packet_count / 10.0)

        final_conf = max(0.1, min(1.0, base_conf * (0.7 + 0.3 * data_sufficiency)))
        return float(round(final_conf, 2))
