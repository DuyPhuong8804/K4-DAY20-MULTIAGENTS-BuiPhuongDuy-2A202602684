# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Bùi Phương Duy | 2A202602684 | Làm cá nhân toàn bộ: cài đặt harness (`agent.py`, `subagents.py`, `runner.py`, `curator.py`), chạy thí nghiệm, phân tích, báo cáo |

- Mô hình: `gpt-6-luna` qua API OpenAI (`LAB_MODEL=openai:gpt-6-luna`, khóa `OPENAI_API_KEY`). `LAB_TEMPERATURE=1`: mô hình từ chối `temperature=0` ("Only the default (1) value is supported"), nên mọi lần chạy đều lấy mẫu ngẫu nhiên và không lặp lại được từng bit. `recursion_limit` = 60 (mặc định của `lab.runner`).
- Deep Agents 0.7.21 (`pip show deepagents`), Python 3.12.15. Máy chủ Windows 11; mọi lệnh `pytest`, `lab.runner`, `lab.curator` chạy **trong Docker** (`python:3.12-slim`, dựng từ `Dockerfile` của lab, mã nguồn gắn vào `/lab`), vì shell của tác tử cần `/bin/sh`. `verify_freeze.py` và `check_breakdown.py` chạy trong một image phụ có thêm `git` (`FROM lab-deepagents` + `apt-get install git`), vì image gốc không có git.
- Số lần chạy: **21 lần chạy tác tử hợp lệ** (baseline 6, subagents 6, skills-auto-dev 3 ở Phần 3.4, skills-auto 6 sau đóng băng) và 1 lần gọi curator. Ngoài ra khoảng 6 lần chạy đầu tiên (baseline và subagents trên tác vụ học) bị loại và xóa vì lỗi CRLF, xem mục 4 và 9. Không có ngân sách cố định được giao nên không so với ngân sách.
- Commit của tag `freeze`: `87c98c5` (`87c98c566d8f9cc605295957a6546d8891d50d98`, 2026-10-06 12:14:26 +07:00). Commit `hypotheses` đứng trước là `7df7c88`.

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): `subagents` sẽ **không** cải thiện điểm tác vụ đánh giá so với `baseline` (chênh lệch điểm trung bình trong khoảng ±0,05, tức nằm trong nhiễu), và sẽ tốn khoảng 3 lần token trở lên. Căn cứ: ở tác vụ học, `baseline` và `subagents` đạt cùng 7/10, 5/8, 6/9; check kỹ thuật đã đạt 18/18 ở `baseline` nên không còn gì cho subagent cải thiện; 9/9 lỗi thuộc nhóm E (quy ước không có trong đề) và explorer chính nó báo "no documented basis" cho quy ước Acme, nên chia việc không tạo ra tri thức mới; token tăng 3,1 đến 3,7 lần. Phù hợp với bài báo hệ thống nghiên cứu đa tác tử của Anthropic (đa tác tử tốn nhiều token, khoảng 15 lần so với hội thoại thường) và với lưu ý của `02_subagents.md` rằng subagent không phù hợp cho tác vụ ít bước.
- H2 (skills-auto so với baseline): `skills-auto` sẽ đạt điểm **cao nhất** trên tác vụ đánh giá, nhưng chỉ cải thiện một phần: dự đoán điểm trung bình tăng khoảng 0,10 đến 0,20 so với `baseline`, không đạt 1,0. Toàn bộ mức tăng đến từ các check quy ước `rule_` mà tác vụ đánh giá dùng lại từ tác vụ học (đề bài nói tác vụ đánh giá dùng lại các quy ước của tác vụ học), vì 3 skill chép đúng các quy ước đó. Check quy ước **mới** của tác vụ đánh giá sẽ không được skill giúp, vì curator chưa từng nhìn thấy nó. Check kỹ thuật sẽ giữ nguyên ở mức cao như `baseline`. Căn cứ: ở tác vụ học (đã thực hiện trước khi viết giả thuyết), `skills-auto` đạt 26/27 so với `baseline` 18/27 và `skills_read` = 1 ở cả 3 lần, nên tác tử có đọc và làm theo skill. Mặt trái: SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi, nên tôi dự đoán lợi ích nhỏ hơn mức 0,30 thấy ở tác vụ học, và có rủi ro skill bị bỏ qua hoặc làm sai ở tác vụ khác tên tệp.
- H3 (tác vụ học so với tác vụ đánh giá): Mức cải thiện của `skills-auto` trên tác vụ đánh giá sẽ **nhỏ hơn** mức cải thiện trên tác vụ học (học: +0,30 điểm trung bình, từ 18/27 lên 26/27; đánh giá: dự đoán +0,10 đến +0,20), tức có một phần quá khớp. Căn cứ: SkillEvolBench ghi nhận lợi ích trên tác vụ học thường không chuyển sang tác vụ mới; skill `tabular-data-deliverables` chép tên tệp `answer.json`, `clean.csv` và thứ tự cột của tác vụ học; skill `typed-package-bugfixes` chỉ yêu cầu chú thích hàm "you add or modify"; và ở data-learn tác tử đã làm theo đề thay vì skill ở trường `north_q1_revenue` ("number" so với số nguyên cent), một kiểu thất bại sẽ lặp lại ở tác vụ mới. Tác vụ học còn có ưu thế vì skill được viết từ chính phản hồi của nó.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute` và `task`. Chỉ `execute` cho phép chạy lệnh shell (và chỉ hoạt động khi backend hỗ trợ chạy lệnh, ở đây là `LocalShellBackend`).
2. Mô tả của `task` nói `general-purpose` là tác tử đa dụng để nghiên cứu, tìm tệp/nội dung và thực hiện tác vụ nhiều bước, "has access to all tools as the main agent". Mỗi lần gọi tạo một subagent tạm thời, không giữ trạng thái: "the agent sees only the prompt you give it and returns a single final report". Nó không thấy hội thoại hay ngữ cảnh của tác tử chính, nên tác tử chính phải đưa đủ thông tin vào prompt giao việc.
3. Từ `task`: "Put full detail in the prompt and state exactly what it should return". Từ `execute`: "You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail." (System prompt mặc định in ra là chuỗi rỗng `''`, nên hành vi mặc định chỉ đến từ mô tả công cụ.)

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | `RULE: every public function ... has type annotations on all parameters and on the return value.` Đề chỉ nói "checked ... against the Acme Python team conventions", không nêu quy tắc. |
| code-learn | `rule_regression_tests` | E | `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3)`. Vết: tác tử sửa 3 file nguồn, chạy `pytest` đạt, không tạo file test mới. |
| code-learn | `rule_changelog` | E | `RULE: record each fix in CHANGELOG.md under '## Unreleased' as '- fix(<function name>): ...'`. Vết không có lệnh đọc hay sửa `CHANGELOG.md`. |
| data-learn | `rule_money_in_cents` | E | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)`. Vết: `'north_q1_revenue': float(sum(...))`, tức số thực USD, đúng với đề ghi "number". Tác tử còn `grep "Acme"` trong workspace để tìm quy ước nhưng không có kết quả. |
| data-learn | `rule_meta_block` | E | `RULE: answer.json has an object meta = {source, rows_in, rows_used}`. `answer.json` chỉ có 5 khóa theo đề. |
| data-learn | `rule_clean_csv` | E | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents ...`. Tệp không được tạo. |
| logs-learn | `rule_service_names` | E | `RULE: service names ... lower-case with '-' replaced by '_' (payment-service -> payment_service)`. Vết: script ghi `'service': service` nguyên văn từ log (`inventory-service`), đúng như ví dụ `payment-service` trong đề. |
| logs-learn | `rule_sorted_errors` | E | `RULE: errors is sorted by service, then by timestamp_utc, ascending`. Vết: `errors.append(item)` theo thứ tự đọc log, không có bước `sort`. |
| logs-learn | `rule_schema_header` | E | `RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage"`. Đề không nhắc hai khóa này. |

