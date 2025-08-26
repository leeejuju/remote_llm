from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from app.schema.schema import QuestionAnswerState
from app.agents.qa_agent import QAAgent
from app.agents.supervisor_agent import CoordinatorAgent


class QAState(TypedDict):
    """问答图状态"""
    question: str
    answer: str | None
    context: Dict[str, Any]
    metadata: Dict[str, Any]


def create_qa_graph(coordinator_agent: CoordinatorAgent) -> StateGraph:
    """创建问答图"""
    
    # 创建状态图
    workflow = StateGraph(QuestionAnswerState)
    
    # 添加节点
    workflow.add_node("process_question", coordinator_agent.process_request)
    
    # 设置入口点
    workflow.set_entry_point("process_question")
    
    # 设置结束点
    workflow.add_edge("process_question", END)
    
    # 编译图
    return workflow.compile()


def create_contextual_qa_graph(qa_agent: QAAgent) -> StateGraph:
    """创建带上下文的问答图"""
    
    # 创建状态图
    workflow = StateGraph(QAState)
    
    # 添加节点
    workflow.add_node("process_with_context", qa_agent.process_with_context)
    
    # 设置入口点
    workflow.set_entry_point("process_with_context")
    
    # 设置结束点
    workflow.add_edge("process_with_context", END)
    
    # 编译图
    return workflow.compile()


def create_multi_step_qa_graph(qa_agent: QAAgent) -> StateGraph:
    """创建多步骤问答图"""
    
    # 创建状态图
    workflow = StateGraph(QAState)
    
    # 添加节点
    workflow.add_node("analyze_question", analyze_question)
    workflow.add_node("process_question", qa_agent.process_question)
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
    
    # 编译图
    return workflow.compile()


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


def validate_answer(state: QAState) -> QAState:
    """验证回答"""
    answer = state.get("answer", "")
    
    if not answer:
        state["answer"] = "抱歉，我无法回答这个问题。"
        state["metadata"]["validation"] = "no_answer"
    elif len(answer) < 10:
        state["metadata"]["validation"] = "answer_too_short"
    else:
        state["metadata"]["validation"] = "answer_valid"
    
    return state


def route_question(state: QAState) -> str:
    """路由问题"""
    analysis = state.get("metadata", {}).get("analysis", "")
    
    if analysis == "question_too_short":
        return "end"
    else:
        return "process"


def route_after_process(state: QAState) -> str:
    """处理后的路由"""
    answer = state.get("answer", "")
    
    if not answer:
        return "end"
    else:
        return "validate" 