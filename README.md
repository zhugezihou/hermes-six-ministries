# hermes-six-ministries

基于 Google A2A 协议的六部尚书多 Agent 协调系统。

中书令（Hermes Agent）通过 A2A 协议并行调度工部、户部、礼部、兵部、刑部、吏部六个专业 AI Agent，实现任务分解、并行执行与结果汇总。

## 架构

```
中书令 (Hermes Agent)
    │
    ├─ A2A Client (Python)
    │       │
    │       ├─ HTTP → A2A Gateway (:18800) — 任务管理
    │       └─ CLI  → OpenClaw Gateway (:18789) — Agent 调度
    │
    ▼
六部尚书 (OpenClaw Agents)
    工部 │ 户部 │ 礼部 │ 兵部 │ 刑部 │ 吏部
```

## 目录结构

```
hermes-six-ministries/
├── a2a_client/                    # 六部尚书 A2A Client
│   ├── six_ministries_a2a_client.py
│   └── requirements.txt
├── hermes_integration/            # Hermes Agent 工具集成
│   ├── six_ministries_tool.py
│   └── skill/SKILL.md
├── docs/
│   ├── protocols/                  # 协议分析
│   │   ├── a2a-protocol.md
│   │   ├── acp-analysis.md
│   │   └── openclaw-api.md
│   └── architecture/               # 架构文档
│       └── README.md
├── examples/                       # 使用示例
│   └── README.md
└── README.md                       # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置 OpenClaw Gateway

确保 OpenClaw Gateway 运行在 `localhost:18789`，并已注册六部尚书 agents。

### 3. 安装 Hermes 集成工具

将 `hermes_integration/six_ministries_tool.py` 复制到 Hermes Agent 的 tools 目录：

```bash
cp -r hermes_integration/ ~/.hermes/hermes-agent/tools/
```

在 `toolsets.py` 中添加 `six_ministries` toolset。

### 4. 使用

```bash
# 单部门调度
python a2a_client/six_ministries_a2a_client.py --agent dev --message "检查服务器状态"

# 全六部并行调度
python a2a_client/six_ministries_a2a_client.py --agent all --message "汇报当前状态" --summarize

# 指定多部门并行
python a2a_client/six_ministries_a2a_client.py --parallel dev hubu content --message "检查基础设施" --summarize
```

## Agent ID 映射

| Agent ID  | 部门       |
|-----------|-----------|
| dev       | 工部尚书   |
| hubu      | 户部尚书   |
| content   | 礼部尚书   |
| bingbu    | 兵部尚书   |
| xingbu    | 刑部尚书   |
| main      | 吏部尚书   |

## 核心模块说明

### A2A Client (`a2a_client/`)

纯 Python 实现的六部尚书调度客户端。通过 `openclaw-cn agent` CLI 与 OpenClaw Gateway 通信，支持并行调度和结果汇总。

### Hermes 集成 (`hermes_integration/`)

将六部尚书调度封装为 Hermes Agent 原生工具 `six_ministries_dispatch`，模型可直接调用。

### 协议分析 (`docs/protocols/`)

- `a2a-protocol.md` — Google A2A v0.3.0 协议分析
- `acp-analysis.md` — OpenClaw ACP 协议分析
- `openclaw-api.md` — OpenClaw Agent API 分析

## 技术背景

本项目源于对 Google A2A (Agent-to-Agent) 协议的实践探索。OpenClaw Gateway 支持 A2A 协议（端口 18800 HTTP / 18801 gRPC），但与 OpenClaw 自身 dispatch 的 Ed25519 签名机制存在兼容性问题。因此采用 CLI 桥接方案作为临时解决方案。

## License

Apache 2.0
