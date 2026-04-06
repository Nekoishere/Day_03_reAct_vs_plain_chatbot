# Football Benchmark Report

- Generated at: `2026-04-06T12:31:13.897150`
- Provider: `dummy`
- Model: `dummy`
- Run tag: `demo`
- Mode: `both`
- Dataset source: `cli_question`
- Dataset size: `2`
- Baseline version: `b1`
- ReAct version: `r1`
- Toolset version: `t1`
- Dataset version: `u1`

## Comparison Summary

| Metric | Baseline | ReAct |
|---|---:|---:|
| Avg keyword score | 0.0 | 0.0 |
| Total tokens | 28 | 42 |
| Avg latency (ms) | 2.0 | 2.0 |
| Avg steps | - | 0.5 |

## Baseline QA

### Q: Ai vo dich World Cup 2018?
- Score: `N/A`
- A: Thought: check
Action: world_cup_champion_by_year(2018)

### Q: Nha vo dich Euro 2016 la ai?
- Score: `N/A`
- A: Portugal won Euro 2016.

## ReAct QA

### Q: Ai vo dich World Cup 2018?
- Score: `N/A`
- A: France won 2018 World Cup 4-2 Croatia.

### Q: Nha vo dich Euro 2016 la ai?
- Score: `N/A`
- A: Portugal won Euro 2016.
