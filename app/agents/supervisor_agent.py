import re
import json
from app.llm import LLM
from typing import Dict, Any
from app.agents.qa_agent import QAAgent
from app.agents.doc_agent import DocAgent
from app.schema import QuestionAnswerState
from app.agents.vision_agent import VisionAgent
from app.agents.toolcall_agent import ToolCallAgent
from app.tools.image_segmentation_tool import ImageSegmentationTool

class SuperVisorAgent(ToolCallAgent):
    def __init__(self, llm: LLM):
        self.llm = llm
        self.agents = {
            'qa': QAAgent(llm),
            'vision': VisionAgent(llm, ImageSegmentationTool()),
            'segmentation': ImageSegmentationTool(),
            # 'detection': DetectionAgent(llm)
        }
        self.word_agent = DocAgent()


    
    
    async def process_request(self, state: QuestionAnswerState) -> QuestionAnswerState:
        """协调处理请求"""
        
        # 第一步：大模型分析用户意图
        intent_analysis = await self._analyze_intent(state)
        
        # 第二步：决定调用哪个Agent
        agent_name = await self._select_agent(intent_analysis)
        
        # 第三步：调用选定的Agent
        selected_agent: ToolCallAgent = self.agents[agent_name]
        result: QuestionAnswerState = await selected_agent.process_question(state)
        if agent_name == "vision":
            self.word_agent.write_analysis(result, title="视觉分析结果")
        return result
    
    async def _analyze_intent(self, state: QuestionAnswerState) -> Dict:
        """分析用户意图"""
        prompt = f"""
        用户问题：{state.question}
        是否有图片：{'是' if state.image_data else '否'}
        
        请分析用户意图，返回JSON格式：
        {{
            "task_type": "qa|vision",
            "requires_image": true|false,
            "description": "任务描述"
        }}
        """
        
        response = await self.llm.generate(prompt)
        json_str = response
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            json_str = match.group(0)
        return json.loads(json_str)
    
    async def _select_agent(self, intent: Dict) -> str:
        """选择要调用的Agent"""
        return intent['task_type']