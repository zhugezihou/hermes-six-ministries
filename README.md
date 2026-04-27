# hermes-six-ministries

基于 Google A2A 协议的六部尚书多 Agent 协调系统。

中书令（Hermes Agent）通过 A2A 协议直接调度工部、户部、礼部、兵部、刑部、吏部六个专业 AI Agent，实现任务分解、并行执行与结果汇总。

## 架构（最新直连方案）

```
中书令 (Hermes Agent)
    │
    │  HTTP POST (Bearer token)
    │  POST http://127.0.0.1:18800/a2a/jsonrpc
    │
    ▼
A2A Gateway (:18800)
    │  Bearer token: <YOUR_BEARER_TOKEN>
    │
    ▼
六部尚书 (OpenClaw Agents)
工部 │ 户部 │ 礼部 │ 兵部 │ 刑部 │ 吏部
```

**无中间层，无 bridge，纯直连。**

## 目录结构

```
hermes-six-ministries/
├── a2a_client/                    # 六部尚书 A2A Client
│   ├── six_ministries_a2a_client.py
│   └── requirements.txt
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

### 2. 配置 A2A Gateway

启动 OpenClaw Gateway，确保端口 `18800` 可访问。

### 3. 调度六部

```bash
# 单部门调度
python a2a_client/six_ministries_a2a_client.py --agent dev --message "检查服务器状态"

# 全六部并行调度
python a2a_client/six_ministries_a2a_client.py --agent all --message "汇报当前状态" --summarize

# 指定多部门并行
python a2a_client/six_ministries_a2a_client.py --parallel dev hubu content --message "检查基础设施" --summarize
```

## A2A 通信参数

| 项目 | 值 |
|------|-----|
| A2A Gateway HTTP | `http://127.0.0.1:18800/a2a/jsonrpc` |
| Bearer Token | `<YOUR_BEARER_TOKEN>` |
| 调度命令 | `openclaw-cn agent --agent <id> --message "..."` |
| 朝堂群 | `<GROUP_CHAT_ID>` |

## Agent ID 映射

| Agent ID | 部门       |
|-----------|-----------|
| dev       | 工部尚书   |
| hubu      | 户部尚书   |
| content   | 礼部尚书   |
| bingbu    | 兵部尚书   |
| xingbu    | 刑部尚书   |
| main      | 吏部尚书   |

## 双向通信流程

```
1. 皇上 → 中书令：下达任务
2. 中书令 → A2A Gateway：派发给对应部门
3. 六部 → A2A Gateway：完成任务后回复中书令
4. 中书令 → 皇上：汇总六部结果上报
```

## 核心模块说明

### A2A Client (`a2a_client/`)

纯 Python 实现的六部尚书调度客户端。直接 HTTP POST 到 A2A Gateway（Bearer token 认证），无需 CLI 桥接，支持并行调度和结果汇总。

### 协议分析 (`docs/protocols/`)

- `a2a-protocol.md` — Google A2A v0.3.0 协议分析
- `acp-analysis.md` — OpenClaw ACP 协议分析
- `openclaw-api.md` — OpenClaw Agent API 分析

## License

Apache 2.0
