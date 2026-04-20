---
name: six-ministries-dispatch
description: Hermes Agent（中书令）调度六部尚书执行任务。通过 A2A 协议并行派发任务给工部/户部/礼部/兵部/刑部/吏部，支持结果汇总。
version: 1.0.0
author: Hermes Agent
license: Apache 2.0
tags: [six-ministries, a2a, multi-agent, openclaw, coordination]
---

# six-ministries-dispatch

中书令（Hermes Agent）调度六部尚书的 Hermes 原生工具。

## 功能

- **单 agent 调度**：指定某一部门执行任务
- **全六部并行**：同时调度全部六部，结果汇总
- **多部门并行**：指定任意部门组合并行执行

## 使用方式

```python
six_ministries_dispatch(
    message="任务描述",
    agents="all",       # dev | hubu | content | bingbu | xingbu | main | all
    summarize=True       # True=汇总格式，False=逐条格式
)
```

## Agent ID 映射

| Agent ID | 部门   |
|----------|--------|
| dev      | 工部   |
| hubu     | 户部   |
| content  | 礼部   |
| bingbu   | 兵部   |
| xingbu   | 刑部   |
| main     | 吏部   |
| all      | 全部   |

## 示例

```json
{
  "name": "six_ministries_dispatch",
  "arguments": {
    "message": "系统全面检查：1)基础设施 2)财务状况 3)内容进度 4)安全状况 5)军事动态 6)吏部监督",
    "agents": "all",
    "summarize": true
  }
}
```

## 返回示例

```
【六部尚书任务汇报】

■ 工部尚书
  系统运行平稳，ComfyUI 正常。

■ 户部尚书
  财务状况良好，无紧急事项。

...
```

## 工作流程

```
中书令 (Hermes)
    │ six_ministries_dispatch 工具调用
    ▼
A2A Client (Python)
    │ openclaw-cn agent --agent <id> --message "..."
    │ WebSocket + Ed25519 签名
    ▼
OpenClaw Gateway (:18789)
    ▼
六部尚书 (OpenClaw Agents)
    │ 各部独立执行
    ▼
结果汇总 → 中书令
```

## 依赖

- `openclaw-cn` CLI（需安装在 PATH 中）
- 六部尚书 agents 已注册到 OpenClaw Gateway
- A2A Gateway 运行在 :18800（用于任务追踪，可选）

## 工具注册

在 `toolsets.py` 中添加：

```python
"six_ministries": {
    "description": "调度六部尚书（中书令专用）",
    "tools": ["six_ministries_dispatch"],
    "includes": []
},
```

## CLI 方式（不使用 Hermes 工具）

```bash
python3 six_ministries_a2a_client.py --agent all \
  --message "汇报当前状态" --summarize
```
