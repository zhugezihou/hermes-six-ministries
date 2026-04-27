#!/usr/bin/env python3
"""
六部尚书 A2A Client — Hermes Agent（中书令）调度六部尚书的 A2A 协议封装

架构：
  Hermes (A2A Client) 
      │ HTTP POST (Bearer token)
      ▼
  A2A Gateway (:18800) — task 管理 / storage / 状态追踪
      │ (内部 dispatch → OpenClaw agents)
      ▼
  openclaw-cn CLI → OpenClaw Gateway (:18789) → 六部尚书 agents

关键：OpenClaw Gateway 的 A2A dispatch 使用 Ed25519 设备签名，
      与 A2A Gateway 的 HMAC-SHA256 不兼容。
      实际 dispatch 通过 CLI（使用正确 Ed25519签名）执行。
      A2A Gateway 负责 task tracking 和结果汇总。

用法：
  python3 six_ministries_a2a_client.py --agent dev --message "检查状态"
  python3 six_ministries_a2a_client.py --parallel dev hubu content --message "汇报"
  python3 six_ministries_a2a_client.py --task-id <taskId> --wait
"""

import argparse
import json
import sys
import time
import uuid
import subprocess
import os
import re
from typing import Optional
import requests

A2A_GATEWAY_URL = "http://127.0.0.1:18800/a2a/jsonrpc"
A2A_BEARER_TOKEN="a2a_zhongshu_2026"
CLI_TIMEOUT = 120  # seconds per agent

# Agent ID → 部门名称映射
AGENT_NAMES = {
    "dev": "工部尚书",
    "hubu": "户部尚书", 
    "content": "礼部尚书",
    "xingbu": "刑部尚书",
    "bingbu": "兵部尚书",
    "main": "吏部尚书",
}

# Agent 别名（支持中文昵称）
AGENT_ALIASES = {
    "工部": "dev",
    "户部": "hubu",
    "礼部": "content",
    "刑部": "xingbu",
    "兵部": "bingbu",
    "吏部": "main",
    "gongbu": "dev",
    "六部": "all",
}


def resolve_agent(agent: str) -> str:
    """解析 agent ID，支持别名"""
    if agent in AGENT_ALIASES:
        return AGENT_ALIASES[agent]
    if agent in AGENT_NAMES or agent == "all":
        return agent
    return agent  # 未知别名原样返回


