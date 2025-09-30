# api/result.py  -- smoke-test handler
import json, os, traceback

def handler(request):
    try:
        info = {
            "ok": True,
            "note": "smoke test ok",
            "cwd": os.getcwd(),
            "files": [f for f in os.listdir(os.getcwd())][:20]
        }
        return (json.dumps(info), 200, {"Content-Type": "application/json"})
    except Exception as e:
        tb = traceback.format_exc()
        print("SMOKE ERROR", tb)
        return (json.dumps({"error":"smoke failed", "detail": str(e)}), 500, {"Content-Type":"application/json"})
