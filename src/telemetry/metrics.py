import time
from typing import Dict, Any, List, Optional
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int],
        latency_ms: int,
        scenario: Optional[str] = None,
    ):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage), # Mock cost calculation
            "scenario": scenario or "unspecified",
            "created_at": int(time.time() * 1000),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        TODO: Implement real pricing logic.
        For now, returns a dummy constant.
        """
        return (usage.get("total_tokens", 0) / 1000) * 0.01

    def reset(self):
        self.session_metrics = []

    def summarize(self, scenario: Optional[str] = None) -> Dict[str, Any]:
        metrics = self.session_metrics
        if scenario is not None:
            metrics = [m for m in metrics if m.get("scenario") == scenario]

        count = len(metrics)
        if count == 0:
            return {
                "requests": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_latency_ms": 0,
                "avg_latency_ms": 0,
                "total_cost_estimate": 0.0,
            }

        total_prompt_tokens = sum(m["prompt_tokens"] for m in metrics)
        total_completion_tokens = sum(m["completion_tokens"] for m in metrics)
        total_tokens = sum(m["total_tokens"] for m in metrics)
        total_latency_ms = sum(m["latency_ms"] for m in metrics)
        total_cost_estimate = sum(m["cost_estimate"] for m in metrics)

        return {
            "requests": count,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency_ms,
            "avg_latency_ms": round(total_latency_ms / count, 2),
            "total_cost_estimate": round(total_cost_estimate, 6),
        }

# Global tracker instance
tracker = PerformanceTracker()