Số liệu từ `python scripts/check_breakdown.py` (baseline, tác vụ học): **check kỹ thuật 18/18 đạt, check quy ước 0/9 đạt**. Đây là bằng chứng phủ định cho các nhóm A, B, C, D, F: không có check kỹ thuật nào thất bại (parse giá, làm tròn half-up, quoting CSV, loại dòng trùng, giá trị -999, múi giờ, `repeat_count`, tổng theo dịch vụ đều đúng). Vết cũng cho thấy tác tử đọc README/docstring trước khi làm (nhóm A không xuất hiện) và chạy `pytest` hoặc script kiểm tra lại (nhóm B không xuất hiện ở code-learn). Câu trả lời cuối của 3 lần chạy chỉ nêu tệp thực sự tạo hoặc sửa (nhóm F không xuất hiện).

Nhận xét: nhóm **E chiếm 9/9 lỗi (100%)**. Nguyên nhân chung: mô hình làm đúng mọi điều đề nói rõ, nhưng quy ước của tổ chức Acme không nằm trong đề hay workspace. Ở điều kiện `subagents`, explorer đọc README rồi báo "gives no Acme-specific report specification ... There is therefore no documented basis for claiming an exact Acme reporting convention" và implementer dặn thêm "don't invent extra output fields", tức tác tử cố ý không bịa quy ước. Kiến thức này chỉ học được từ phản hồi `detail`, nên một skill do curator viết từ `detail` có thể phòng ngừa nhóm E ở tác vụ cùng loại, với điều kiện quy ước của tác vụ mới trùng. Nhưng skill không thể tạo ra quy ước **mới** chưa từng thấy.

