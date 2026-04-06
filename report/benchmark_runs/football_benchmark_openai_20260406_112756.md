# Football Benchmark Report

- Generated at: `2026-04-06T11:27:56.897201`
- Provider: `openai`
- Model: `gpt-4o`

## Comparison Summary

| Metric | Baseline | ReAct |
|---|---:|---:|
| Avg keyword score | 0.45 | 0.67 |
| Total tokens | 261 | 1438 |
| Avg latency (ms) | 1600.67 | 1074.5 |
| Avg steps | - | 1.0 |

## Baseline QA

### Q: Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?
- Score: `0.67`
- A: Đội tuyển Pháp vô địch World Cup 2018 và tỷ số chung kết là 4-2 trước Croatia.

### Q: Nha vo dich Euro 2016 la ai?
- Score: `0.0`
- A: Nhà vô địch Euro 2016 là đội tuyển Bồ Đào Nha.

### Q: Real Madrid vo dich Champions League cac nam nao trong dataset?
- Score: `0.67`
- A: Trong dataset của tôi, Real Madrid đã vô địch UEFA Champions League các năm: 1956, 1957, 1958, 1959, 1960, 1966, 1998, 2000, 2002, 2014, 2016, 2017, 2018 và 2022.

## ReAct QA

### Q: Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?
- Score: `0.67`
- A: Đội tuyển Pháp đã vô địch World Cup 2018, đánh bại Croatia với tỷ số 4-2 trong trận chung kết.

### Q: Nha vo dich Euro 2016 la ai?
- Score: `1.0`
- A: The winner of Euro 2016 was Portugal. They defeated France 1-0 in the final.

### Q: Real Madrid vo dich Champions League cac nam nao trong dataset?
- Score: `0.33`
- A: Qua kết quả tìm kiếm trong tập dữ liệu có sẵn, Real Madrid đã vô địch Champions League hai lần.
