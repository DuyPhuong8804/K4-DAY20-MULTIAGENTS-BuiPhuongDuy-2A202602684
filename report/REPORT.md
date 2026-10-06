# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| | | |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`:
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker:
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline): `subagents` sẽ **không** cải thiện điểm tác vụ đánh giá so với `baseline` (chênh lệch điểm trung bình trong khoảng ±0,05, tức nằm trong nhiễu), và sẽ tốn khoảng 3 lần token trở lên. Căn cứ: ở tác vụ học, `baseline` và `subagents` đạt cùng 7/10, 5/8, 6/9; check kỹ thuật đã đạt 18/18 ở `baseline` nên không còn gì cho subagent cải thiện; 9/9 lỗi thuộc nhóm E (quy ước không có trong đề) và explorer chính nó báo "no documented basis" cho quy ước Acme, nên chia việc không tạo ra tri thức mới; token tăng 3,1 đến 3,7 lần. Phù hợp với bài báo hệ thống nghiên cứu đa tác tử của Anthropic (đa tác tử tốn nhiều token, khoảng 15 lần so với hội thoại thường) và với lưu ý của `02_subagents.md` rằng subagent không phù hợp cho tác vụ ít bước.
- H2 (skills-auto so với baseline): `skills-auto` sẽ đạt điểm **cao nhất** trên tác vụ đánh giá, nhưng chỉ cải thiện một phần: dự đoán điểm trung bình tăng khoảng 0,10 đến 0,20 so với `baseline`, không đạt 1,0. Toàn bộ mức tăng đến từ các check quy ước `rule_` mà tác vụ đánh giá dùng lại từ tác vụ học (đề bài nói tác vụ đánh giá dùng lại các quy ước của tác vụ học), vì 3 skill chép đúng các quy ước đó. Check quy ước **mới** của tác vụ đánh giá sẽ không được skill giúp, vì curator chưa từng nhìn thấy nó. Check kỹ thuật sẽ giữ nguyên ở mức cao như `baseline`. Căn cứ: ở tác vụ học (đã thực hiện trước khi viết giả thuyết), `skills-auto` đạt 26/27 so với `baseline` 18/27 và `skills_read` = 1 ở cả 3 lần, nên tác tử có đọc và làm theo skill. Mặt trái: SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi, nên tôi dự đoán lợi ích nhỏ hơn mức 0,30 thấy ở tác vụ học, và có rủi ro skill bị bỏ qua hoặc làm sai ở tác vụ khác tên tệp.
- H3 (tác vụ học so với tác vụ đánh giá): Mức cải thiện của `skills-auto` trên tác vụ đánh giá sẽ **nhỏ hơn** mức cải thiện trên tác vụ học (học: +0,30 điểm trung bình, từ 18/27 lên 26/27; đánh giá: dự đoán +0,10 đến +0,20), tức có một phần quá khớp. Căn cứ: SkillEvolBench ghi nhận lợi ích trên tác vụ học thường không chuyển sang tác vụ mới; skill `tabular-data-deliverables` chép tên tệp `answer.json`, `clean.csv` và thứ tự cột của tác vụ học; skill `typed-package-bugfixes` chỉ yêu cầu chú thích hàm "you add or modify"; và ở data-learn tác tử đã làm theo đề thay vì skill ở trường `north_q1_revenue` ("number" so với số nguyên cent), một kiểu thất bại sẽ lặp lại ở tác vụ mới. Tác vụ học còn có ưu thế vì skill được viết từ chính phản hồi của nó.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có 9 công cụ: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, `execute` và `task`. Chỉ `execute` cho phép chạy lệnh shell (và chỉ hoạt động khi backend hỗ trợ chạy lệnh, ở đây là `LocalShellBackend`).
2. Mô tả của `task` nói `general-purpose` là tác tử đa dụng để nghiên cứu, tìm tệp/nội dung và thực hiện tác vụ nhiều bước, "has access to all tools as the main agent". Mỗi lần gọi tạo một subagent tạm thời, không giữ trạng thái: "the agent sees only the prompt you give it and returns a single final report". Nó không thấy hội thoại hay ngữ cảnh của tác tử chính, nên tác tử chính phải đưa đủ thông tin vào prompt giao việc.
3. Từ `task`: "Put full detail in the prompt and state exactly what it should return". Từ `execute`: "You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail." (System prompt mặc định in ra là chuỗi rỗng `''`, nên hành vi mặc định chỉ đến từ mô tả công cụ.)

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
