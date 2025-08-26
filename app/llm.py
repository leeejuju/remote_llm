import math
from langchain_ollama import ChatOllama
from typing import Dict, Any, Optional, Union, List
from abc import ABC, abstractmethod
from app.config import LLMSettings, config
from app.tools.custom_decorator_tool import retry_decorator
from langchain_core.vectorstores import InMemoryVectorStore

# class BaseLLM(ABC):
#     """LLM模型基类"""
    
#     @abstractmethod
#     async def generate(self, prompt, **kwargs) -> str:
#         """生成回答"""
#         pass
    
#     @abstractmethod
#     async def generate_with_context(self, messages: list, **kwargs) -> str:
#         """基于上下文生成回答"""
#         pass


class TokenCounter:
    """Token计数器"""
    # Token常量
    BASE_MESSAGE_TOKENS = 4
    FORMAT_TOKENS = 2
    LOW_DETAIL_IMAGE_TOKENS = 85
    HIGH_DETAIL_TILE_TOKENS = 170

    # 图像大小常量
    MAX_SIZE = 2048
    HIGH_DETAIL_TARGET_SHORT_SIDE = 768
    TILE_SIZE = 512

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def count_text(self, text: str) -> int:
        """计算输入文本的token数量"""
        return 0 if not text else len(self.tokenizer.encode(text))

    def count_image(self, image_item: dict) -> int:
        """
        根据维度信息等计算图像的token

        低细节: 固定85token
        高细节:
        1. 整体裁剪至2048
        2. 短边裁剪至于768
        3. 将缩放后的图像按 512×512 像素块切分，每块大概170token
        4. 在所有块 token 总数上，额外加 85 tokens
        """
        detail = image_item.get("detail", "medium")

        # 低画质
        if detail == "low":
            return self.LOW_DETAIL_IMAGE_TOKENS

        # 中高画质
        if detail == "high" or detail == "medium":
            # 如果提供了图像尺寸
            if "dimensions" in image_item:
                width, height = image_item["dimensions"]
                return self._calculate_high_detail_tokens(width, height)

        return (
            self._calculate_high_detail_tokens(1024, 1024) if detail == "high" else 1024
        )

    def _calculate_high_detail_tokens(self, width: int, height: int) -> int:
        """根据图像尺寸计算Token"""
        # 第一步：固定图像尺寸
        if width > self.MAX_SIZE or height > self.MAX_SIZE:
            scale = self.MAX_SIZE / max(width, height)
            width = int(width * scale)
            height = int(height * scale)

        # 第二步：图像scale刀768
        scale = self.HIGH_DETAIL_TARGET_SHORT_SIDE / min(width, height)
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)

        # 第三步: scale到512
        tiles_x = math.ceil(scaled_width / self.TILE_SIZE)
        tiles_y = math.ceil(scaled_height / self.TILE_SIZE)
        total_tiles = tiles_x * tiles_y

        # 第四步：计算tokens数量
        return (total_tiles * self.HIGH_DETAIL_TILE_TOKENS) + self.LOW_DETAIL_IMAGE_TOKENS

    def count_content(self, content: Union[str, List[Union[str, dict]]]) -> int:
        """计算Message的token数量"""
        if not content:
            return 0

        if isinstance(content, str):
            return self.count_text(content)

        token_count = 0
        for item in content:
            if isinstance(item, str):
                token_count += self.count_text(item)
            elif isinstance(item, dict):
                if "text" in item:
                    token_count += self.count_text(item["text"])
                elif "image_url" in item:
                    token_count += self.count_image(item)
        return token_count

    def count_tool_calls(self, tool_calls: List[dict]) -> int:
        """计算一次ToolCall消耗的Token"""
        token_count = 0
        for tool_call in tool_calls:
            if "function" in tool_call:
                function = tool_call["function"]
                token_count += self.count_text(function.get("name", ""))
                token_count += self.count_text(function.get("arguments", ""))
        return token_count

    def count_message_tokens(self, messages: List[dict]) -> int:
        """计算Messagelist消耗的Token数量"""
        total_tokens = self.FORMAT_TOKENS  # 固定Token数

        for message in messages:
            tokens = self.BASE_MESSAGE_TOKENS  # 消息token数

            # 计算Role token
            tokens += self.count_text(message.get("role", ""))

            # 计算content消耗的token
            if "content" in message:
                tokens += self.count_content(message["content"])

            # 计算tool call消耗的token
            if "tool_calls" in message:
                tokens += self.count_tool_calls(message["tool_calls"])

            # 计算name和tool_call_id的token
            tokens += self.count_text(message.get("name", ""))
            tokens += self.count_text(message.get("tool_call_id", ""))

            total_tokens += tokens
        
        # 返回总token数量
        return total_tokens

class LLM:
    """设置LLM属性以及方法"""

    _instances: Dict[str, "LLM"] = {}

    def __new__(cls, config_name: str = "default", llm_config: Optional[LLMSettings] = None):
        if config_name not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(config_name, llm_config)
            cls._instances[config_name] = instance
        return cls._instances[config_name]
    
    def __init__(
        self, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if not hasattr(self, "client"):  # 没有llm实例则初始化一个即可
            llm_config = llm_config or config.llm
            llm_config = llm_config.get(config_name, llm_config["default"])
            self.model = llm_config.model
            self.max_tokens = llm_config.max_tokens
            self.temperature = llm_config.temperature
            self.api_type = llm_config.api_type
            self.api_key = llm_config.api_key
            self.api_version = llm_config.api_version
            self.base_url = llm_config.base_url
            self.top_k = llm_config.top_k
            self.top_p = llm_config.top_p

            # 设置token计数器
            self.total_input_tokens = 0
            self.total_completion_tokens = 0
            self.max_input_tokens = (
                llm_config.max_input_tokens
                if hasattr(llm_config, "max_input_tokens")
                else None
            )

            # 初始化分词器，考虑使用Qwen的
            try:
                pass
                self.tokenizer = None
            except KeyError:
                pass
                # If the model is not in tiktoken's presets, use cl100k_base as default
                # self.tokenizer = tiktoken.get_encoding("cl100k_base")

            if self.api_type == "ollama":
                self.client = ChatOllama(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    temperature=self.temperature,
                    top_k=self.top_k,
                    top_p=self.top_p
                )
            # elif self.api_type == "aws":
            #     self.client = BedrockClient()
            # else:
            #     self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

            self.token_counter = TokenCounter(self.tokenizer)

    @retry_decorator(tries=3)
    async def generate(self,
        messages: List[Union[dict]],
        system_msgs: Optional[List[Union[dict]]] = None,
        stream: bool = True,
        temperature: Optional[float] = None,):
        pass


    


    
   