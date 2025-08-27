from typing import Annotated
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Dict, Any, TypedDict, Optional
from langgraph.graph import END, StateGraph, START, MessagesState

class RSAgentState(MessagesState):
    # 基础输入
    image_id: Annotated[str, "图像ID"]
    task_type: Annotated[str, "User's task type: segmentation, detection, change analysis, etc."]
    sender: Annotated[str, "Agent that sent this message"]

    # 各分析Agent产出
    segmentation_result: Annotated[dict, "Output from segmentation agent"]
    detection_result: Annotated[dict, "Output from detection agent"]
    change_analysis_report: Annotated[str, "Report from change analysis agent"]
    water_analysis_report: Annotated[str, "Water body analysis report"]

    # 讨论阶段
    fusion_state: Annotated[str, "Fusion or consensus state of multiple agents"]
    qa_response: Annotated[str, "Final answer for QA-type queries"]

    # 最终输出
    final_decision: Annotated[str, "Final output/result to return to user"]

