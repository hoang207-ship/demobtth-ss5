import re

with open("app.py", "r", encoding="utf-8") as f:
    text = f.read()

styles = re.findall(r"<style>(.*?)</style>", text, re.DOTALL)
print(f"Found {len(styles)} style blocks")
for i, s in enumerate(styles):
    open_b = s.count("{")
    close_b = s.count("}")
    print(f"Block {i}: open={open_b}, close={close_b}")
    if open_b != close_b:
        print(f"MISMATCH IN BLOCK {i}!")
