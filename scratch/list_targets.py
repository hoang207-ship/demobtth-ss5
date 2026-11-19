import json, urllib.request

with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
    targets = json.loads(resp.read().decode())
    for t in targets:
        print(f"type: {t.get('type')}, title: {t.get('title')}, url: {t.get('url')}, ws: {t.get('webSocketDebuggerUrl')}")