Lưu ý (xem mục 9): lần chạy đầu tiên của tôi bị bỏ vì repo trên Windows bị `core.autocrlf=true` đổi `tasks/` sang CRLF, khiến `tests_not_modified` thất bại giả và có thể làm sai dữ liệu. Đã đặt `core.autocrlf=false`, khôi phục `tasks/` về đúng bản LF trong git rồi chạy lại toàn bộ; mọi số liệu trong báo cáo đến từ các lần chạy sau khi sửa.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (`src/lab/subagents.py`):
  - `explorer`: chỉ đọc (README, docstring, changelog, mẫu dữ liệu) và báo cáo quy tắc, định dạng, quy ước, dữ liệu bẩn; không sửa tệp. `description` bắt đầu bằng "Use FIRST, before changing anything".
  - `implementer`: thực hiện thay đổi, sửa nguyên nhân gốc, chạy lại test/script, chỉ báo cáo tệp thật sự đã đổi. `description` yêu cầu đưa MỌI quy tắc và đường dẫn vào lời giao việc.
  - `reviewer`: kiểm tra độc lập từng quy tắc và trường hợp biên, trả về PASS/FAIL kèm bằng chứng; không sửa tệp. `description` bắt đầu bằng "Use LAST".
  - Lý do thiết kế: tách đọc / làm / kiểm tra thành 3 vai trò có phạm vi rõ ràng, nhằm ngăn lỗi bỏ qua đặc tả (A) và không kiểm chứng (B). Tôi dùng `description` dạng chỉ dẫn hành động và quy định "chỉ đọc" ở `system_prompt`; `PATHS_NOTE` được `build_agent` nối thêm.
- `subagent_calls` (luồng chính, `results/subagents/*/run.json`):

| Tác vụ | `subagent_calls` | Subagent được gọi | Điểm | token (baseline → subagents) | giây (baseline → subagents) |
|---|---|---|---|---|---|
| code-learn | 4 | explorer, implementer, reviewer, reviewer | 7/10 → 7/10 | 67 293 → 213 776 (3,2x) | 53,7 → 259,2 |
| data-learn | 2 | explorer, implementer | 5/8 → 5/8 | 27 211 → 84 904 (3,1x) | 28,2 → 111,6 |
| logs-learn | 2 | explorer, reviewer | 6/9 → 6/9 | 26 593 → 97 524 (3,7x) | 18,1 → 106,0 |

  Cả 3 lần chạy đều có giao việc (không có trường hợp bằng 0). Tác tử chính làm theo `SUBAGENTS_NOTE` ("delegate ... for anything beyond a trivial step"). Ở logs-learn tác tử chính tự viết `errors.json` và chỉ nhờ reviewer kiểm tra; ở data-learn implementer tạo `answer.json`.
- Thông tin truyền đi:
  - Thừa/đủ: lời giao việc cho `implementer` rất đầy đủ. Ví dụ data-learn (1 269 ký tự) chép lại gần hết quy tắc từ README (loại dòng trùng, `-999` là thiếu, múi giờ, cửa sổ Q1) và các khóa bắt buộc, đúng yêu cầu "put ALL the task rules". Lời giao cho explorer/reviewer ngắn (178 đến 447 ký tự) nhưng chỉ cần chỉ đường dẫn, vì chúng tự đọc tệp.
  - Thiếu: không có quy ước Acme trong lời giao việc, vì chính explorer báo "gives no Acme-specific report specification ... no documented basis" và implementer được dặn "don't invent extra output fields". Reviewer ở code-learn được nhắc "likely Acme Python convention issues" nhưng không biết quy tắc cụ thể, nên không bắt được `rule_type_hints`, `rule_regression_tests`, `rule_changelog`.
  - Kiểm tra báo cáo subagent: ở code-learn tác tử chính gọi reviewer lần 2 để xác minh các lỗi lần 1 đã sửa, tức có kiểm tra trước khi dùng.
