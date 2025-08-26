#!/usr/bin/env python3
"""
基于LangGraph的简单问答系统演示
"""

import asyncio
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END


# 定义状态类型
class QAState(TypedDict):
    question: str
    answer: str | None
    metadata: Dict[str, Any]


# 模拟LLM
class MockLLM:
    def __init__(self):
        self.responses = {
            "你好": "你好！我是基于LangGraph的问答助手。",
            "什么是LangGraph": "LangGraph是一个用于构建LLM应用的框架，支持状态管理和工作流编排。",
            "天气": "抱歉，我无法获取实时天气信息。",
            "时间": "我无法获取当前时间，建议您查看设备时间。"
        }
    
    async def generate(self, question: str) -> str:
        # 简单的关键词匹配
        for key, response in self.responses.items():
            if key in question:
                return response
        return "这是一个模拟的回答。"


# 问答处理节点
async def process_question(state: QAState) -> QAState:
    """处理问题并生成回答"""
    llm = MockLLM()
    question = state["question"]
    
    # 生成回答
    answer = await llm.generate(question)
    
    # 更新状态
    state["answer"] = answer
    state["metadata"]["processed"] = True
    
    return state


# 问题分析节点
def analyze_question(state: QAState) -> QAState:
    """分析问题"""
    question = state["question"]
    
    # 简单的分析逻辑
    if len(question) < 5:
        state["metadata"]["analysis"] = "question_too_short"
        state["metadata"]["confidence"] = "low"
    elif "?" in question:
        state["metadata"]["analysis"] = "proper_question"
        state["metadata"]["confidence"] = "high"
    else:
        state["metadata"]["analysis"] = "statement"
        state["metadata"]["confidence"] = "medium"
    
    return state


# 路由函数
def route_question(state: QAState) -> str:
    """路由问题"""
    analysis = state.get("metadata", {}).get("analysis", "")
    
    if analysis == "question_too_short":
        return "end"
    else:
        return "process"


# 创建基础问答图
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


# 创建多步骤问答图
def create_multi_step_qa_graph() -> StateGraph:
    """创建多步骤问答图"""
    workflow = StateGraph(QAState)
    
    # 添加节点
    workflow.add_node("analyze_question", analyze_question)
    workflow.add_node("process_question", process_question)
    
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
    
    workflow.add_edge("process_question", END)
    
    return workflow.compile()


async def demo_basic_qa():
    """演示基础问答"""
    print("=== 基础问答演示 ===")
    
    graph = create_basic_qa_graph()
    
    questions = [
        "你好",
        "什么是LangGraph",
        "今天天气怎么样?"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        
        result = await graph.ainvoke({
            "question": question,
            "answer": None,
            "metadata": {}
        })
        
        print(f"回答: {result['answer']}")


async def demo_multi_step_qa():
    """演示多步骤问答"""
    print("\n=== 多步骤问答演示 ===")
    
    graph = create_multi_step_qa_graph()
    
    questions = [
        "hi",  # 太短的问题
        "什么是LangGraph?",  # 正常问题
        "Python是什么?"  # 另一个正常问题
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        
        result = await graph.ainvoke({
            "question": question,
            "answer": None,
            "metadata": {}
        })
        
        print(f"回答: {result['answer']}")
        print(f"元数据: {result['metadata']}")


async def interactive_qa():
    """交互式问答"""
    print("\n=== 交互式问答 ===")
    print("请输入您的问题（输入 'quit' 退出）:")
    
    graph = create_basic_qa_graph()
    
    while True:
        try:
            question = input("\n您: ").strip()
            
            if question.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            
            if not question:
                continue
            
            result = await graph.ainvoke({
                "question": question,
                "answer": None,
                "metadata": {}
            })
            
            print(f"助手: {result['answer']}")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


async def main():
    """主函数"""
    print("基于LangGraph的问答系统演示")
    print("=" * 50)
    
    # 运行演示
    await demo_basic_qa()
    await demo_multi_step_qa()
    
    # 询问是否进行交互式演示
    response = input("\n是否进行交互式演示? (y/n): ").strip().lower()
    if response in ['y', 'yes', '是']:
        await interactive_qa()
    
    print("\n演示完成!")


if __name__ == "__main__":
    asyncio.run(main()) 