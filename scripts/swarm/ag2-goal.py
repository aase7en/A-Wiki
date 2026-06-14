#!/usr/bin/env python3
"""
scripts/swarm/ag2-goal.py — AG2 Goal Orchestrator for A-Wiki
=============================================================

Runs a multi-agent loop to accomplish a declared goal:
  1. Planner (top model, o3/xhigh) — decomposes goal into subtasks
  2. Executor(s) (free models via delegate.sh) — execute subtasks in parallel
  3. Validator (Planner again) — reviews evidence, decides done or re-plan

Usage:
  python3 scripts/swarm/ag2-goal.py --goal "<goal>" [--mode plan|execute|full] [--json]
  python3 scripts/swarm/ag2-goal.py --goal "<goal>" --dry-run

Requires Python >=3.10 and .venv-ag2:
  python3.10 -m venv .venv-ag2 && source .venv-ag2/bin/activate
  pip install -r requirements-ag2.txt
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "swarm"))

try:
    from ag2_tools import TOOL_REGISTRY, delegate_task, wiki_search
    AG2_TOOLS_OK = True
except ImportError:
    AG2_TOOLS_OK = False


def check_ag2_available() -> tuple[bool, str]:
    """Check if AG2 is installed in the active Python environment."""
    try:
        import autogen  # noqa: F401 — ag2 package installs as `autogen`
        return True, ""
    except ImportError:
        return False, (
            "AG2 not installed. Run:\n"
            "  python3.10 -m venv .venv-ag2\n"
            "  source .venv-ag2/bin/activate\n"
            "  pip install -r requirements-ag2.txt\n"
            "Then re-run this script."
        )


def build_planner_system_prompt(goal: str) -> str:
    return f"""You are the A-Wiki Planner — a senior architect with access to a personal knowledge wiki.

Your goal: {goal}

RESPONSIBILITIES:
1. Decompose the goal into concrete subtasks (max 6 subtasks per round).
2. Assign each subtask a task_type: search | lookup | summarize | reason | compare | scan
3. Dispatch subtasks via delegate_task() — these run on free models (Gemini/DeepSeek/Qwen).
4. Use wiki_search() and wiki_get_page() to gather context before delegating.
5. After receiving executor results, validate and synthesize into a final answer.
6. If subtasks are insufficient, re-plan with more specific prompts.

COST-FIRST RULES:
- Always call wiki_search() FIRST before delegating to external models.
- Use delegate_task("search", ...) for lookup tasks — do NOT answer from training data alone.
- Only use this model (Planner) for planning, synthesis, and validation.

OUTPUT FORMAT:
When done, respond with EXACTLY:
FINAL_ANSWER: <your synthesized answer>
DONE
"""


def build_executor_system_prompt() -> str:
    return """You are an A-Wiki Executor. You receive a single delegated subtask and execute it.

Use the tools available to you:
- wiki_search(query) — search local A-Wiki knowledge (free, prefer this first)
- delegate_task(task_type, prompt) — call a free external model for non-local tasks

