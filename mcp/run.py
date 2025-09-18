import sys, yaml
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT_DIR / "config/.env")

from mcp.agents.stockpilot.agent import run as stockpilot_run
from mcp.agents.notifier.agent  import run as notifier_run
from mcp.tools.webfetch.runner  import run as webfetch_run
from mcp.tools.memvector.runner import run as memvector_run
from mcp.tools.qvector.runner   import run as qvector_run
from mcp.tools.browser.runner   import run as browser_run
from mcp.tools.qdrant.runner   import run as qdrantdb_run
from mcp.tools.fileparse.runner   import run as fileparse_run
from mcp.tools.embedder.runner   import run as embedder_run

HANDLERS = {"stockpilot": stockpilot_run, "notifier": notifier_run}
TOOLS    = {"webfetch": webfetch_run, "memvector": memvector_run, "qvector": qvector_run, "browser": browser_run, "qdrant": qdrantdb_run, "fileparse": fileparse_run}

def _resolve(val, context):
    if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
        path = val[2:-1].split(".")
        cur = context
        for p in path:
            if p == "prev":
                cur = context
            else:
                cur = cur.get(p, {})
        return cur if not isinstance(cur, dict) else str(cur)
    if isinstance(val, dict):
        return {k: _resolve(v, context) for k,v in val.items()}
    if isinstance(val, list):
        return [_resolve(x, context) for x in val]
    return val

def run_flow(path: str):
    data = yaml.safe_load(Path(path).read_text())
    context={}
    last_result=None
    for step in data.get("steps",[]):
        if "agent" in step:
            agent,task = step["agent"], step.get("task","")
            fn = HANDLERS.get(agent)
            if not fn:
                raise RuntimeError(f"unknown agent: {agent}")
            result = fn(task, last_result or context)
            context[agent]=result
            last_result=result
        elif "tool" in step:
            tool,action = step["tool"], step.get("action","")
            raw_args = step.get("args", {})
            args = _resolve(raw_args, context | {"prev": last_result or {}})
            trun = TOOLS.get(tool)
            if not trun:
                raise RuntimeError(f"unknown tool: {tool}")
            result = trun(action, args)
            context[tool]=result
            last_result=result
        elif "gate" in step:
            gate=step["gate"]
            input(f"⏸  승인 게이트({gate}) — Enter를 눌러 진행 ▶ ")
    print("✅ flow done.\ncontext=",context)

if __name__=="__main__":
    flow = sys.argv[1] if len(sys.argv)>1 else str(ROOT_DIR/"mcp/flows/daily_research.flow")
    run_flow(flow)
