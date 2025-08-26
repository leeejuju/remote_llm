# 基于LangGraph实现问答系统指南

## 概述

LangGraph是一个用于构建LLM应用的框架，特别适合创建复杂的问答系统。本指南展示了如何使用LangGraph实现不同类型的问答系统。

## 核心概念

### 1. 状态图 (StateGraph)
LangGraph的核心是状态图，它定义了数据如何在节点间流动：

```python
from langgraph.graph import StateGraph, END

# 定义状态类型
class QAState(TypedDict):
    question: str
    answer: str | None
    metadata: Dict[str, Any]

# 创建状态图
workflow = StateGraph(QAState)

# 添加节点
workflow.add_node("process_question", process_question)

# 设置边
workflow.add_edge("process_question", END)

# 编译图
graph = workflow.compile()
```

### 2. 节点 (Nodes)
节点是图中的处理单元，每个节点接收状态并返回更新后的状态：

```python
async def process_question(state: QAState) -> QAState:
    """处理问题并生成回答"""
    question = state["question"]
    
    # 生成回答
    answer = await llm.generate(question)
    
    # 更新状态
    state["answer"] = answer
    state["metadata"]["processed"] = True
    
    return state
```

### 3. 条件路由 (Conditional Edges)
使用条件边实现智能路由：

```python
def route_question(state: QAState) -> str:
    """路由问题"""
    analysis = state.get("metadata", {}).get("analysis", "")
    
    if analysis == "question_too_short":
        return "end"
    else:
        return "process"

# 添加条件边
workflow.add_conditional_edges(
    "analyze_question",
    route_question,
    {
        "process": "process_question",
        "end": END
    }
)
```

## 问答系统实现类型

### 1. 基础问答系统

最简单的问答形式，直接处理用户问题：

```python
def create_basic_qa_graph() -> StateGraph:
    """创建基础问答图"""
    workflow = StateGraph(QAState)
    
    # 添加节点
    workflow.add_node("process_question", process_question)
    
    # 设置入口点
    workflow.set_entry_point("process_question")
    
    # 设置结束点
    workflow.add_edge("process_question", END)
    
    return workflow.compile()
```

**特点：**
- 单轮对话
- 无上下文记忆
- 快速响应

### 2. 上下文问答系统

支持多轮对话，能够记住对话历史：

```python
def create_contextual_qa_graph() -> StateGraph:
    """创建带上下文的问答图"""
    workflow = StateGraph(QAState)
    
    # 添加节点
    workflow.add_node("process_with_context", process_with_context)
    
    # 设置入口点
    workflow.set_entry_point("process_with_context")
    
    # 设置结束点
    workflow.add_edge("process_with_context", END)
    
    return workflow.compile()
```

**特点：**
- 多轮对话支持
- 上下文记忆
- 对话连贯性

### 3. 多步骤问答系统

包含问题分析、处理和验证的完整流程：

```python
def create_multi_step_qa_graph() -> StateGraph:
    """创建多步骤问答图"""
    workflow = StateGraph(QAState)
    
    # 添加节点
    workflow.add_node("analyze_question", analyze_question)
    workflow.add_node("process_question", process_question)
    workflow.add_node("validate_answer", validate_answer)
    
    # 设置入口点
    workflow.set_entry_point("analyze_question")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "analyze_question",
        route_question,
        {
            "process": "process_question",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "process_question",
        route_after_process,
        {
            "validate": "validate_answer",
            "end": END
        }
    )
    
    workflow.add_edge("validate_answer", END)
    
    return workflow.compile()
```

**特点：**
- 问题质量检查
- 回答验证
- 智能路由

### 4. 工具增强问答系统

集成外部工具来增强回答能力：

