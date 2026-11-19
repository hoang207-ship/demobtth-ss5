import re
import os
import sys

# 1. Read app.py and verify CSS keyframes & rules
with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# Assert Keyframes
assert "@keyframes orbitRevolve360" in code, "orbitRevolve360 keyframe missing"
assert "@keyframes orbitCounterRevolve360" in code, "orbitCounterRevolve360 keyframe missing"
assert "@keyframes floatBobbingY" in code, "floatBobbingY keyframe missing"

# Assert concentric positioning (Pixel Margin Centering to prevent transform displacement)
assert "margin-left: -120px;" in code and "margin-top: -120px;" in code, "hero-circle concentric pixel centering missing"
assert "margin-left: -155px;" in code and "margin-top: -155px;" in code, "orbit-ring concentric pixel centering missing"

# Assert 30s revolution and 120-degree phase shift
assert "animation: orbitRevolve360 30s linear infinite;" in code, "orbitRevolve360 30s missing"
assert "animation-delay: -10s;" in code, "satellite 2 120-degree delay missing"
assert "animation-delay: -20s;" in code, "satellite 3 240-degree delay missing"

# Assert counter-spin keeping cards upright
assert "animation: orbitCounterRevolve360 30s linear infinite;" in code, "orbitCounterRevolve360 30s missing"

# Assert bottom cards decoupled vertical float
assert "animation: floatBobbingY 4.5s ease-in-out infinite;" in code, "floatBobbingY 4.5s missing"
assert ".mini-col.mc-1" in code and ".mini-col.mc-2" in code and ".mini-col.mc-3" in code, "mini-col columns missing"

# 2. Verify with Streamlit AppTest
from streamlit.testing.v1 import AppTest
app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
at = AppTest.from_file(app_path, default_timeout=30)
at.run()
assert not at.exception, f"App crashed: {at.exception}"

# Check HTML content
found_circle = False
found_sat1 = False
found_sat2 = False
found_sat3 = False
found_mc1 = False
found_mc2 = False
found_mc3 = False

for m in at.markdown:
    v = str(m.value)
    if "hero-circle" in v and "DF" in v and "Data Force" in v:
        found_circle = True
    if "orbit-sat sat-1" in v and "Auto-Clean" in v and "6 Bước chuẩn hoá" in v:
        found_sat1 = True
    if "orbit-sat sat-2" in v and "7 Audit Tests" in v and "Bảo toàn dòng tiền" in v:
        found_sat2 = True
    if "orbit-sat sat-3" in v and "HITL Guardrail" in v and "Kiểm soát ngoại lệ" in v:
        found_sat3 = True
    if "mini-col mc-1" in v and "Làm Sạch Tự Động" in v and "6 Bước" in v:
        found_mc1 = True
    if "mini-col mc-2" in v and "Hồ sơ chờ phê duyệt (HITL)" in v and ">0<" in v:
        found_mc2 = True
    if "mini-col mc-3" in v and "Kiểm Toán Suite" in v and "7 Tests" in v:
        found_mc3 = True

print(f"1. Center DF Data Force circle: {found_circle}")
print(f"2. Orbit Sat 1 (Auto-Clean): {found_sat1}")
print(f"3. Orbit Sat 2 (7 Audit Tests): {found_sat2}")
print(f"4. Orbit Sat 3 (HITL Guardrail): {found_sat3}")
print(f"5. Bottom Card 1 (Auto 6 Bước): {found_mc1}")
print(f"6. Bottom Card 2 (HITL 0): {found_mc2}")
print(f"7. Bottom Card 3 (Audit 7 Tests): {found_mc3}")

assert found_circle, "Center circle missing"
assert found_sat1, "Sat 1 missing"
assert found_sat2, "Sat 2 missing"
assert found_sat3, "Sat 3 missing"
assert found_mc1, "Bottom Card 1 missing"
assert found_mc2, "Bottom Card 2 missing"
assert found_mc3, "Bottom Card 3 missing"

print("\n>>> ALL MOTION DESIGN SPECIFICATIONS VERIFIED 100% PASS! <<<")
