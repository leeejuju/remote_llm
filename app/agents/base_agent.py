
from app.llm import LLM
from app.logger import logger
from typing import List, Optional
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, model_validator
from app.schema.schema import ROLE_TYPE, AgentState, Memory, Message


# from app.logger import logger
# from app.sandbox.client import SANDBOX_CLIENT
# from app.schema import ROLE_TYPE, AgentState, Memory, Message



class BaseAgent(BaseModel, ABC):
    """
    Agent的抽象基类, 用于设置Agent的属性以及执行
    
    """
    name: str = Field(..., description="Agent名称")
    description: Optional[str] = Field(None, description="Agent描述")
    
    # 依赖
    llm = Field(default_factory=LLM, description="大模型类型")
    memory: Memory = Field(default_factory=Memory, description="Agent的memo存储")
    
    # Prompt提示词
    system_prompt: Optional[str] = Field(None, description="系统级的指示Prompt")
    next_step_prompt: Optional[str] = Field(None, description="下一步动作的Prompt")
    state: AgentState = Field(default=AgentState.IDLE, description="Agent状态")

    # 执行控制
    max_steps: int = Field(default=10, description="最大反复执行次数")
    current_step: int = Field(default=0, description="当前次数")

    duplicate_threshold: int = 2

    class Config:
        arbitrary_types_allowed = True # 允许添加基础类型除外的类型
        extra = "allow"  # 允许添加其他字段 
    

    @model_validator(mode="after")
    def initialize_agent(self) -> "BaseAgent":
        """以默认参数初始化Agent状态"""
        if self.llm is None or not isinstance(self.llm, LLM):
            self.llm = LLM(config_name=self.name.lower())
        if not isinstance(self.memory, Memory):
            self.memory = Memory()
        return self

    async def state_context(self, new_state: AgentState):
        """Context manager for safe agent state transitions.

        Args:
            new_state: The state to transition to during the context.

        Yields:
            None: Allows execution within the new state.

        Raises:
            ValueError: If the new_state is invalid.
        """
        if not isinstance(new_state, AgentState):
            raise ValueError(f"Invalid state: {new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # Transition to ERROR on failure
            raise e
        finally:
            self.state = previous_state  # Revert to previous state

    def update_memory(
        self,
        role: ROLE_TYPE,  # type: ignore
        content: str,
        base64_image: Optional[str] = None,
        **kwargs,
    ) -> None:
        """向Agent的记忆库中添加消息

        Args:
            role: 消息发送方的类型The role of the message sender (user, system, assistant, tool).
            content: 消息内容.
            base64_image: 附带的的图像（可能没有）.
            **kwargs: 其他参数.
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, 
            **kw: Message.tool_message(content, **kw),
        }

        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")

        # 基于消息类型的角色定位创建参数
        kwargs = {"base64_image": base64_image, **(kwargs if role == "tool" else {})}
        self.memory.add_message(message_map[role](content, **kwargs))

    async def run(self, request: Optional[str] = None) -> str:
        """异步循环执行agent.


        Args:
            request: Optional initial user request to process.

        Returns:
            执行结果的Str字段.
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"当前状态不可执行: {self.state}")

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"当前执行第 {self.current_step}/{self.max_steps}")
                step_result = await self.step()

                # Check for stuck state
                if self.is_stuck():
                    self.handle_stuck_state()

                results.append(f"第 {self.current_step}: {step_result}步")

            if self.current_step >= self.max_steps:
                self.current_step = 0
                self.state = AgentState.IDLE
                results.append(f"当前执行第 ({self.max_steps})次，停止执行")
        # await SANDBOX_CLIENT.cleanup()
        return "\n".join(results) if results else "执行停止"

    @abstractmethod
    async def step(self) -> str:
        """Execute a single step in the agent's workflow.

        Must be implemented by subclasses to define specific behavior.
        """

    def handle_stuck_state(self):
        """Handle stuck state by adding a prompt to change strategy"""
        stuck_prompt = "\
        Observed duplicate responses. Consider new strategies and avoid repeating ineffective paths already attempted."
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"
        logger.warning(f"Agent detected stuck state. Added prompt: {stuck_prompt}")

    def is_stuck(self) -> bool:
        """Check if the agent is stuck in a loop by detecting duplicate content"""
        if len(self.memory.messages) < 2:
            return False

        last_message = self.memory.messages[-1]
        if not last_message.content:
            return False

        # Count identical content occurrences
        duplicate_count = sum(
            1
            for msg in reversed(self.memory.messages[:-1])
            if msg.role == "assistant" and msg.content == last_message.content
        )

        return duplicate_count >= self.duplicate_threshold

    @property
    def messages(self) -> List[Message]:
        """从内存获取历史Message."""
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        """为Agent的Memo进行set"""
        self.memory.messages = value
