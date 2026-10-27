import os,json,urllib.request,concurrent.futures as cf
tasks=[t["prompt"] for t in json.load(open("tasks.json"))]
assert len(tasks)==10
SYS="You are a payroll assistant at a US company. Answer the request."
def run(i):
    body=json.dumps({"model":"claude-opus-5-5","max_tokens":2000,"system":SYS,"messages":[{"role":"user","content":tasks[i]}]}).encode()
    r=urllib.request.Request("https://api.anthropic.com/v1/messages",body,{"x-api-key":os.environ["ANTHROPIC_API_KEY"],**({"anthropic-workspace-id":os.environ["ANTHROPIC_WORKSPACE_ID"]} if "ANTHROPIC_WORKSPACE_ID" in os.environ else {}),"anthropic-version":"2023-06-01","content-type":"application/json"})
    d=json.load(urllib.request.urlopen(r,timeout=180))
    txt="".join(c.get("text","") for c in d["content"])
    json.dump({"task_id":f"T{i+1:02d}","prompt":tasks[i],"system":SYS,"model":d["model"],"response":txt,"usage":d.get("usage")},open(f"T{i+1:02d}.json","w"),indent=1)
    return i
with cf.ThreadPoolExecutor(10) as ex:
    for i in ex.map(run,range(10)): print("done",i+1)
