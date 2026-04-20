# OpenClaw API 分析

> 分析日期：2026-04-20
> 来源：GitHub + six-ministries-hub skill

## OpenClaw Gateway 架构

```
openclaw-cn (CLI)
    ↓
openclaw-gateway (Node.js 进程)
    ↓
飞书 / Telegram / Discord 等平台
```

**我们环境的 Gateway**：
- WSL：`localhost:18789`（OpenClaw Gateway）
- Hermes Gateway：`localhost:xxxxx`（Hermes 自有 Gateway）

## 关键命令

### 触发 Agent

```bash
openclaw-cn agent --agent <agent_id> --message "<msg>" [--timeout <sec>]
```

**坑**：
- `agent_id` 不等于飞书 bot 账号名
  - `dev` = 工部尚书（不是 gongbu）
  - `content` = 礼部尚书（不是 libu）
  - `main` = 吏部尚书
- **回复在 stderr，不在 stdout**（Node.js console.log 输出到 stderr）

### 发送消息

```bash
openclaw-cn message send --channel feishu --account <account> --target <chat_id> --message "<msg>"
```

**坑**：
- `--account` 只切换配置，不改变发送者身份
- 实际上还是用 default/main 的 token 发送
- 真正的各部 bot 身份发送需要直接调飞书 API

### 其他命令

```bash
openclaw-cn plugins list           # 查看插件状态
openclaw-cn config get             # 查看配置
openclaw-cn config set <key> <val> # 设置配置
```

## Gateway WebSocket API

从 itq5/OpenClaw-Admin 的 `gateway.js` 可以看到：

```javascript
// Gateway WebSocket 端点（推测）
ws://localhost:18789/gateway

// 消息格式（推测 JSON）
{
  type: "message" | "agent" | "system",
  agent?: string,
  content: string,
  chat_id?: string,
  // ...
}
```

**需要验证**：实际的 Gateway WebSocket 协议格式

## OpenClaw agents 目录

从 `~/.openclaw/agents/` 结构：

```
~/.openclaw/agents/
├── bingbu/
│   ├── agent.json
│   └── ...
├── content/
│   └── ...
├── dev/
│   └── ...
├── hubu/
│   └── ...
├── main/
│   └── ...
└── xingbu/
    └── ...
```

每个 agent 目录包含：
- `agent.json`：agent 配置
- `SOUL.md`（可能有）
- 记忆文件

**注意**：没有 `hermes` 目录 —— Hermes 没有注册为 OpenClaw agent。

## 与 Hermes 的连接点

| 方向 | 方式 | 状态 |
|------|------|------|
| Hermes → OpenClaw agent | `openclaw-cn agent --agent <id> --message` | ✅ 可行 |
| OpenClaw agent → Hermes | `sessions_send` (OpenClaw 内部) | ❌ Hermes 不在 agents 目录 |
| 飞书群消息共享 | 两边都监听同一群 | ✅ 可行但混乱 |
| six-ministries-hub | Hermes Hub 客户端 + 各部 Bridge | ⚠️ 部分实现 |

## 深入研究计划

1. **抓包 Gateway WebSocket**：用 `curl` 或 Python WebSocket 客户端连 `ws://localhost:18789` 抓实际协议
2. **分析 agent.json**：每个 OpenClaw agent 的配置格式
3. **研究 sessions_send**：OpenClaw 内部如何路由消息给 agent
4. **从 OpenClaw-Admin 学习**：itq5 的 `hermes-proxy.js`（43KB）详细分析

## 已知问题

- WSL 飞书 channel 有时 disabled
- Gateway 日志无飞书插件加载记录
- bindings 数组迁移后丢失（WSL 迁移 bug）

## 代码参考

```python
# six-ministries-hub/sdk/agent_sdk.py 中的调用方式
async def call_openclaw_agent(agent_id, message, timeout=60):
    proc = await asyncio.create_subprocess_exec(
        "openclaw-cn", "agent",
        "--agent", agent_id,
        "--message", message,
        "--timeout", str(timeout),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE  # 回复在 stderr！
    )
    stdout, stderr = await proc.communicate()
    return stderr.decode() or stdout.decode()
```
