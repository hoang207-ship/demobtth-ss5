import asyncio
import json
import subprocess
import time
import urllib.request
import websockets

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

async def check_biz_context():
    port = 9222
    proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "http://localhost:8501"
    ])
    try:
        ws_url = None
        for _ in range(20):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    page_tabs = [t for t in tabs if t.get("type") == "page"]
                    if page_tabs:
                        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                pass

        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            async def call(method, params=None):
                nonlocal msg_id
                cid = msg_id
                msg_id += 1
                payload = {"id": cid, "method": method}
                if params:
                    payload["params"] = params
                await ws.send(json.dumps(payload))
                while True:
                    res = json.loads(await ws.recv())
                    if res.get("id") == cid:
                        return res.get("result", {})

            await call("Page.enable")
            await call("Runtime.enable")

            # Click on navigation to PAGES[1] ("Kết Nối Google Sheets")
            # Wait for sidebar radio buttons
            print("Waiting for page load...")
            for _ in range(10):
                time.sleep(1)
                res = await call("Runtime.evaluate", {
                    "expression": "document.querySelectorAll('input[type=\"radio\"]').length",
                    "returnByValue": True
                })
                if res.get("result", {}).get("value", 0) > 0:
                    break

            # Click the second radio button (Kết Nối Google Sheets)
            click_js = """
            (() => {
                const radios = Array.from(document.querySelectorAll('label'));
                const connectLabel = radios.find(l => l.innerText && l.innerText.includes('Kết Nối Google Sheets'));
                if (connectLabel) {
                    connectLabel.click();
                    return "CLICKED_CONNECT";
                }
                return "NOT_FOUND";
            })()
            """
            click_res = await call("Runtime.evaluate", {"expression": click_js, "returnByValue": True})
            print("Click result:", click_res.get("result", {}).get("value"))

            time.sleep(3)

            # Query biz context elements
            check_js = """
            (() => {
                const bizHead = document.querySelector('.biz-head');
                const bizTitle = document.querySelector('.biz-title')?.innerText;
                const bizSub = document.querySelector('.biz-sub')?.innerText;
                const inputs = Array.from(document.querySelectorAll('input, textarea')).map(el => ({
                    placeholder: el.placeholder,
                    type: el.tagName
                }));
                const aiBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Trao đổi yêu cầu'));

                return {
                    hasBizHead: !!bizHead,
                    bizTitle: bizTitle,
                    bizSub: bizSub,
                    inputs: inputs,
                    hasAiBtn: !!aiBtn,
                    aiBtnText: aiBtn?.innerText
                };
            })()
            """
            eval_res = await call("Runtime.evaluate", {"expression": check_js, "returnByValue": True})
            data = eval_res.get("result", {}).get("value", {})
            print("Biz Context Elements:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            assert data.get("hasBizHead"), "biz-head not found"
            assert data.get("hasAiBtn"), "AI consult button not found"
            print("\n>>> BIZ CONTEXT & AI CONSULTATION BLOCK VERIFIED IN BROWSER! <<<")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(check_biz_context())
