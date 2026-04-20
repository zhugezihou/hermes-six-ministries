# 架构文档

## 系统概述

hermes-six-ministries 是一个运行在 OpenClaw Gateway 上的多 Agent 协调系统。中书令（Hermes Agent）作为协调者，通过 A2A 协议调度六个专业 Agent（工部、户部、礼部、兵部、刑部、吏部）并行执行任务。

## 组件关系

```
┌─────────────────────────────────────────────────────────────┐
│  Hermes Agent（中书令）                                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  six_ministries_dispatch 工具                         │  │
│  │  (Hermes 原生工具)                                    │  │
│  └─────────────────────┬───────────────────────────────┘  │
└────────────────────────┼──────────────────────────────────┘
                         │ six_ministries_a2a_client.py
                         │
┌────────────────────────┼──────────────────────────────────┐
│  ┌─────────────────────▼───────────────────────────────┐  │
│  │  A2A Gateway (:18800)                               │  │
│  │  - 任务管理 / Task Store                             │  │
│  │  - Agent Card (.well-known/agent-card.json)         │  │
│  │  - Bearer Token 认证                                │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │ dispatch (Ed25519, 兼容性问题)   │
│  ┌─────────────────────▼───────────────────────────────┐  │
│  │  OpenClaw Gateway (:18789)                          │  │
│  │  - WebSocket + Ed25519 设备签名                     │  │
│  │  - Agent Registry                                   │  │
│  │  - sessions / dispatch                             │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │ openclaw-cn agent --agent <id>    │
└────────────────────────┼──────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐      ┌─────────┐      ┌─────────┐
│ 工部    │      │ 户部    │      │ 礼部    │
│ dev     │      │ hubu    │      │ content │
└─────────┘      └─────────┘      └─────────┘
    ┌────────────────────┬────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐      ┌─────────┐      ┌─────────┐
│ 兵部    │      │ 刑部    │      │ 吏部    │
│ bingbu  │      │ xingbu  │      │ main    │
└─────────┘      └─────────┘      └─────────┘

六部尚书
(OpenClaw Agents)
```

## 通信方式

### 中书令 → 六部尚书

1. **Hermes 工具调用**（推荐）：模型调用 `six_ministries_dispatch` 工具
2. **CLI 直接调度**：`openclaw-cn agent --agent <id> --message "..."`

### 六部尚书 → 中书令

各部通过飞书群聊（`channel=feishu`，`peer=oc_d860f9f653e3421db6ea419a81414cf6`）向中书令汇报。

## A2A Gateway 说明

A2A Gateway（`win4r/openclaw-a2a-gateway`）实现了 Google A2A v0.3.0 协议，提供：
- HTTP JSON-RPC（:18800）
- gRPC（:18801）
- DNS-SD / mDNS 自动发现
- Bearer Token 认证

**已知限制**：A2A Gateway 的 outbound dispatch 使用 HMAC-SHA256，与 OpenClaw Gateway 要求的 Ed25519 签名不兼容。因此实际调度通过 `openclaw-cn CLI` 执行，A2A Gateway 负责任务追踪。

## 飞书集成

六部尚书的飞书绑定通过 OpenClaw 的 bindings 配置实现：

```json
{
  "agentId": "dev",
  "match": {
    "channel": "feishu",
    "accountId": "gongbu",
    "peer": { "kind": "group", "id": "oc_d860f9f653e3421db6ea419a81414cf6" }
  }
}
```

朝堂群 ID：`oc_d860f9f653e3421db6ea419a81414cf6`
