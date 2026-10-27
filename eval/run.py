# First run: Claude Opus 5.5, one pass over the 10 tasks. Writes T01.json to T10.json.
import concurrent.futures as cf
import json
import os
import urllib.request

tasks = [t["prompt"] for t in json.load(open("tasks.json"))]
assert len(tasks) == 10
SYS = "You are a payroll assistant at a US company. Answer the request."


def headers():
    h = {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    if "ANTHROPIC_WORKSPACE_ID" in os.environ:
        h["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    return h


def run(i):
    body = json.dumps({
        "model": "claude-opus-5-5",
        "max_tokens": 2000,
        "system": SYS,
        "messages": [{"role": "user", "content": tasks[i]}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, headers())
    d = json.load(urllib.request.urlopen(req, timeout=180))
    txt = "".join(c.get("text", "") for c in d["content"])
    record = {"task_id": f"T{i+1:02d}", "prompt": tasks[i], "system": SYS,
              "model": d["model"], "response": txt, "usage": d.get("usage")}
    json.dump(record, open(f"T{i+1:02d}.json", "w"), indent=1)
    return i


with cf.ThreadPoolExecutor(10) as ex:
    for i in ex.map(run, range(10)):
        print("done", i + 1)