- Ảnh hưởng đến token và thời gian: token trung bình 40 365 (baseline) → 132 068 (subagents), gấp **3,3 lần**; thời gian tăng 4,0 đến 5,9 lần (ví dụ 53,7 s → 259,2 s). Điểm không đổi ở cả 3 tác vụ (đúng 7/10, 5/8, 6/9), vì các check kỹ thuật đã đạt hết ở baseline và 9 check quy ước thất bại cùng 9 chỗ. Vết `trace.md` chỉ có luồng chính, nên việc subagent làm bên trong không hiện ra; tổng token vẫn đủ nhờ `UsageMetadataCallbackHandler`.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: **1** (`python -m lab.curator`, nguồn `results/baseline`, 3 tác vụ học, `max_skills=3`). Số skill bị xóa: **0**. Không chạy lại curator và không sửa tay skill nào. Lý do giữ nguyên: cả 3 skill hợp lệ theo `validate_skill`, đúng với phản hồi `detail`, và không chứa tên tác vụ đánh giá. Các khiếm khuyết bên dưới là khiếm khuyết thật của đầu ra curator và được ghi lại làm dữ liệu, không phải để sửa.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `log-triage-json` | Khá tổng quát về quy trình (đọc schema, xử lý dòng nối tiếp và dòng lặp, tự kiểm tra), nhưng bước 3 đến 5 nêu thẳng các quy ước Acme của tác vụ học: tên dịch vụ `lower_snake`, sắp xếp theo dịch vụ rồi thời gian, `schema_version: 2`, `generated_by: log-triage`. Các quy ước này được phép vì chúng là chính quy tắc (`05_skill_quality.md` mục 3), nhưng chỉ có ích nếu tác vụ mới dùng cùng quy ước. | Đúng: khớp từng dòng `RULE:` trong `detail` của 3 check `rule_` của logs-learn. Lỗi nhỏ: dòng cuối file là `=== END===` (thiếu dấu cách) nên không bị tách khỏi nội dung và lọt vào thân skill; vô hại nhưng là rác từ đầu ra curator. | 15 dòng. `description` "Use when parsing application logs into structured JSON error-triage reports" nêu đúng tình huống nhưng hẹp ở "error-triage". `skills_read` = 1 ở logs-learn; tác tử đọc `/skills/log-triage-json/SKILL.md` ngay bước đầu và đạt 9/9. |
| `tabular-data-deliverables` | Một nửa tổng quát (đọc yêu cầu, dùng decimal, loại dòng trùng theo khóa, tự kiểm tra), một nửa là chi tiết của tác vụ học: bước 5 và 6 chép tên `answer.json`, `meta`, `clean.csv` và đúng thứ tự cột `order_id,timestamp_utc,region,amount_cents`. Đây là quy ước Acme nên hợp lệ, nhưng nguy cơ quá khớp cao: nếu tác vụ mới đặt tên tệp khác, hướng dẫn này sai chỗ. | Đúng với `detail`. Có một chỗ thiếu: bước 2 dặn đổi sang cent "wherever cents are required" nhưng không nói rõ trường `north_q1_revenue` mà đề ghi là "number" cũng phải là cent. Chính chỗ mơ hồ này gây thất bại ở Phần 3.4. | 16 dòng. `description` "Use when cleaning order-like CSV data and producing structured summaries or cleaned-data artifacts" rộng vừa phải. `skills_read` = 1 ở data-learn; tác tử làm theo `meta` và `clean.csv` (2/3 check quy ước đạt) nhưng vẫn ghi `north_q1_revenue: 3130.24` (số thực) vì đề nói "number", nên `rule_money_in_cents` thất bại (7/8). Đúng kiểu thất bại "đề nói khác thì tác tử làm theo đề" mô tả ở `05_skill_quality.md` mục 5. |
| `typed-package-bugfixes` | Tổng quát nhất về quy trình (checklist, một test cho mỗi lỗi, một bullet changelog cho mỗi lỗi), nhưng bước 4 và 5 cũng chép quy ước Acme của tác vụ học (`tests/test_regressions.py`, `## Unreleased`, `fix(<function name>)`). | Đúng một phần. (1) Bước 3 chỉ yêu cầu chú thích kiểu cho hàm công khai "you add or modify", hẹp hơn quy tắc gốc "every public function in the package", nên một hàm công khai không bị sửa vẫn có thể thiếu chú thích. (2) Bước 7 ("Inspect the changed files directly if a preferred diff tool is unavailable") là nhiễu lấy từ việc `git diff` không chạy được trong sandbox, không phải quy tắc. | 15 dòng. `description` "Use when fixing bugs in a typed Python package with repository-level testing and changelog requirements" nêu đúng tình huống nhưng chứa "typed" và "changelog" có thể làm tác tử bỏ qua ở tác vụ không có hai yếu tố này. `skills_read` = 1 ở code-learn; tác tử đọc skill trước tiên, tạo `tests/test_regressions.py` và thêm bullet vào `CHANGELOG.md`; đạt 10/10 (cả `rule_type_hints`). |

Kết quả Phần 3.4 (tác vụ học, **skills-auto, trước đóng băng**, lưu ở `results/skills-auto-dev/`): code-learn 10/10, data-learn 7/8, logs-learn 9/9; tổng 26/27 (baseline 18/27). `skills_read` = 1 ở cả 3 lần; mỗi lần tác tử chỉ đọc đúng skill khớp với họ tác vụ, không đọc skill của họ khác. `skills_modified` = false ở cả 3 lần.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Bảng từ `python -m lab.compare` (cũng có trong `report/table.md`). Cột `skills-auto` ở hàng tác vụ học là lần chạy **sau đóng băng**; lần chạy trước đóng băng (Phần 3.4) nằm ở `results/skills-auto-dev/`.

```text
| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 10/10 |
| data-learn | 5/8 | 5/8 | 7/8 |
| logs-learn | 6/9 | 6/9 | 9/9 |
| code-eval | 7/11 | 7/11 | 9/11 |
| data-eval | 5/9 | 4/9 | 5/9 |
| logs-eval | 6/10 | 1/10 | 9/10 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.96 |
| **Mean score - evaluation tasks** | 0.60 | 0.39 | 0.76 |
| **Mean tokens per run** | 40,481 | 133,275 | 62,360 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |
```

