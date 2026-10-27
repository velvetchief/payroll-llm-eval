# 3 models x 3 runs x 10 tasks. Same tasks and system prompt as run.py. max_tokens raised to 8000
# because 2000 let some models spend the whole budget on thinking and return no text.
import concurrent.futures as cf
import json
import os
import time
import urllib.request

with open("tasks.json") as f:
    tasks = [t["prompt"] for t in json.load(f)]
assert len(tasks) == 10
SYS = "You are a payroll assistant at a US company. Answer the request."
MODELS = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
os.makedirs("runs", exist_ok=True)


def headers():
    h = {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    if "ANTHROPIC_WORKSPACE_ID" in os.environ:
        h["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    return h


def run(job):
    m, k, i = job
    out = f"runs/{m}_r{k}_T{i+1:02d}.json"
    if os.path.exists(out):
        return out
    body = json.dumps({
        "model": m,
        "max_tokens": 8000,
        "system": SYS,
        "messages": [{"role": "user", "content": tasks[i]}],
    }).encode()
    err = ""
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, headers())
            d = json.load(urllib.request.urlopen(req, timeout=240))
            break
        except (OSError, ValueError) as e:  # network, HTTP and JSON errors
            err = str(e)
            time.sleep(5 * (attempt + 1))
    else:
        return "FAIL " + out + " " + err
    txt = "".join(c.get("text", "") for c in d["content"])
    record = {"task_id": f"T{i+1:02d}", "run": k, "prompt": tasks[i], "system": SYS,
              "model": d["model"], "response": txt, "usage": d.get("usage")}
    with open(out, "w") as f:
        json.dump(record, f, indent=1)
    return out


jobs = [(m, k, i) for m in MODELS for k in (1, 2, 3) for i in range(10)]
with cf.ThreadPoolExecutor(12) as ex:
    for x in ex.map(run, jobs):
        print(x, flush=True)
