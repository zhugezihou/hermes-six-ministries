#!/usr/bin/env python3
"""
六部尚书调度工具 — Hermes Agent（中书令）派发任务给六部尚书

通过 A2A Client 脚本调度六部尚书 agents 并汇总结果。
支持单部门、多部门并行、全六部并行三种模式。

用法（Hermes 工具调用）:
  six_ministries_dispatch(
    message="检查服务器状态",
    agents="dev",           # dev | hubu | content | bingbu | xingbu | main | all
    summarize=true           # true=汇总格式, false=逐条格式
  )
"""

import json
import subprocess
import os
import sys
import re
import concurrent.futures
from typing import Optional, List
from tools.registry import registry

SCRIPT_PATH = "/home/asus/.openclaw/workspace-wsl/cross-agent-comm/scripts/six_ministries_a2a_client.py"
CLI_TIMEOUT = 120  # seconds per agent

AGENT_NAMES = {
    "dev": "工部尚书",
    "hubu": "户部尚书",
    "content": "礼部尚书",
    "xingbu": "刑部尚书",
    "bingbu": "兵部尚书",
    "main": "吏部尚书",
}

AGENT_IDS = set(AGENT_NAMES.keys())


def _cli_dispatch(agent_id: str, message: str) -> dict:
    """通过 openclaw-cn CLI 调度单个 agent"""
    cmd = [
        sys.executable,  # 使用当前 Python 解释器
        SCRIPT_PATH,
        "--agent", agent_id,
        "--message", message,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT,
            env={**os.environ, "NO_COLOR": "1"},
        )
        
        output = result.stdout
        
        # 提取最后的响应行
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        
        # 跳过调度信息行，只取结果
        response_lines = []
        for line in lines:
            if line.startswith("[中书令]") or line.startswith("【"):
                continue
            response_lines.append(line)
        
        response = "\n".join(response_lines) if response_lines else "(无响应)"
        
        if result.returncode != 0 and not response_lines:
            response = f"执行失败 (code={result.returncode})"
            
    except subprocess.TimeoutExpired:
        response = f"[超时 {CLI_TIMEOUT}s]"
    except Exception as e:
        response = f"[错误: {e}]"
    
    return {
        "agent_id": agent_id,
        "agent_name": AGENT_NAMES.get(agent_id, agent_id),
        "response": response,
    }


def _parallel_dispatch(agent_ids: List[str], message: str) -> List[dict]:
    """并行调度多个 agent"""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_ids)) as executor:
        futures = {
            executor.submit(_cli_dispatch, agent_id, message): agent_id
            for agent_id in agent_ids
        }
        for future in concurrent.futures.as_completed(futures, timeout=CLI_TIMEOUT + 10):
            agent_id = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append({
                    "agent_id": agent_id,
                    "agent_name": AGENT_NAMES.get(agent_id, agent_id),
                    "response": f"[错误: {e}]",
                })
    return results


def six_ministries_dispatch(
    message: str,
    agents: str = "all",
    summarize: bool = True,
) -> str:
    """
    调度六部尚书执行任务并汇总结果。
    
    Args:
        message: 要派发的任务描述
        agents: 目标 agent (dev/hubu/content/bingbu/xingbu/main/all)，默认 all
        summarize: 是否汇总格式输出，默认 true
    
    Returns:
        JSON 格式的任务结果
    """
    # 解析 agents
    if agents == "all":
        target_ids = list(AGENT_IDS)
    elif agents in AGENT_IDS:
        target_ids = [agents]
    else:
        return json.dumps({
            "error": f"未知 agent: {agents}",
            "available": list(AGENT_IDS) + ["all"],
        }, ensure_ascii=False)
    
    # 并行调度
    results = _parallel_dispatch(target_ids, message)
    
    if summarize:
        lines = ["【六部尚书任务汇报】", ""]
        for r in results:
            lines.append(f"■ {r['agent_name']}")
            lines.append(f"  {r['response'][:300]}")
            lines.append("")
        return "\n".join(lines)
    else:
        parts = []
        for r in results:
            parts.append(f"=== {r['agent_name']} ===\n{r['response']}")
        return "\n\n".join(parts)


# --- Schema ---
SIX_MINISTRIES_SCHEMA = {
    "name": "six_ministries_dispatch",
    "description": """调度六部尚书执行任务（中书令专用）。

六部尚书是运行在 OpenClaw Gateway 上的独立 AI agents。
通过 A2A 协议并行调度，工部/户部/礼部/兵部/刑部/吏部各自独立执行后汇总结果。

使用场景：
- 系统全面检查（各部汇报本领域状态）
- 多部门协作任务（分解后并行执行）
- 定期巡查（每日例行汇报）

返回格式：各部尚书回复汇总，可选逐条或汇总格式。""",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "要派发给六部尚书的任务描述，越具体越好。例如：'检查服务器状态'、'汇报当前最重要的一件事'、'系统全面检查：1)基础设施 2)财务状况 3)内容进度'",
            },
            "agents": {
                "type": "string",
                "description": "目标 agent：dev(工部)/hubu(户部)/content(礼部)/bingbu(兵部)/xingbu(刑部)/main(吏部)/all(全部，默认)",
                "default": "all",
            },
            "summarize": {
                "type": "boolean",
                "description": "true=汇总格式（推荐），false=逐条详细格式",
                "default": True,
            },
        },
        "required": ["message"],
    },
}


# --- Registry ---
registry.register(
    name="six_ministries_dispatch",
    toolset="six_ministries",
    schema=SIX_MINISTRIES_SCHEMA,
    handler=lambda args, **kw: six_ministries_dispatch(
        message=args.get("message", ""),
        agents=args.get("agents", "all"),
        summarize=args.get("summarize", True),
    ),
    check_fn=lambda: os.path.exists(SCRIPT_PATH),
)