def a2a_jsonrpc(method: str, params: dict, timeout: int = 10) -> dict:
    """发送 A2A JSON-RPC 请求"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {A2A_BEARER_TOKEN}",
    }
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())[:8],
    }
    resp = requests.post(
        f"{A2A_GATEWAY_URL}/a2a/jsonrpc",
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def send_message(agent_id: str, message: str, task_id: Optional[str] = None) -> dict:
    """通过 A2A Gateway 发送消息（实际通过 CLI 执行）"""
    if task_id is None:
        task_id = str(uuid.uuid4())
    
    msg_id = str(uuid.uuid4())
    
    try:
        result = a2a_jsonrpc("message/send", {
            "message": {
                "messageId": msg_id,
                "role": "user",
                "parts": [{"type": "text", "text": message}],
                "agentId": agent_id,
            },
            "taskId": task_id,
        })
        return result
    except Exception as e:
        # A2A dispatch 失败，回退到 CLI 直接调用
        return {"error": str(e), "_fallback": "cli"}


def cli_dispatch(agent_id: str, message: str) -> str:
    """直接通过 openclaw-cn CLI 调度 agent（带 A2A 风格的任务追踪）"""
    task_id = str(uuid.uuid4())
    
    # 构建 CLI 命令
    cmd = [
        "openclaw-cn", "agent",
        "--agent", agent_id,
        "--message", message,
    ]
    
    # 执行 CLI，捕获输出（过滤 Node.js 警告）
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=CLI_TIMEOUT,
            env={**os.environ, "NO_COLOR": "1"},
        )
        
        # 提取响应文本（只取 stdout，stderr 已经是过滤后的）
        output = result.stdout
        lines = output.splitlines()
        
        # 找到实际的 agent 响应（通常是最后的几行有意义的输出）
        response_lines = []
        skip_patterns = [
            r"^\[plugins\]",
            r"^Config warnings",
            r"^─", r"^├", r"^╰", r"^╮",
            r"^$",
            r"DeprecationWarning",
            r"manifest",
            r"Use `node",
        ]
        
        for line in lines:
            skip = False
            for pat in skip_patterns:
                if re.match(pat, line.strip()):
                    skip = True
                    break
            if not skip and line.strip():
                response_lines.append(line.strip())
        
        # 返回最后3行作为响应摘要
        response = "\n".join(response_lines[-3:]) if response_lines else "(无响应)"
        
        if result.returncode != 0 and not response_lines:
            response = f"执行失败 (code={result.returncode})"
            
    except subprocess.TimeoutExpired:
        response = f"[超时 {CLI_TIMEOUT}s]"
    except Exception as e:
        response = f"[错误: {e}]"
    
    return response


def create_task(agent_id: str, message: str) -> dict:
    """创建 A2A task（使用 CLI 执行，返回 task 结果）"""
    task_id = str(uuid.uuid4())
    
    # 直接使用 CLI 执行（绕过 A2A Gateway dispatch）
    agent_name = AGENT_NAMES.get(agent_id, agent_id)
    print(f"[中书令] 派发任务给 {agent_name}...", file=sys.stderr)
    
    response = cli_dispatch(agent_id, message)
    
    # 构造 A2A 风格的响应
    return {
        "kind": "task",
        "id": task_id,
        "status": {
            "state": "completed",
            "message": {
                "kind": "message",
                "messageId": str(uuid.uuid4()),
                "role": "agent",
                "parts": [{"kind": "text", "text": response}],
            },
        },
        "_agent_id": agent_id,
        "_agent_name": agent_name,
    }


def parallel_dispatch(agent_ids: list, message: str) -> list:
    """并行调度多个部门"""
    import concurrent.futures
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agent_ids)) as executor:
        futures = {
            executor.submit(create_task, agent_id, message): agent_id
            for agent_id in agent_ids
        }
        for future in concurrent.futures.as_completed(futures, timeout=CLI_TIMEOUT + 10):
            agent_id = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "kind": "task",
                    "id": str(uuid.uuid4()),
                    "status": {
                        "state": "failed",
                        "message": {
                            "kind": "text",
                            "text": f"{AGENT_NAMES.get(agent_id, agent_id)}: {e}",
                        },
                    },
                    "_agent_id": agent_id,
                    "_agent_name": AGENT_NAMES.get(agent_id, agent_id),
                })
    return results


def summarize_results(results: list) -> str:
    """汇总多个部门的结果"""
    lines = ["【六部尚书任务汇报】", ""]
    for r in results:
        agent_name = r.get("_agent_name", r.get("_agent_id", "?"))
        status = r.get("status", {})
        state = status.get("state", "?")
        msg = status.get("message", {})
        parts = msg.get("parts", [])
        text = parts[0].get("text", "(无内容)") if parts else "(无内容)"
        
        lines.append(f"■ {agent_name} [{state}]")
        lines.append(f"  {text[:200]}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="六部尚书 A2A Client")
    parser.add_argument("--agent", type=str, help="Agent ID (dev/hubu/content/xingbu/bingbu/main)")
    parser.add_argument("--parallel", nargs="+", dest="parallel_agents", help="并行调度多个 agent")
    parser.add_argument("--message", type=str, required=True, help="任务消息")
    parser.add_argument("--task-id", type=str, help="查询已有 task 的结果")
    parser.add_argument("--wait", action="store_true", help="等待 task 完成")
    parser.add_argument("--summarize", action="store_true", help="汇总所有结果")
    parser.add_argument("--list-agents", action="store_true", help="列出所有可用 agent")
    
    args = parser.parse_args()
    
    if args.list_agents:
        print("可用 agent:")
        for aid, name in AGENT_NAMES.items():
            print(f"  {aid:10s} — {name}")
        return
    
    if args.task_id:
        # 查询 task 状态
        result = a2a_jsonrpc("tasks/get", {"id": args.task_id})
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    if args.parallel_agents:
        # 并行调度
        agent_ids = [resolve_agent(a) for a in args.parallel_agents]
        if "all" in agent_ids:
            agent_ids = list(AGENT_NAMES.keys())
        
        results = parallel_dispatch(agent_ids, args.message)
        
        if args.summarize:
            print(summarize_results(results))
        else:
            for r in results:
                print(f"\n=== {r.get('_agent_name', '?')} ===")
                status = r.get("status", {})
                msg = status.get("message", {})
                parts = msg.get("parts", [])
                if parts:
                    print(parts[0].get("text", ""))
        return
    
    if args.agent:
        agent_id = resolve_agent(args.agent)
        
        if agent_id == "all":
            # 全部分部门并行调度
            results = parallel_dispatch(list(AGENT_NAMES.keys()), args.message)
            if args.summarize:
                print(summarize_results(results))
            else:
                for r in results:
                    print(f"\n=== {r.get('_agent_name', '?')} ===")
                    status = r.get("status", {})
                    msg = status.get("message", {})
                    parts = msg.get("parts", [])
                    if parts:
                        print(parts[0].get("text", ""))
        else:
            result = create_task(agent_id, args.message)
            status = result.get("status", {})
            msg = status.get("message", {})
            parts = msg.get("parts", [])
            text = parts[0].get("text", "(无内容)") if parts else "(无内容)"
            print(text)
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
