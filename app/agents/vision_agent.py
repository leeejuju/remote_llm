import base64
from ast import List
from app.llm import LLM
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from app.schema import QuestionAnswerState
from app.tools.image_segmentation_tool import ImageSegmentationTool


class VisionAgent(BaseAgent):
    def __init__(self, llm: LLM, segmentation_tool: ImageSegmentationTool):
        self.llm = llm
        self.segmentation_tool = segmentation_tool
    
    async def process_question(self, state: QuestionAnswerState) -> QuestionAnswerState:
        """处理图像请求"""
        # 第一步：大模型理解用户意图
        intent_prompt = f"""
        用户问题：{state.question}
        请分析用户想要什么操作，只返回以下关键词之一：
        - segmentation (分割)
        - detection (检测)
        - analysis (分析)
        """
        intent = (await self.llm.generate(intent_prompt)).strip().lower()

        def to_base64_str(image_bytes):
            return base64.b64encode(image_bytes).decode("utf-8")

       
        # 第二步：根据意图调用相应工具
        if 'segmentation' in intent:
            # 调用YOLO分割
            segmented_image, seg_info, seg_image_path = self.segmentation_tool.\
                segment_image(
                    image_data = state.image_data
                    , image_format=state.image_format)
            state.segmented_image = segmented_image
            state.segmentation_info = seg_info
            state.segmented_image_path = seg_image_path
            
            analysis_prompt = f"""
            你是一名顶尖的遥感专家，擅长用精炼清晰的语言解答遥感问题
            我已经对图像进行了分割，检测到以下对象：
            {self._format_segmentation_info(seg_info)}
            用户的问题是：{state.question}
            
            请基于分割结果图以及原图，根据置信度用自然语言回答用户的问题而非图片检测精度\
                ，并给出遥感领域的整体图像解释。
            """
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": analysis_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{to_base64_str(state.segmented_image)}"},
                    },
         
                ],
            )
            # 第三步：将分割结果送回大模型分析
            
            
            final_answer = await self.llm.generate(message)
            state.answer = final_answer
            
        elif 'detection' in intent:
            # 类似的处理逻辑...
            pass
        
        state.metadata["processed"] = True
        return state
    
    def _format_segmentation_info(self, seg_info: List[Dict]) -> str:
        """格式化分割信息"""
        if not seg_info:
            return "未检测到任何对象"
        
        result = []
        for seg in seg_info:
            result.append(f"- {seg['class']} (置信度: {seg['confidence']:.2f})")
        
        return "\n".join(result)