Return your result as a concise structured summary. Do not add padding or pleasantries.
Format: SUBTASK_RESULT: <your result>
"""


def run_dry_plan(goal: str) -> dict[str, Any]:
    """
    Dry-run: plan subtasks WITHOUT calling external models or AG2.
    Uses only local wiki search to gather evidence.
    """
    print(f"🎯 Goal: {goal}", file=sys.stderr)
    print("🔍 Dry-run: searching local wiki for context...", file=sys.stderr)

    context_results = wiki_search(goal, limit=5) if AG2_TOOLS_OK else "{}"
    try:
        context = json.loads(context_results)
    except Exception:
        context = {"raw": context_results}

    plan = {
        "goal": goal,
        "mode": "dry-run",
        "wiki_context_found": bool(context.get("results")),
        "suggested_subtasks": [
            {"task_type": "search", "prompt": f"What is known about: {goal}"},
            {"task_type": "reason", "prompt": f"What are the key challenges or steps for: {goal}"},
            {"task_type": "summarize", "prompt": f"Summarize recent wiki knowledge about: {goal}"},
        ],
        "delegation_target": "scripts/swarm/delegate.sh",
        "planner_model": "o3 (xhigh reasoning)",
        "executor_models": ["gemini-2.5-flash:free", "deepseek-chat-v3:free", "qwen3-235b:free"],
        "note": "Run without --dry-run to execute with AG2 agents",
    }

    if context.get("results"):
        plan["wiki_context"] = context["results"][:3]

    return plan


def run_ag2_goal(goal: str, mode: str = "full") -> dict[str, Any]:
    """Run the full AG2 orchestration loop."""
    ok, err = check_ag2_available()
    if not ok:
        print(f"❌ {err}", file=sys.stderr)
        sys.exit(1)

    import autogen  # type: ignore

    # AG2 LLM config — uses env var OPENAI_API_KEY for Planner (Codex platform)
    planner_config = {
        "config_list": [
            {
                "model": os.environ.get("AG2_PLANNER_MODEL", "o3"),
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
                "api_type": "openai",
            }
        ],
        "timeout": 120,
        "cache_seed": None,  # disable caching for live runs
    }

    # Tool list for Planner and Executor
    tool_functions = {t["name"]: t["func"] for t in TOOL_REGISTRY}

    # Create Planner agent
    planner = autogen.AssistantAgent(
        name="Planner",
        system_message=build_planner_system_prompt(goal),
        llm_config=planner_config,
        max_consecutive_auto_reply=8,
    )

    # Create Executor agent (same tool access, simpler prompt)
    executor = autogen.AssistantAgent(
        name="Executor",
        system_message=build_executor_system_prompt(),
        llm_config=planner_config,  # Could use a cheaper model here
        max_consecutive_auto_reply=4,
    )

    # Create UserProxy (orchestrates tool execution)
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=12,
        is_termination_msg=lambda msg: "DONE" in msg.get("content", ""),
        code_execution_config=False,  # No code execution — tools only
    )

    # Register tools with both agents and user_proxy
    for tool_name, tool_func in tool_functions.items():
        autogen.register_function(
            tool_func,
            caller=planner,
            executor=user_proxy,
            name=tool_name,
            description=next(
                t["description"] for t in TOOL_REGISTRY if t["name"] == tool_name
            ),
        )

    # Kick off the goal
    print(f"🎯 Starting AG2 goal orchestration: {goal}", file=sys.stderr)
    print(f"   Planner: {planner_config['config_list'][0]['model']}", file=sys.stderr)
    print(f"   Executors: via delegate.sh (free models)", file=sys.stderr)

    chat_result = user_proxy.initiate_chat(
        planner,
        message=f"Goal: {goal}\n\nBegin by searching the local wiki, then plan and execute subtasks.",
    )

    # Extract final answer from last Planner message
    final_answer = ""
    for msg in reversed(chat_result.chat_history):
        content = msg.get("content", "")
        if "FINAL_ANSWER:" in content:
            final_answer = content.split("FINAL_ANSWER:")[-1].split("DONE")[0].strip()
            break

    return {
        "goal": goal,
        "mode": mode,
        "final_answer": final_answer or "(no FINAL_ANSWER found in conversation)",
        "turns": len(chat_result.chat_history),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AG2 Goal Orchestrator for A-Wiki")
    parser.add_argument("--goal", required=True, help="The goal to accomplish")
    parser.add_argument(
        "--mode",
        choices=["plan", "execute", "full"],
        default="full",
        help="plan=dry-run plan only; execute=run without re-planning; full=full loop (default)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan subtasks without calling AG2/external models")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output result as JSON")
    args = parser.parse_args()

    if args.dry_run or args.mode == "plan":
        result = run_dry_plan(args.goal)
    else:
        result = run_ag2_goal(args.goal, mode=args.mode)

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if "final_answer" in result:
            print(f"\n✅ Final Answer:\n{result['final_answer']}")
        elif "suggested_subtasks" in result:
            print(f"\n📋 Dry-run plan for: {result['goal']}")
            for i, sub in enumerate(result["suggested_subtasks"], 1):
                print(f"  {i}. [{sub['task_type']}] {sub['prompt']}")
            print(f"\n  → Executor: {result['delegation_target']}")
            print(f"  → Models: {', '.join(result['executor_models'])}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
