from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Literal
from langgraph.graph import END, StateGraph, START, MessagesState



class AgentState(str, Enum):
    """Agent执行状态枚举类"""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"
    NEXT = ""



class Role(str, Enum):
    """角色消息类型"""
    SYSTEM = "system" #参考Langchain的
    USER = "user"
    ASSISTANT = "assistant"
    AI = "ai"
    TOOL = "tool"
    
ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class ToolChoice(str, Enum):
    """工具选择枚举"""

    NONE = "none" #无需工具
    AUTO = "auto" #自主选择
    REQUIRED = "required" #必须带工具


class Function(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    """消息中的函数类型"""

    id: str
    type: str = "function"
    function: Function

class Message(BaseModel):
    """对话中的消息参数，其实可使用LangGraph代替"""

    role: ROLE_TYPE = Field(...)  # type: ignore
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)

    def __add__(self, other) -> List["Message"]:
        """支持 Message + list 或 Message + Message 的操作"""
        if isinstance(other, list):
            return [self] + other
        elif isinstance(other, Message):
            return [self, other]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )

    def __radd__(self, other) -> List["Message"]:
        """支持 list + Message 的操作"""
        if isinstance(other, list):
            return other + [self]
        else:
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(other).__name__}' and '{type(self).__name__}'"
            )

    def to_dict(self) -> dict:
        """将消息类型转化为字段形式"""
        message = {"role": self.role}
        if self.content is not None:
            message["content"] = self.content
        if self.tool_calls is not None:
            message["tool_calls"] = [tool_call.model_dump() for tool_call in self.tool_calls]
        if self.name is not None:
            message["name"] = self.name
        if self.tool_call_id is not None:
            message["tool_call_id"] = self.tool_call_id
        if self.base64_image is not None:
            message["base64_image"] = self.base64_image
        return message

    @classmethod
    def user_message(
        cls, content: str, base64_image: Optional[Union[str, bytes]] = None
    ) -> "Message":
        """创建用户消息,如果带有图像"""
        return cls(role=Role.USER, content=content, base64_image=base64_image)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """创建系统消息模板"""
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def assistant_message(
        cls, content: Optional[str] = None, base64_image: Optional[str] = None
    ) -> "Message":
        """创建AI消息模板"""
        return cls(role=Role.ASSISTANT, content=content, base64_image=base64_image)

    @classmethod
    def tool_message(
        cls, content: str, name, tool_call_id: str, base64_image: Optional[str] = None
    ) -> "Message":
        """创建Tool调用消息"""
        return cls(
            role=Role.TOOL,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            base64_image=base64_image)

    @classmethod
    def from_tool_calls(
        cls,
        tool_calls: List[Any],
        content: Union[str, List[str]] = "",
        base64_image: Optional[str] = None,
        **kwargs,
    ):
        """Create ToolCallsMessage from raw tool calls.

        Args:
            tool_calls: Raw tool calls from LLM
            content: Optional message content
            base64_image: Optional base64 encoded image
        """
        formatted_calls = [
            {"id": call.id, "function": call.function.model_dump(), "type": "function"}
            for call in tool_calls
        ]
        return cls(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=formatted_calls,
            base64_image=base64_image,
            **kwargs,
        )


class Memory(BaseModel):
    """创建上下文记忆实体类"""
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(default=100)

    def add_message(self, message: Message) -> None:
        """记忆库中添加消息"""
        #TODO 此处可替换为LangGraph的InMemoryVectore类，虽然其底层也是一个字典
        self.messages.append(message)
        # Optional: 如果超过限制，那么直接将消息进行截断
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def add_messages(self, messages: List[Message]) -> None:
        """多重消息都塞入Memo"""
        self.messages.extend(messages)
        # Optional: 如果超过限制，那么直接将消息进行截断
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        """清除消息"""
        self.messages.clear()

    def get_recent_messages(self, n: int) -> List[Message]:
        """获得最近N轮对话"""
        return self.messages[-n:]

    def to_dict_list(self) -> List[dict]:
        """消息转化为字典"""
        return [msg.to_dict() for msg in self.messages]


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatState(BaseModel):
    """聊天状态模型"""
    messages: List[ChatMessage] = []
    current_question: Optional[str] = None
    answer: Optional[str] = None
    context: Dict[str, Any] = {}


class QuestionAnswerState(BaseModel):
    """问答状态模型"""
    question: str
    answer: Optional[str] = None
    context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None
    segmented_image: Optional[bytes] = None  # 分割后的图像
    segmentation_info: Optional[List[Dict]] = None  # 分割信息
    segmented_image_path: Union[List,str] = None  # 分割图像存储路径