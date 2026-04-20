# A2A (Agent-to-Agent) 协议

> 分析日期：2026-04-20
> 来源：https://github.com/google/A2A | https://a2a-protocol.org

## 协议概述

**A2A 是 Google 开发的开放协议**，让不同框架、不同公司、不同服务器上的 AI Agent 能够互相通信和协作。

```
A2A 解决的核心问题：
不同 Agent（可能用不同框架、不同公司开发、运行在不同服务器上）
如何在不暴露内部状态/记忆/工具的情况下，协作完成任务？
```

## 核心特性

| 特性 | 说明 |
|------|------|
| **标准化通信** | JSON-RPC 2.0 over HTTP(S) |
| **Agent 发现** | 通过 "Agent Cards" 发现彼此能力 |
| **三种交互模式** | 同步请求/响应、Streaming (SSE)、异步推送 |
| **丰富数据交换** | 支持文本、文件、JSON |
| **企业级** | 安全、认证、可观测 |

## 核心概念

### 1. Agent Card

每个 Agent 有一个公开的 JSON 描述文件（`.well-known/agent-card.json`）：

```json
{
  "name": "工部尚书",
  "description": "负责基础设施和工程任务",
  "url": "http://localhost:18800/a2a/jsonrpc",
  "skills": [
    {"id": "infrastructure", "name": "基础设施", "description": "服务器运维"},
    {"id": "coding", "name": "编码", "description": "代码开发和调试"}
  ]
}
```

### 2. 任务 (Task)

A2A 是**任务导向**的：

```
Task 生命周期：
submitted → working → completed/failed/canceled
           ↓
         可选：input-required（需要更多输入）
```

### 3. 核心 RPC 方法

| 方法 | 说明 |
|------|------|
| `send_message` | 发送消息（同步） |
| `send_streaming_message` | 流式发送 |
| `get_task` | 查询任务状态 |
| `list_tasks` | 列出任务 |
| `cancel_task` | 取消任务 |

### 4. 消息流（对应用户描述的模式）

```
Agent 1 (Coordinator)              Agent 2 (Worker)
      |                                  |
      |── send_message(task) ──────────→ |
      |     (taskId: "t123")             |── 执行任务
      |                                  |── 完成
      |←── task result ──────────────── |
      |     (taskId: "t123")             |
      |                                  |
      └──── 汇总结果 ────────────────────┘
```

这正是用户描述的：
1. Agent 1 派发任务给 Agent 2
2. Agent 2 完成任务后汇报 Agent 1
3. Agent 1 汇总

## A2A SDK

有多个语言的 SDK：

| 语言 | SDK |
|------|-----|
| Python | `pip install a2a-sdk` |
| Go | `go get github.com/a2aproject/a2a-go` |
| JS/TS | `npm install @a2a-js/sdk` |
| Java | Maven |
| .NET | `dotnet add package A2A` |

## OpenClaw A2A Gateway 插件

**win4r/openclaw-a2a-gateway** (⭐443) 是 OpenClaw 的 A2A 实现：

```
OpenClaw Server A (A2A Gateway :18800)  ←── A2A/JSON-RPC ──→  OpenClaw Server B (A2A Gateway :18800)
      │                                                                    │
      └── Agent: 工部尚书                                                     └── Agent: 户部尚书
```

**关键能力**：
- **智能路由**：按技能/标签路由到合适的 Agent
- **Peer 发现**：DNS-SD、mDNS 自动发现
- **熔断器**：四态仿生熔断（closed → desensitized → open → recovering）
- **自适应传输**：JSON-RPC → REST → gRPC 自动降级
- **任务持久化**：磁盘存储任务状态

## 关键发现：Hermes 能否接入 A2A？

**当前架构问题**：

```
OpenClaw A2A Gateway（:18800）
    │
    └── OpenClaw agents（dev/main/hubu 等）
            └── 通过 openclaw-cn 调用
            └── 通过 A2A 协议与其他 OpenClaw agent 通信 ✅

我们的 Hermes Agent
    │
    └── Hermes Gateway（飞书 WebSocket）
            └── 不是 OpenClaw agent
            └── 不在 OpenClaw agents 目录中
            └── ❌ 无法直接用 A2A 通信
```

**可能的方案**：

| 方案 | 描述 | 难度 |
|------|------|------|
| **Hermes 作为 A2A Client** | Hermes 连接 OpenClaw A2A Gateway，作为 Client 发消息给 OpenClaw agents | 中 |
| **Hermes 暴露 A2A Server** | Hermes 实现 A2A Server 端，OpenClaw agents 作为 A2A Client | 高 |
| **Hub 桥接** | six-ministries-hub 同时支持 A2A 协议和飞书 | 高 |

**最可行方案**：Hermes 作为 A2A Client，接入 OpenClaw A2A Gateway

```
Hermes Agent（我们）
    │
    └── Hermes A2A Client SDK
            │
            └── HTTP/JSON-RPC ──→ OpenClaw A2A Gateway（:18800）
                                        │
                                        └── OpenClaw agents（工部/户部/...）
```

## 安装 A2A Gateway 插件到我们的 OpenClaw

```bash
openclaw plugins install openclaw-a2a-gateway
# 或从源码安装
mkdir -p ~/.openclaw/workspace/plugins
git clone https://github.com/win4r/openclaw-a2a-gateway.git a2a-gateway
cd a2a-gateway && npm install --production
openclaw plugins install ~/.openclaw/workspace/plugins/a2a-gateway
openclaw gateway restart
```

## 验证

```bash
curl -s http://localhost:18800/.well-known/agent-card.json | python3 -m json.tool
```

## 下一步

1. 在我们的 OpenClaw 上安装 a2a-gateway 插件
2. 研究 Hermes 如何作为 A2A Client 接入
3. 用 Python A2A SDK 测试 Hermes → OpenClaw agent 通信

## 链接

- A2A 协议规范：https://a2a-protocol.org/latest/specification/
- OpenClaw A2A Gateway：https://github.com/win4r/openclaw-a2a-gateway
- A2A Python SDK：`pip install a2a-sdk`
- A2A JS SDK：`npm install @a2a-js/sdk`
