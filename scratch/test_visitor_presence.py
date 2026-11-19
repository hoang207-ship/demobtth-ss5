from streamlit.testing.v1 import AppTest

at = AppTest.from_file("../app.py", default_timeout=120)
at.run()
assert not at.exception, at.exception

# Default user is Vũ Ruy Hoàng
assert at.session_state["user_name"] == "Vũ Ruy Hoàng"
vid1 = at.session_state["visitor_id"]
assert vid1

# Update current visitor name via visitor_profile_form
name_input = [ti for ti in at.text_input if ti.label == "Tên hiển thị của bạn"][0]
name_input.input("Nguyễn Minh Anh")
save_btn = [b for b in at.button if "Cập nhật tên hiển thị" in str(b.label)][0]
save_btn.click().run()
assert not at.exception, at.exception
assert at.session_state["user_name"] == "Nguyễn Minh Anh"

print("VISITOR PRESENCE TEST PASSED!")
