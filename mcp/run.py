import sys, yaml
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(ROOT_DIR))

from mcp.agents.stockpilot.agent import run as stockpilot_run
from mcp.agents.notifier.agent  import run as notifier_run

HANDLERS={"stockpilot":stockpilot_run,"notifier":notifier_run}

def run_flow(path: str):
    data=yaml.safe_load(Path(path).read_text())
    context={}
    last_result=None
    for step in data.get("steps",[]):
        if "agent" in step:
            agent,task=step["agent"],step.get("task","")
            fn = HANDLERS.get(agent)
            if not fn:
                raise RuntimeError(f"unknown agent: {agent}")
            result=fn(task, last_result or context)
            context[agent]=result
            last_result=result
        elif "gate" in step:
            gate=step["gate"]
            input(f"⏸  승인 게이트({gate}) — Enter를 눌러 진행 ▶ ")
    print("✅ flow done.\ncontext=",context)

if __name__=="__main__":
    flow=sys.argv[1] if len(sys.argv)>1 else str(ROOT_DIR/"mcp/flows/daily_research.flow")
    run_flow(flow)