Kết quả `python scripts/check_breakdown.py` (technical = check kỹ thuật; house rules = check `rule_`):

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          40,597      0/3
baseline      learn    18/18         0/9           40,365      0/3
subagents     eval     12/18         0/12         134,483      0/3
subagents     learn    18/18         0/9          132,068      0/3
skills-auto   eval     18/18         5/12          63,285      3/3
skills-auto   learn    18/18         8/9           61,436      3/3
```

Các check `rule_` của tác vụ đánh giá gồm 9 check dùng lại từ tác vụ học và 3 check **mới** (`rule_version_bump` ở code-eval, `rule_sorted_keys_format` ở data-eval, `rule_source_line` ở logs-eval). Check đạt của `skills-auto` ở tác vụ đánh giá:

| Tác vụ đánh giá | Quy ước dùng lại, đạt/tổng | Quy ước mới | Check kỹ thuật |
|---|---|---|---|
| code-eval | 2/3 (`rule_regression_tests`, `rule_changelog` đạt; `rule_type_hints` không) | `rule_version_bump` không đạt | 7/7 |
| data-eval | 0/3 | `rule_sorted_keys_format` không đạt | 5/5 |
| logs-eval | 3/3 | `rule_source_line` không đạt | 6/6 |

Lần chạy có `error` hoặc `skills_modified = true`: **không có** (`error` là `null` và `skills_modified` là `false` ở cả 21 lần chạy hợp lệ). `python scripts/verify_freeze.py` báo `checked 6 runs of skill conditions: OK`. Lần đầu script báo `skills/ differs from the freeze tag`: nguyên nhân là `skills/auto/README.md` còn ở dạng CRLF trong working tree (di sản của `autocrlf=true`) trong khi blob git là LF, nội dung giống hệt; sau khi đổi về LF thì báo OK. Nội dung 3 skill không đổi từ lúc đóng băng.

## 8. Phân tích

1. **Cải thiện so với `baseline`.**
   - `skills-auto` cải thiện cả hai: tác vụ học 0,66 → 0,96 (+0,30), tác vụ đánh giá 0,60 → 0,76 (+0,16).
   - `subagents` không cải thiện tác vụ học (0,66 → 0,66) và làm **giảm** tác vụ đánh giá (0,60 → 0,39, −0,21). Mức giảm gần như toàn bộ do một lần chạy (logs-eval 1/10 so với 6/10); code-eval giữ 7/11 và data-eval giảm 5/9 → 4/9.
   - Không có điều kiện nào cải thiện tác vụ học mà không cải thiện tác vụ đánh giá, nhưng mức tăng của `skills-auto` ở tác vụ đánh giá chỉ bằng khoảng một nửa mức ở tác vụ học (+0,16 so với +0,30), và ở data-eval **không tăng** (5/9 → 5/9) dù data-learn tăng 5/8 → 7/8. Đây là dấu hiệu quá khớp một phần (skill chép quy ước và chi tiết của tác vụ học, xem câu 5), khớp với H3. Với H2, `skills-auto` đúng là điều kiện cao nhất và mức tăng +0,16 nằm trong khoảng dự đoán 0,10 đến 0,20. H1 đúng một nửa: không cải thiện và token gấp 3,3 lần như dự đoán, nhưng điểm giảm 0,21 lớn hơn ngưỡng ±0,05 tôi đã đặt.
2. **Check kỹ thuật so với check quy ước (tác vụ đánh giá).**
   - Check kỹ thuật: `baseline` 18/18, `skills-auto` 18/18, `subagents` 12/18. Skill không giúp được gì ở nhóm này vì `baseline` đã đạt tối đa (hiệu ứng trần).
   - Check quy ước: `baseline` 0/12, `subagents` 0/12, `skills-auto` 5/12. Toàn bộ khoảng cách điểm của `skills-auto` nằm ở nhóm `rule_`.
   - Trong 9 check quy ước dùng lại từ tác vụ học, `skills-auto` đạt 5/9 (code-eval 2/3, data-eval 0/3, logs-eval 3/3). Trong 3 check quy ước **mới** (`rule_version_bump`, `rule_sorted_keys_format`, `rule_source_line`) đạt **0/3**. Lý do: curator chỉ nhìn thấy phản hồi `detail` của tác vụ học, và `detail` nêu từng quy ước một cách tường minh; ba quy ước mới không xuất hiện trong bất kỳ phản hồi nào nên không có trong skill, và tác tử cũng không tự suy ra (đề chỉ nói chung "plus whatever the Acme ... conventions require", mà workspace không ghi quy ước). Ví dụ: `rule_version_bump` ở code-eval đòi `__version__` tăng patch lên `1.4.3`, và check không đạt.
3. **Một check skill giúp, một check skill không giúp.**
   - Giúp: logs-eval `rule_service_names`, `rule_sorted_errors`, `rule_schema_header`. `baseline` trượt cả ba (0/3); `skills-auto` đạt cả ba. Vết: lời gọi công cụ đầu tiên là `read_file skills/log-triage-json/SKILL.md` (`skills_read` = 1), sau đó script parse chứa `replace('-', '_')`, `sort(`, `"schema_version": 2` và `"generated_by": "log-triage"`, đúng các bước 3 đến 5 của skill. Cùng lần chạy chỉ trượt `rule_source_line` (quy ước mới).
   - Không giúp, đọc nhưng không làm theo: data-eval `rule_money_in_cents`. Tác tử đọc cả 3 skill (`skills_read` = 3) nhưng `answer.json` ghi `"march_revenue_utc": 52957.19` (số thực), vì đề nói "(number)"; đây đúng là kiểu thất bại đã gặp ở data-learn (Phần 3.4) và đã mô tả ở `05_skill_quality.md` mục 5. Tương tự `rule_meta_block`: `meta.rows_in` = 88 và `meta.rows_used` = 76 đúng, nhưng `meta.source` = `"workspace/orders.json"` (đường dẫn) thay vì tên tệp `orders.json`, vì skill chỉ viết "`source`" mà không định nghĩa. Và `rule_clean_csv`: vết không có lệnh ghi `clean.csv`, tức bước 6 của skill bị bỏ qua. Ngay cả khi ghi, header cứng `order_id,timestamp_utc,region,amount_cents` của skill sẽ sai vì cột của tác vụ này là `category` (xem câu 5).
   - Skill hẹp hơn quy tắc: code-eval `rule_type_hints` trượt dù skill được đọc. Skill chỉ yêu cầu chú thích hàm "you add or modify"; vết cho thấy tác tử chú thích các hàm nó sửa (`billable_blocks`, `parse_duration`) và quy tắc gốc đòi mọi hàm công khai.
4. **Chi phí.** Token trung bình mỗi lần chạy: `baseline` 40 481, `skills-auto` 62 360 (1,54 lần), `subagents` 133 275 (3,29 lần).

   | Điều kiện | Điểm trung bình (6 tác vụ) | Token TB | Điểm trên 100 nghìn token | Điểm trung bình tác vụ đánh giá |
   |---|---|---|---|---|
   | baseline | 0,63 | 40 481 | 1,56 | 0,60 |
   | skills-auto | 0,86 | 62 360 | 1,38 | 0,76 |
   | subagents | 0,53 | 133 275 | 0,39 | 0,39 |

   `baseline` có điểm trên token cao nhất (rẻ nhất) nhưng điểm tuyệt đối thấp hơn `skills-auto`; `skills-auto` tốn thêm 54% token (đọc 1 đến 3 skill trước rồi mới làm, thêm lời gọi công cụ, ví dụ code-eval 28 so với 22 lần gọi) lấy +0,16 đến +0,30 điểm nên là điểm cân bằng tốt nhất. Đa tác tử **không đáng** trong thí nghiệm này: gấp 3,3 lần token và 4 đến 6 lần thời gian mà không tăng điểm học, giảm điểm đánh giá. Cơ chế của mức giảm ở logs-eval (1/10): explorer đọc log và trả về một bảng các mục lỗi; tác tử chính cũng đọc log rồi ghi tay `errors.json` (23 mục theo câu trả lời cuối) bằng `write_file` mà không viết script parse (`baseline` và `skills-auto` đều chạy một script Python để parse), rồi chỉ "kiểm chứng" bằng cách cộng `repeat_count` so với `counts_by_service` do chính nó viết, không đối chiếu với log. Kết quả sai ở 5 check kỹ thuật (`entry_count`, `timestamps_utc`, `levels_uppercase`, `repeat_counts`, `counts_by_service`). Ở data-eval, lời giao việc cho reviewer có câu "verify March order count includes all distinct orders in UTC March even if total is missing", khác với cách hiểu của đề ("distinct orders counted in `march_revenue_utc`"), và `march_orders_utc` là check kỹ thuật duy nhất trượt ở lần chạy này (`skills-auto` và `baseline` đạt check này). Đây là một cách diễn giải lại yêu cầu khi đi qua subagent, nhưng vì chỉ một lần chạy nên tôi không khẳng định đây là nguyên nhân chắc chắn.
5. **Rò rỉ và quá khớp.**
   - Rò rỉ: không thấy. `curate_skills` chỉ đọc lần chạy có `role == "learn"` và có test; `validate_skill` loại skill chứa định danh của tác vụ đánh giá; tôi grep 3 skill với `orders.json`, `worker.log`, `bookings`, `march`, `category`, `__version__` và không có kết quả; giả thuyết được commit trước tag `freeze` và tôi không mở `check.py` hay kết quả của tác vụ đánh giá trước khi đóng băng; `verify_freeze.py` báo OK.
   - Quá khớp: có. `tabular-data-deliverables` ghi cứng tên `answer.json`, `clean.csv` và header `order_id,timestamp_utc,region,amount_cents` của tác vụ học; tác vụ đánh giá dùng cột `category`, nên một tác tử làm đúng skill sẽ ghi sai header. Kết quả: `skills-auto` đạt 0/3 check quy ước dùng lại ở data-eval và không tăng điểm ở tác vụ này. Các skill còn lại cũng ghi quy ước cụ thể (`tests/test_regressions.py`, `schema_version: 2`), có ích chỉ vì tác vụ đánh giá cố ý dùng lại chúng.
   - Biện pháp: các guardrail ở trên; không sửa tay skill; curator chỉ chạy một lần. Tôi không xóa skill quá khớp vì quy ước của lab cho phép chỉ xóa skill kém hoặc có hại, và bằng chứng quá khớp chỉ thấy sau khi đóng băng.
6. **Nhiễu.** Cùng bộ 3 skill, tác vụ học, trước đóng băng (Phần 3.4, `results/skills-auto-dev/`) so với sau đóng băng:

   | Tác vụ | Điểm 3.4 → sau freeze | Token 3.4 → sau freeze | Số lần gọi công cụ |
   |---|---|---|---|
   | code-learn | 10/10 → 10/10 | 111 404 → 121 348 (+9%) | 28 → 25 |
   | data-learn | 7/8 → 7/8 | 44 237 → 34 571 (−22%) | 7 → 8 |
   | logs-learn | 9/9 → 9/9 | 18 337 → 28 390 (+55%) | 4 → 5 |

   Điểm chênh **0** (cùng 0,96 trung bình, cùng check thất bại ở data-learn), nhưng token dao động −22% đến +55% giữa hai lần chạy giống hệt. Điều này cho biết: điểm tác vụ học của `skills-auto` khá ổn định trong lần lặp duy nhất này, song chỉ 3 cặp mẫu nên không ước lượng được phương sai; tỉ lệ token 1,54 lần của `skills-auto` so với `baseline` chỉ lớn hơn một chút so với dao động từng lần chạy, trong khi 3,3 lần của `subagents` lớn hơn nhiều. Chênh lệch một check (0,09 đến 0,11 điểm của một tác vụ) không đáng tin; chênh lệch của `skills-auto` so với `baseline` (+0,16 trung bình, cùng chiều ở 2/3 tác vụ đánh giá và 3/3 tác vụ học) đáng tin hơn, còn mức giảm của `subagents` (từ một lần chạy) thì không.

## 9. Hạn chế và tính hợp lệ

1. **Số mẫu rất nhỏ, mỗi ô chạy một lần.** Có 3 tác vụ đánh giá và mỗi (điều kiện, tác vụ) chỉ chạy một lần, với `temperature=1`. Một check chênh lệch bằng 0,09 đến 0,11 điểm của một tác vụ; điểm trung bình của một điều kiện có thể đổi hơn 0,1 chỉ vì một lần chạy xấu. Ảnh hưởng: mức giảm 0,21 của `subagents` đến từ một lần chạy (logs-eval 1/10) nên không thể phân biệt với nhiễu; chỉ kết luận về token (gấp 3,3 lần, nhất quán ở cả 6 tác vụ) là chắc chắn. Kết luận về `skills-auto` (+0,16) cũng chỉ ở mức gợi ý.
2. **Chỉ đo nhiễu bằng 3 cặp lặp.** Ở câu 6 mục 8 tôi chỉ có 3 cặp (cùng skill, tác vụ học) và không lặp lại tác vụ đánh giá, nên không tính được khoảng dao động. Điểm giống nhau ở cả 3 cặp không chứng minh điểm ổn định; token đã dao động −22% đến +55%. Ảnh hưởng: hạn chế khả năng nói về độ tin cậy của chênh lệch điểm; hướng 6e (lặp lại ít nhất 2 lần) sẽ giải quyết, nhưng tôi không làm.
3. **Tác vụ do giảng viên thiết kế, có sẵn quy ước và có chủ ý dùng lại.** Điểm "quy ước" là các quy tắc tùy ý của "Acme", và 9/12 check quy ước ở tác vụ đánh giá là quy ước dùng lại từ tác vụ học, được nêu nguyên văn trong `detail`. Việc skill "học" được chúng gần như là sao chép phản hồi, không phải khám phá. Check kỹ thuật đã đạt trần (18/18) ở `baseline` nên không cho thấy được tác động của skill hay subagent lên chất lượng kỹ thuật. Ảnh hưởng: kết quả `skills-auto` có thể chỉ phản ánh việc nhớ quy ước, và không suy rộng cho tác vụ có quy ước chưa từng thấy (đúng như 0/3 check mới).
4. **Chỉ một mô hình, và cùng mô hình viết skill và thực thi.** Dùng `gpt-6-luna` cho cả curator, tác tử chính và subagent, với `temperature=1` bắt buộc. Ảnh hưởng: kết luận (đặc biệt về hành vi "đọc skill rồi làm theo đề") có thể không chuyển sang mô hình khác; không so sánh được skill do mô hình mạnh hơn viết.
5. **Chỉ một lần chạy curator và thiết kế subagent do tôi chọn.** Curator ngẫu nhiên: một lần chạy khác có thể cho skill tốt hơn hoặc xấu hơn (bước 3 của skill `typed-package-bugfixes` hẹp hơn quy tắc gốc, một khiếm khuyết có thể không xảy ra ở lần khác). Cấu hình 3 subagent (explorer, implementer, reviewer) là một lựa chọn trong nhiều; một thiết kế khác (ví dụ ép subagent viết script rồi chạy) có thể không gặp lỗi chép tay của logs-eval. Ảnh hưởng: kết luận "đa tác tử không đáng" chỉ đúng cho thiết kế này. Ngoài ra `trace.md` không chứa việc subagent làm bên trong nên cơ chế lỗi của subagent chỉ suy ra được từ lời giao việc và kết quả.
6. **Sai lệch môi trường đã phát hiện.** Lần chạy đầu bị loại vì CRLF (mục 4). Điều này cho thấy kết quả nhạy với chi tiết môi trường; tôi đã kiểm chứng sau khi sửa (`git ls-files --eol`, `verify_freeze.py` OK), nhưng không thể loại trừ hoàn toàn các khác biệt tương tự khác. `final_message` trong `run.json` là chuỗi `repr` của các khối nội dung vì mô hình trả về khối kiểu Responses API; không ảnh hưởng điểm (chấm trên tệp), chỉ ảnh hưởng độ dễ đọc.

## 10. Kết luận

`skills-auto` đạt điểm trung bình cao nhất trên tác vụ đánh giá (0,76 so với 0,60 của `baseline` và 0,39 của `subagents`) với 1,54 lần token của `baseline`, nhưng toàn bộ mức tăng đến từ các quy ước dùng lại từ tác vụ học (5/9 đạt) và không có quy ước mới nào được giúp (0/3). Mức tăng ở tác vụ đánh giá (+0,16) chỉ bằng khoảng một nửa mức ở tác vụ học (+0,30), và ở data-eval skill không tăng điểm vì quá khớp (cột `category` so với `region` đã ghi cứng) và tác tử làm theo đề thay vì skill ở trường tiền. `subagents` tốn gấp 3,3 lần token mà không tăng điểm học và giảm điểm đánh giá (nhưng từ một lần chạy duy nhất, nên chưa thể khẳng định). Với 3 tác vụ mỗi vai trò, một lần chạy mỗi ô, một mô hình và `temperature=1`, chênh lệch một check không đáng tin. Đề xuất tiếp theo: bắt curator tách quy trình tổng quát khỏi tên tệp và cột cụ thể (tham số hóa theo đề bài) và thêm một bước "tìm quy ước còn thiếu", rồi lặp lại tác vụ đánh giá nhiều lần để đo nhiễu (hướng 6e).

## Phụ lục

- Lệnh đã chạy (theo thứ tự, trong container `docker run --rm --env-file .env -v "$PWD:/lab" lab-deepagents ...`):
  1. `docker build -t lab-deepagents .`; `pytest tests` (29 test đạt); `python scripts/tour.py`.
  2. Kiểm tra mô hình, rồi `python -m lab.runner --condition baseline --tasks data-learn` (lần đầu).
  3. Phát hiện lỗi CRLF: `git config --local core.autocrlf false`, khôi phục `tasks/`, `scripts/`, `tests/` từ git; xóa kết quả cũ.
  4. `python -m lab.runner --condition baseline --tasks learn`; `python -m lab.runner --condition subagents --tasks learn`.
  5. `python -m lab.curator`; `python -m lab.runner --condition skills-auto --tasks learn`; `mv results/skills-auto results/skills-auto-dev`.
  6. Điền giả thuyết (mục 2); `git commit` (`hypotheses`); `git commit --allow-empty` + `git tag freeze`.
  7. `python -m lab.runner --condition baseline --tasks eval`; `... --condition subagents --tasks eval`; `... --condition skills-auto --tasks all`.
  8. `python scripts/verify_freeze.py` (OK); `python -m lab.compare > report/table.md`; `python scripts/check_breakdown.py`.
- Thử thách mở rộng: không thực hiện.
- Ghi chú khác:
  - Lỗi CRLF: `core.autocrlf=true` của Git for Windows đổi `tasks/**` sang CRLF; `check.py` của `code-learn` so băm SHA-256 của tệp test (tính trên bản LF) nên `tests_not_modified` thất bại với mọi lần chạy, và CRLF có thể làm sai dữ liệu log và CSV. Kết quả của lần chạy đầu bị loại và xóa; mọi số liệu trong báo cáo đến từ lần chạy lại sau khi `tasks/` khớp với git (`git ls-files --eol tasks`: `i/lf w/lf`, ngoại trừ `sales.csv` vốn là CRLF trong git).
  - Image phụ có git: `FROM lab-deepagents` + `apt-get install git` (chỉ để chạy `verify_freeze.py` và `check_breakdown.py`, không đưa vào kho).
  - Tôi không sửa `tests/`, `tasks/`, `scripts/` hay các tệp có sẵn; không sửa tay `skills/auto/*/SKILL.md`. `skills/auto/README.md` chỉ được đổi line ending CRLF → LF (nội dung không đổi) để trùng blob git.
