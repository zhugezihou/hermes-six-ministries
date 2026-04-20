# ACP (Agent Client Protocol) 分析

> 分析日期：2026-04-20
> 来源：NousResearch/hermes-agent

## 协议概述

ACP 是 Hermes Agent 内置的客户端-服务端协议，主要用于 IDE 集成（VS Code、Zed、JetBrains）。

```
IDE (ACP Client) ← stdio (stdin/stdout) → Hermes Agent
```

## 文件结构

```
hermes-agent/
├── acp_adapter/
│   ├── __init__.py
│   ├── __main__.py         # 入口：hermes acp
│   ├── entry.py            # ACP 会话入口
│   ├── server.py           # HermesACPAgent 类（核心）
│   ├── session.py          # SessionManager 会话管理
│   ├── tools.py            # Hermes → ACP ToolKind 映射
│   ├── auth.py             # provider 检测
│   └── permissions.py      # 权限回调
├── agent/
│   └── copilot_acp_client.py  # 另一个方向：Hermes → Copilot ACP
```

## 核心组件

### HermesACPAgent (server.py)

继承自 `acp.Agent`，是 ACP 协议的服务端实现。

```python
class HermesACPAgent(acp.Agent):
    _SLASH_COMMANDS = {
        "help": "Show available commands",
        "model": "Show or change current model",
        "tools": "List available tools",
        "context": "Show conversation context info",
        "reset": "Clear conversation history",
        "compact": "Compress conversation context",
        "version": "Show Hermes version",
    }
```

### SessionManager (session.py)

管理多个 ACP 会话，支持 fork、resume 等操作。

### tools.py 映射

| Hermes tool | ACP ToolKind |
|-------------|--------------|
| read_file | read |
| write_file / patch | edit |
| search_files | search |
| terminal / process / execute_code | execute |
| web_search / web_extract | fetch |
| browser_navigate | fetch |
| delegate_task | execute |
| _thinking | think |

## 协议消息流

```
1. Client → Server: initialize (ClientCapabilities)
2. Server → Client: InitializeResponse (AgentCapabilities)
3. Client → Server: createSession / resumeSession
4. Server → Client: NewSessionResponse / ResumeSessionResponse
5. [循环]
   a. Client → Server: prompt (content blocks)
   b. Server → Client: stream response (text, tool calls)
   c. Client → Server: tool results
   d. Server → Client: completion
```

## 是否可用于 OpenClaw 通信？

**结论：目前不适用，原因：**

1. **设计用途**：ACP 是 IDE → Agent 的单向请求-响应协议，不是 agent-to-agent 协议
2. **传输层**：基于 stdio，不适合跨进程网络通信
3. **会话模型**：一个 Client 对应一个 Session，OpenClaw Hub 是多 agent 聚合
4. **工具集**：ACP 的 tools 是给 IDE 用的，不是通用的 agent 间消息

**可能的扩展方向：**

如果 ACP 协议可以改用 WebSocket 传输，理论上可以让 Hermes 和 OpenClaw 都作为 ACP Agent 接入同一个 Hub。但这需要：
- 实现 ACP over WebSocket
- 扩展协议支持多 agent 广播
- 修改 SessionManager 支持 agent 间消息路由

**当前不推荐**：改造成本过高，不如基于现有的 six-ministries-hub 模式继续开发。

## 相关代码

```python
# acp_adapter/server.py - 核心入口
class HermesACPAgent(acp.Agent):
    async def handle_message(self, message):
        # 处理 ACP 消息
        pass

# agent/copilot_acp_client.py - 反向： Hermes 作为 Copilot ACP client
"""
这是 Hermes 调用 GitHub Copilot ACP 的客户端
可以参考它的实现方式
"""
```

## 关键启发

ACP 的工具映射机制（tools.py）值得借鉴：
- 统一的 ToolKind 枚举
- 工具名称到 kind 的显式映射
- 缺失工具默认返回 "other"

这个模式可以用在我们的 Hub 消息类型系统中。