```python
def create_advanced_qa_graph() -> StateGraph:
    """创建带工具的进阶问答图"""
    workflow = StateGraph(AdvancedQAState)
    
    # 添加节点
    workflow.add_node("analyze_question", analyze_question)
    workflow.add_node("search_knowledge", search_knowledge)
    workflow.add_node("calculate", calculate)
    workflow.add_node("generate_answer", generate_answer)
    
    # 设置入口点
    workflow.set_entry_point("analyze_question")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "analyze_question",
        route_after_analysis,
        {
            "search": "search_knowledge",
            "calculate": "calculate",
            "direct": "generate_answer",
            "end": END
        }
    )
    
    workflow.add_edge("search_knowledge", "generate_answer")
    workflow.add_edge("calculate", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()
```

**特点：**
- 自动工具选择
- 多工具集成
- 智能增强

## 实现步骤

### 步骤1：定义状态结构

```python
from typing import Dict, Any, TypedDict

class QAState(TypedDict):
    question: str
    answer: str | None
    context: Dict[str, Any]
    metadata: Dict[str, Any]
```

### 步骤2：创建LLM接口

```python
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

class MockLLM(BaseLLM):
    async def generate(self, prompt: str, **kwargs) -> str:
        # 实现LLM调用逻辑
        return "回答内容"
```

### 步骤3：实现处理节点

```python
async def process_question(state: QAState) -> QAState:
    llm = MockLLM()
    question = state["question"]
    
    answer = await llm.generate(question)
    state["answer"] = answer
    state["metadata"]["processed"] = True
    
    return state
```

### 步骤4：创建图

```python
def create_qa_graph() -> StateGraph:
    workflow = StateGraph(QAState)
    
    workflow.add_node("process_question", process_question)
    workflow.set_entry_point("process_question")
    workflow.add_edge("process_question", END)
    
    return workflow.compile()
```

### 步骤5：运行图

```python
async def main():
    graph = create_qa_graph()
    
    result = await graph.ainvoke({
        "question": "你好",
        "answer": None,
        "context": {},
        "metadata": {}
    })
    
    print(result["answer"])

asyncio.run(main())
```

## 最佳实践

### 1. 状态设计
- 使用TypedDict定义清晰的状态结构
- 避免在状态中存储过多数据
- 保持状态的不可变性

### 2. 错误处理
```python
async def process_question(state: QAState) -> QAState:
    try:
        # 处理逻辑
        pass
    except Exception as e:
        state["error"] = str(e)
        state["metadata"]["failed"] = True
    return state
```

### 3. 异步支持
- 使用async/await处理异步操作
- 避免阻塞操作
- 合理使用并发

### 4. 工具集成
```python
class SearchTool:
    async def search(self, query: str) -> List[Dict[str, Any]]:
        # 实现搜索逻辑
        pass

async def search_knowledge(state: QAState) -> QAState:
    tool = SearchTool()
    results = await tool.search(state["question"])
    state["context"]["search_results"] = results
    return state
```

### 5. 测试
```python
async def test_qa_graph():
    graph = create_qa_graph()
    
    result = await graph.ainvoke({
        "question": "测试问题",
        "answer": None,
        "context": {},
        "metadata": {}
    })
    
    assert result["answer"] is not None
    assert result["metadata"]["processed"] is True
```

## 扩展建议

### 1. 添加更多工具
- 计算器工具
- 搜索工具
- 文件处理工具
- API调用工具

### 2. 增强状态管理
- 持久化状态
- 状态版本控制
- 状态回滚

### 3. 优化性能
- 缓存机制
- 并行处理
- 资源管理

### 4. 监控和日志
- 性能监控
- 错误追踪
- 用户行为分析

## 总结

基于LangGraph实现问答系统的优势：

1. **模块化设计**: 每个组件都是独立的，易于维护和扩展
2. **状态管理**: 内置的状态管理机制，简化了复杂流程
3. **条件路由**: 支持智能路由，实现复杂的业务逻辑
4. **异步支持**: 原生支持异步操作，提高性能
5. **可扩展性**: 易于添加新功能和工具
6. **可测试性**: 每个节点都可以独立测试

通过LangGraph，我们可以构建从简单到复杂的各种问答系统，满足不同的业务需求。 