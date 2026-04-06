from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class EvalSample:
    question: str
    must_have_keywords: List[str]


@dataclass
class EvalRecord:
    question: str
    answer: str
    score: float
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


FOOTBALL_DATASET: List[EvalSample] = [
    EvalSample(
        question="Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?",
        must_have_keywords=["France", "4-2", "Croatia"],
    ),
    EvalSample(
        question="Nha vo dich Euro 2016 la ai?",
        must_have_keywords=["Portugal"],
    ),
    EvalSample(
        question="Real Madrid vo dich Champions League cac nam nao trong dataset?",
        must_have_keywords=["2022", "2024", "Real Madrid"],
    ),
]


def keyword_score(answer: str, keywords: List[str]) -> float:
    content = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in content)
    return round(hits / max(1, len(keywords)), 2)


def avg_score(records: List[EvalRecord]) -> float:
    if not records:
        return 0.0
    return round(sum(r.score for r in records) / len(records), 2)
