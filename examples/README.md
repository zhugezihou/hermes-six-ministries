# 使用示例

## 1. CLI 方式（无需 Hermes）

### 单部门调度

```bash
python a2a_client/six_ministries_a2a_client.py \
  --agent dev \
  --message "检查 ComfyUI 是否正常运行"
```

### 全六部并行调度

```bash
python a2a_client/six_ministries_a2a_client.py \
  --agent all \
  --message "汇报当前最重要的一件事" \
  --summarize
```

### 指定多部门并行

```bash
python a2a_client/six_ministries_a2a_client.py \
  --parallel dev hubu content \
  --message "检查基础设施、財務狀況、內容進度" \
  --summarize
```

### 查询任务结果

```bash
python a2a_client/six_ministries_a2a_client.py \
  --task-id <taskId> \
  --wait
```

## 2. Hermes Agent 方式

在 Hermes Agent 对话中，直接让模型调用 `six_ministries_dispatch` 工具：

```
请调度六部尚书汇报当前状态，包括：
1. 工部：基础设施检查
2. 户部：财务状况
3. 礼部：内容进度
4. 兵部：安全状况
5. 刑部：法务状态
6. 吏部：人员管理
```

模型会自动调用 `six_ministries_dispatch(message="...", agents="all", summarize=True)`。

## 3. 飞书群方式

在飞书朝堂群 @中书令 发消息，中书令会调度六部尚书执行并汇总结果。

## Agent ID 参考

| ID       | 部门   | 用途                     |
|----------|--------|------------------------|
| dev      | 工部   | 基础设施、ComfyUI、运维  |
| hubu     | 户部   | 财务、资源、预算          |
| content  | 礼部   | 内容创作、社区管理        |
| bingbu   | 兵部   | 安全、风控、合规          |
| xingbu   | 刑部   | 法务、审计、追踪         |
| main     | 吏部   | 人员、绩效、协调          |
| all      | 全部   | 并行调度全部六部          |
