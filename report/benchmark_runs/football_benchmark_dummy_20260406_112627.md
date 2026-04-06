# Football Benchmark Report

- Generated at: `2026-04-06T11:26:27.899762`
- Provider: `dummy`
- Model: `dummy`

## Comparison Summary

| Metric | Baseline | ReAct |
|---|---:|---:|
| Avg keyword score | 0.11 | 1.0 |
| Total tokens | 66 | 132 |
| Avg latency (ms) | 5.0 | 5.0 |
| Avg steps | - | 1.0 |

## Baseline QA

### Q: Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?
- Score: `0.0`
- A: Thought: Tim du lieu
Action: world_cup_champion_by_year(2018)

### Q: Nha vo dich Euro 2016 la ai?
- Score: `0.0`
- A: Thought: Tim du lieu
Action: search_football_history(Euro 2016)

### Q: Real Madrid vo dich Champions League cac nam nao trong dataset?
- Score: `0.33`
- A: Thought: Tim du lieu
Action: search_football_history(Real Madrid Champions League)

## ReAct QA

### Q: Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?
- Score: `1.0`
- A: France vo dich World Cup 2018 voi ti so 4-2 truoc Croatia. Portugal vo dich Euro 2016. Real Madrid vo dich 2022 va 2024.

### Q: Nha vo dich Euro 2016 la ai?
- Score: `1.0`
- A: France vo dich World Cup 2018 voi ti so 4-2 truoc Croatia. Portugal vo dich Euro 2016. Real Madrid vo dich 2022 va 2024.

### Q: Real Madrid vo dich Champions League cac nam nao trong dataset?
- Score: `1.0`
- A: France vo dich World Cup 2018 voi ti so 4-2 truoc Croatia. Portugal vo dich Euro 2016. Real Madrid vo dich 2022 va 2024.
