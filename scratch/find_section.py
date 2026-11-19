with open("app.py", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if line.startswith("def html(") or "html =" in line or "html(" in line and idx < 100:
            print(f"Line {idx}: {line.strip()}")
