from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.schema.schema import QuestionAnswerState
from app.llm import BaseLLM

class QAAgent(BaseAgent):
    """纯文本问答Agent"""
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
    
    async def process_question(self, state: QuestionAnswerState) -> QuestionAnswerState:
        """处理纯文本问题"""
        answer = await self.llm.generate(state.question)
        state.answer = answer
        state.metadata["processed"] = True
        return state

    async def process_with_context(self, state: QuestionAnswerState) -> QuestionAnswerState:
        """基于上下文处理问题"""
        # 构建上下文消息
        context_messages = []
        if state.context.get("previous_messages"):
            context_messages = state.context["previous_messages"]
        
        # 添加当前问题
        context_messages.append({"role": "user", "content": state.question})
        
        # 生成回答
        answer = await self.llm.generate_with_context(context_messages)
        
        # 更新状态
        state.answer = answer
        state.context["previous_messages"] = context_messages
        state.metadata["processed"] = True
        
        return state 
    

# class QAAgent:
#     """问答代理"""
    
#     def __init__(self, llm: BaseLLM):
#         self.llm = llm
    
#     async def process_question(self, state: QuestionAnswerState) -> QuestionAnswerState:
#         """处理问题并生成回答"""
#         # 生成回答
#         answer = await self.llm.generate(state.question)
        
#         # 更新状态
#         state.answer = answer
#         state.metadata["processed"] = True
        
#         return state
    
