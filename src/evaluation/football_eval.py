import json
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional


@dataclass
class EvalSample:
    question: str
    must_have_keywords: List[str] = field(default_factory=list)


@dataclass
class EvalRecord:
    question: str
    answer: str
    score: Optional[float]
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
    scored = [r.score for r in records if r.score is not None]
    if not scored:
        return 0.0
    return round(sum(scored) / len(scored), 2)


def sample_from_dict(data: Dict[str, Any]) -> EvalSample:
    question = str(data.get("question", "")).strip()
    if not question:
        raise ValueError("Each sample must include a non-empty 'question'.")

    keywords = data.get("must_have_keywords", [])
    if keywords is None:
        keywords = []
    if not isinstance(keywords, list):
        raise ValueError("'must_have_keywords' must be a list of strings.")
    keywords = [str(k) for k in keywords]
    return EvalSample(question=question, must_have_keywords=keywords)


def load_dataset_from_json(path: str) -> List[EvalSample]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError("Dataset JSON must be a list of objects.")

    return [sample_from_dict(item) for item in raw]


def build_dataset_from_questions(questions: List[str]) -> List[EvalSample]:
    cleaned = [q.strip() for q in questions if q and q.strip()]
    return [EvalSample(question=q, must_have_keywords=[]) for q in cleaned]


def interactive_collect_samples() -> List[EvalSample]:
    print("\n=== Dataset Input UI (Terminal) ===")
    print("Nhập câu hỏi từng dòng. Enter rỗng để kết thúc.")
    print("Tùy chọn từ khóa chấm điểm: nhập dạng kw1,kw2,kw3 (có thể bỏ trống).")

    items: List[EvalSample] = []
    idx = 1
    while True:
        question = input(f"\nQ{idx}: ").strip()
        if not question:
            break
        keywords_raw = input("  Keywords (optional, comma-separated): ").strip()
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()] if keywords_raw else []
        items.append(EvalSample(question=question, must_have_keywords=keywords))
        idx += 1

    return items
