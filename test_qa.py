#!/usr/bin/env python3
"""
简单的问答系统测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.llm import MockLLM
from app.agents.qa_agent import QAAgent
from app.schema.schema import QuestionAnswerState


async def test_basic_qa():
    """测试基础问答功能"""
    print("=== 测试基础问答功能 ===")
    
    # 初始化组件
    llm = MockLLM()
    qa_agent = QAAgent(llm)
    
    # 测试问题
    test_questions = [
        "你好",
        "什么是LangGraph?",
        "今天天气怎么样?"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        
        # 创建状态
        state = QuestionAnswerState(question=question)
        
        # 处理问题
        result = await qa_agent.process_question(state)
        
        print(f"回答: {result.answer}")
        print(f"元数据: {result.metadata}")


async def test_contextual_qa():
    """测试上下文问答功能"""
    print("\n=== 测试上下文问答功能 ===")
    
    # 初始化组件
    llm = MockLLM()
    qa_agent = QAAgent(llm)
    
    # 模拟对话
    conversation = [
        "你好",
        "我叫小明",
        "你还记得我的名字吗?"
    ]
    
    context = {"previous_messages": []}
    
    for question in conversation:
        print(f"\n用户: {question}")
        
        # 创建状态
        state = QuestionAnswerState(
            question=question,
            context=context
        )
        
        # 处理问题
        result = await qa_agent.process_with_context(state)
        
        print(f"助手: {result.answer}")
        
        # 更新上下文
        context = result.context


async def main():
    """主测试函数"""
    print("LangGraph 问答系统测试")
    print("=" * 40)
    
    try:
        await test_basic_qa()
        await test_contextual_qa()
        print("\n" + "=" * 40)
        print("所有测试完成!")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 