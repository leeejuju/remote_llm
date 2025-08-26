from typing import Dict, Any, List
import asyncio


class SearchTool:
    """搜索工具示例"""
    
    def __init__(self):
        self.knowledge_base = {
            "LangGraph": "LangGraph是一个用于构建LLM应用的框架，支持状态管理和工作流编排。",
            "问答系统": "问答系统是一种能够理解用户问题并提供准确回答的AI系统。",
            "Python": "Python是一种高级编程语言，以其简洁的语法和丰富的库而闻名。",
            "机器学习": "机器学习是人工智能的一个分支，通过算法让计算机从数据中学习。"
        }
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索知识库"""
        results = []
        
        # 简单的关键词匹配
        for key, content in self.knowledge_base.items():
            if query.lower() in key.lower() or query.lower() in content.lower():
                results.append({
                    "title": key,
                    "content": content,
                    "relevance": 0.8
                })
        
        # 模拟异步延迟
        await asyncio.sleep(0.1)
        
        return results
    
    async def get_relevant_context(self, question: str) -> str:
        """获取相关问题上下文"""
        results = await self.search(question)
        
        if results:
            context = "\n".join([f"{r['title']}: {r['content']}" for r in results])
            return f"相关上下文:\n{context}"
        else:
            return "未找到相关信息。"


class CalculatorTool:
    """计算器工具"""
    
    async def calculate(self, expression: str) -> str:
        """安全计算数学表达式"""
        try:
            # 只允许安全的数学运算
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return "表达式包含不安全的字符"
            
            result = eval(expression)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}" 