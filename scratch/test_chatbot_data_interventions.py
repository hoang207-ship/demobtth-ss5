from streamlit.testing.v1 import AppTest


def send_chat(at: AppTest, prompt: str) -> str:
    """Nhập tin nhắn vào Chatbot trên UI và bấm Gửi yêu cầu."""
    ti = [t for t in at.text_input if "Hỏi hoặc ra lệnh cho Trợ lý AI" in str(t.label)][0]
    ti.input(prompt)
    submit = [b for b in at.button if "Gửi yêu cầu" in str(b.label)][0]
    submit.click().run()
    assert not at.exception, [e.message for e in at.exception]
    hist = at.session_state["chat_history"]
    assert hist[-2]["role"] == "user" and hist[-2]["content"] == prompt
    assert hist[-1]["role"] == "assistant"
    return hist[-1]["content"]


def test_chatbot_interventions_e2e():
    at = AppTest.from_file("../app.py", default_timeout=120).run()
    assert not at.exception, [e.message for e in at.exception]
    assert at.session_state["data_status"] == "NOT_CONNECTED"

    # 1. Nút nhanh ai_q1: "Làm sạch dữ liệu và chạy quy trình 6 bước ngay" (tự nạp dữ liệu + làm sạch + 6 bước)
    btn_q1 = [b for b in at.button if b.key == "ai_q1"][0]
    btn_q1.click().run()
    assert not at.exception, [e.message for e in at.exception]
    assert at.session_state["data_status"] == "CONNECTED"
    assert at.session_state["process_status"] == "COMPLETED"
    last_reply = at.session_state["chat_history"][-1]["content"]
    assert "Biên bản Can thiệp Dữ liệu Trực tiếp" in last_reply
    print("[PASS] 1. Quick button Làm sạch & Xử lý 6 bước qua Chatbot OK")

    # 2. Lệnh chat: Nạp dữ liệu lộn xộn và làm sạch ngay
    rep2 = send_chat(at, "Nạp dữ liệu lộn xộn và làm sạch ngay")
    assert "GiaHoa_Raw_Messy_TestCase_08" in at.session_state["source_name"]
    assert at.session_state["cleaning_status"] == "NEEDS_APPROVAL"
    assert at.session_state["process_status"] == "COMPLETED"
    assert "GiaHoa_Raw_Messy_TestCase_08" in rep2
    print("[PASS] 2. Chat 'Nạp dữ liệu lộn xộn và làm sạch ngay' OK")

    # 3. Câu hỏi tra cứu thụ động ("Giải thích ngoại lệ cần duyệt") KHÔNG được tự ý phê duyệt
    pending_before_q = len([e for e in at.session_state["exceptions_list"] if e.get("Approval_Status") == "PENDING_REVIEW"])
    rep_passive = send_chat(at, "Giải thích ngoại lệ cần duyệt")
    pending_after_q = len([e for e in at.session_state["exceptions_list"] if e.get("Approval_Status") == "PENDING_REVIEW"])
    assert pending_before_q == pending_after_q and pending_after_q > 0
    assert "Ngoại lệ chờ duyệt" in rep_passive
    print(f"[PASS] 3. Câu hỏi tra cứu giữ nguyên {pending_after_q} ngoại lệ (không kích hoạt nhầm hành động)")

    # 4. Lệnh chat: Sửa giá trị đơn ORD-2001 và đổi kênh -> kiểm tra Normalized_Transactions & Audit Log & Net Sales
    df_before = at.session_state["normalized_data"]["Normalized_Transactions"]
    old_val_2001 = float(df_before.loc[df_before["Order_ID"] == "ORD-2001", "Order_Value"].iloc[0])
    rep4 = send_chat(at, "Sửa đơn ORD-2001 giá trị 8000000 đổi kênh thành TikTok")
    df_after_edit = at.session_state["normalized_data"]["Normalized_Transactions"]
    row_2001 = df_after_edit.loc[df_after_edit["Order_ID"] == "ORD-2001"].iloc[0]
    assert float(row_2001["Order_Value"]) == 8000000.0 and old_val_2001 != 8000000.0
    assert row_2001["Channel"] == "TikTok Shop"
    assert any(a.get("Method") == "AI_CHAT_EDIT_ORDER" and a.get("Record_ID") == "ORD-2001" for a in at.session_state["audit_log"])
    assert "8,000,000 đ" in rep4
    print("[PASS] 4. Chat trực tiếp sửa đơn ORD-2001 (8,000,000 đ, TikTok Shop) + ghi Audit Log OK")

    # 5. Lệnh chat: Xóa đơn ORD-2002
    n_before_del = len(df_after_edit)
    rep5 = send_chat(at, "Xóa đơn ORD-2002")
    df_after_del = at.session_state["normalized_data"]["Normalized_Transactions"]
    assert len(df_after_del) == n_before_del - 1
    assert "ORD-2002" not in set(df_after_del["Order_ID"])
    assert "ORD-2002" in rep5
    print("[PASS] 5. Chat trực tiếp xóa đơn ORD-2002 khỏi dữ liệu chuẩn hóa OK")

    # 6. Lệnh chat: Xóa các dòng trùng lặp và loại bỏ các dòng lỗi
    rep6 = send_chat(at, "Xóa các dòng trùng lặp và loại bỏ các dòng lỗi")
    df_clean_deep = at.session_state["normalized_data"]["Normalized_Transactions"]
    assert df_clean_deep["Order_ID"].duplicated().sum() == 0
    assert "ORD-2007" not in set(df_clean_deep["Order_ID"])
    assert "ORD-2009" not in set(df_clean_deep["Order_ID"])
    assert any(a.get("Method") == "AI_CHAT_DEDUPLICATE" for a in at.session_state["audit_log"])
    assert any(a.get("Method") == "AI_CHAT_REMOVE_INVALID" for a in at.session_state["audit_log"])
    assert "loại bỏ" in rep6.lower()
    print("[PASS] 6. Chat trực tiếp xóa dòng trùng lặp & loại bỏ dòng lỗi OK")

    # 7. Lệnh chat: Duyệt tất cả ngoại lệ và chạy kiểm toán -> Verification PASS
    rep7 = send_chat(at, "Duyệt tất cả ngoại lệ và chạy kiểm toán")
    assert at.session_state["verification_status"] == "PASS", at.session_state["verification_result"]
    assert len([e for e in at.session_state["exceptions_list"] if e.get("Approval_Status") == "PENDING_REVIEW"]) == 0
    assert "PASS" in rep7
    print("[PASS] 7. Chat trực tiếp phê duyệt HITL & Verification PASS OK")

    # 8. Chuyển sang trang Data Cleaning & Audit (kiểm tra Chatbot xuất hiện ở mọi trang) & đổi Return Window
    at.radio(key="nav_page").set_value("Data Cleaning & Audit").run()
    assert any(b.key == "ai_q1" for b in at.button), "Chatbot phải hiển thị ở mọi trang!"
    rep8 = send_chat(at, "Đổi Return Window thành 20 ngày")
    assert at.session_state["return_window"] == 20
    assert "Return Window = 20 ngày" in rep8
    print("[PASS] 8. Chatbot hoạt động trên trang Data Cleaning & đổi Return Window = 20 ngày OK")

    # 9. Lọc dữ liệu theo kênh (an toàn khi không có dòng khớp & lọc thành công kênh Lazada)
    n_before_flt = len(at.session_state["normalized_data"]["Normalized_Transactions"])
    rep_empty_flt = send_chat(at, "Chỉ giữ lại kênh Shopee")
    assert len(at.session_state["normalized_data"]["Normalized_Transactions"]) == n_before_flt
    assert "giữ nguyên" in rep_empty_flt

    rep9 = send_chat(at, "Chỉ giữ lại kênh Lazada")
    df_flt = at.session_state["normalized_data"]["Normalized_Transactions"]
    assert not df_flt.empty
    assert df_flt["Channel"].str.lower().str.contains("lazada").all()
    assert "Lazada" in rep9
    print("[PASS] 9. Chat lọc kênh an toàn & chỉ giữ lại kênh Lazada OK")

    # 10. Reset toàn bộ phiên dữ liệu qua Chatbot
    rep10 = send_chat(at, "Reset dữ liệu")
    assert at.session_state["data_status"] == "NOT_CONNECTED"
    assert "Chưa kết nối" in rep10
    print("[PASS] 10. Chat Reset toàn bộ phiên dữ liệu OK")

    print("\nALL 10 CHATBOT DATA INTERVENTION E2E TESTS PASSED!")


if __name__ == "__main__":
    test_chatbot_interventions_e2e()
