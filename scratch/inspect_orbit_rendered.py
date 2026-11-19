import os
from streamlit.testing.v1 import AppTest
app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
at = AppTest.from_file(app_path, default_timeout=30)
at.run()
for i, m in enumerate(at.markdown):
    v = str(m.value)
    if "orbit-stage" in v:
        print(f"--- MARKDOWN {i} ---")
        print(v)
