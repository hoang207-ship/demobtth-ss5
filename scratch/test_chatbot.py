from streamlit.testing.v1 import AppTest

at = AppTest.from_file("../app.py", default_timeout=120)
at.run()
assert not at.exception, at.exception

# 1. Click quick-prompt "Bước tiếp theo?" when not connected
[b for b in at.button if b.key == "ai_q1"][0].click().run()
assert not at.exception, at.exception
assert len(at.session_state["chat_history"]) >= 3
assert "chưa nạp dữ liệu" in at.session_state["chat_history"][-1]["content"].lower()

# 2. Load standard 3-tab sample, run clean + 6 steps, ask KPI & exceptions
[b for b in at.button if b.key == "qs_std"][0].click().run()
[b for b in at.button if b.key == "ov_run_all"][0].click().run()
assert not at.exception, at.exception

[b for b in at.button if b.key == "ai_q2"][0].click().run()
assert not at.exception, at.exception
kpi_reply = at.session_state["chat_history"][-1]["content"]
assert "Doanh thu phân bổ" in kpi_reply and "Net Sales" in kpi_reply, kpi_reply

[b for b in at.button if b.key == "ai_q3"][0].click().run()
assert not at.exception, at.exception
exc_reply = at.session_state["chat_history"][-1]["content"]
assert "Ngoại lệ chờ duyệt" in exc_reply, exc_reply

# 3. Ask open general-knowledge / ChatGPT brain question via ai_chat_form
chat_in = [ti for ti in at.text_input if ti.label == "Hỏi Trợ lý AI..."][0]
chat_in.input("Thủ đô của Nhật Bản là gì? Trả lời ngắn gọn.")
send_btn = [b for b in at.button if "Gửi câu hỏi" in str(b.label)][0]
send_btn.click().run()
assert not at.exception, at.exception
gen_reply = at.session_state["chat_history"][-1]["content"]
assert len(gen_reply.strip()) > 0
print("General Q reply:", gen_reply[:160])

# 4. Clear conversation
[b for b in at.button if b.key == "ai_clear"][0].click().run()
assert not at.exception, at.exception
assert len(at.session_state["chat_history"]) == 1

print("CHATBOT AI TESTS PASSED!")

