import sys, json, yaml
from jinja2 import Environment

# --- tool runners ---
from mcp.tools.webfetch.runner    import run as webfetch_run
from mcp.tools.embedder.runner    import run as embedder_run
from mcp.tools.qdrant.runner      import run as qdrant_run
from mcp.tools.fileparse.runner   import run as fileparse_run
from mcp.tools.browser.runner     import run as browser_run
from mcp.tools.memvector.runner   import run as memvector_run
from mcp.tools.qvector.runner     import run as qvector_run

# --- agent runners ---
from mcp.agents.researcher.runner import run as researcher_run
from mcp.agents.notifier.runner   import run as notifier_run

TOOLS = {
    "webfetch":  webfetch_run,
    "embedder":  embedder_run,
    "qdrant":    qdrant_run,
    "fileparse": fileparse_run,
    "browser":   browser_run,
    "memvector": memvector_run,
    "qvector":   qvector_run,
}

AGENTS = {
    "researcher": researcher_run,
    "notifier":   notifier_run,
}

def _env():
    env = Environment()
    env.filters["tojson"]   = lambda v: json.dumps(v, ensure_ascii=False)
    env.filters["truncate"] = lambda s, n=200: (s[:n]+"...") if isinstance(s, str) and len(s) > n else s
    return env

def _render(val, ctx, env):
    if isinstance(val, str):
        return env.from_string(val).render(**ctx)
    if isinstance(val, dict):
        return {k: _render(v, ctx, env) for k, v in val.items()}
    if isinstance(val, list):
        return [_render(v, ctx, env) for v in val]
    return val

def run_flow(flow_path: str):
    with open(flow_path, "r", encoding="utf-8") as f:
        flow = yaml.safe_load(f)

    ctx, env = {}, _env()

    for step in flow.get("steps", []):
        if "tool" in step:
            name   = step["tool"]
            action = step.get("action", "")
            fn     = TOOLS.get(name)
            if not fn:
                raise RuntimeError(f"unknown tool: {name}")
            args = _render(step.get("args", {}) or {}, ctx, env)
            res  = fn(action, args)
            ctx[name] = res

        elif "agent" in step:
            name = step["agent"]
            task = step.get("task", "")
            fn   = AGENTS.get(name)
            if not fn:
                raise RuntimeError(f"unknown agent: {name}")
            args = _render(step.get("args", {}) or {}, ctx, env)
            res  = fn(task, args)
            ctx[name] = res

        elif "gate" in step:
            gate = step["gate"]
            input(f"\n⏸  승인 게이트({gate}) — Enter를 눌러 진행 ▶ ")
        else:
            print("skip step:", step)

    print("✅ flow done.")
    return ctx

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: bin/flow <flow_path>  (또는)  python mcp/run.py <flow_path>")
        sys.exit(1)
    run_flow(sys.argv[1])
