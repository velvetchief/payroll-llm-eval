# 3 models x 3 runs x 10 tasks. Same tasks and system prompt as run.py. max_tokens raised to 8000 because 2000 let some models spend the whole budget on thinking and return no text.
import os,json,urllib.request,concurrent.futures as cf,time
tasks=[t["prompt"] for t in json.load(open("tasks.json"))]
assert len(tasks)==10
SYS="You are a payroll assistant at a US company. Answer the request."
MODELS=["claude-opus-5-5","claude-sonnet-5-5","claude-haiku-5-5"]
os.makedirs("runs",exist_ok=True)
def run(job):
    m,k,i=job; out=f"runs/{m}_r{k}_T{i+1:02d}.json"
    if os.path.exists(out): return out
    body=json.dumps({"model":m,"max_tokens":8000,"system":SYS,"messages":[{"role":"user","content":tasks[i]}]}).encode()
    for a in range(4):
        try:
            r=urllib.request.Request("https://api.anthropic.com/v1/messages",body,{"x-api-key":os.environ["ANTHROPIC_API_KEY"],**({"anthropic-workspace-id":os.environ["ANTHROPIC_WORKSPACE_ID"]} if "ANTHROPIC_WORKSPACE_ID" in os.environ else {}),"anthropic-version":"2023-06-01","content-type":"application/json"})
            d=json.load(urllib.request.urlopen(r,timeout=240));break
        except Exception as e: time.sleep(5*(a+1)); err=str(e)
    else: return "FAIL "+out+" "+err
    txt="".join(c.get("text","") for c in d["content"])
    json.dump({"task_id":f"T{i+1:02d}","run":k,"prompt":tasks[i],"system":SYS,"model":d["model"],"response":txt,"usage":d.get("usage")},open(out,"w"),indent=1)
    return out
jobs=[(m,k,i) for m in MODELS for k in (1,2,3) for i in range(10)]
with cf.ThreadPoolExecutor(12) as ex:
    for x in ex.map(run,jobs): print(x,flush=True)
