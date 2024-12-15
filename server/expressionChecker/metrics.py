from rapidfuzz.distance import Levenshtein


class Metrics:
    @staticmethod
    def levenshteinMetric(r1: str, r2: str) -> int:
        "computes metric as the sum of Levenstein distances in the following path: root1->root2"
        return Levenshtein.distance(r1, r2)
