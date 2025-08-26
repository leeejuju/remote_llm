import io
import base64
import traceback
from PIL import Image
import asyncio
import traceback
from app.agents.supervisor_agent import CoordinatorAgent
from app.llm import MockLLM
from app.agents.qa_agent import *
from app.graphs.qa_graph import create_qa_graph


async def simple_qa_demo():
    """简单的问答演示"""
    print("=== LangGraph 问答系统演示 ===")
    
    # 初始化组件
    llm = MockLLM()
    qa_agent = CoordinatorAgent(llm)
    graph = create_qa_graph(qa_agent)

    def image_to_base64(image_path):
        try:
            with Image.open(image_path) as img:
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                return img_base64
        except Exception as e:
            raise RuntimeError(f"Failed to process image: {e}")
    
    # 交互式问答
    print("\n请输入您的问题（输入 'quit' 退出）:")
    
    while True:
        try:
            question = input("\n您: ").strip()
            
            if question.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            
            if not question:
                continue
            # 运行问答图
            result = await graph.ainvoke({
                "question": question,
                "answer": None,
                "context": {},
                "image_data":image_to_base64(image_path=r"D:\1_LLM_PROJECT\remote_llm\test\image\airport_301.png"),
                "image_format":"PNG"
            })
            
            print(f"助手: {result['answer']}")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:

            print(f"错误: {traceback.print_exc()}")


def main():
    """主函数"""
    print("基于LangGraph的问答系统")
    print("=" * 40)
    
    # 运行演示
    asyncio.run(simple_qa_demo())


if __name__ == "__main__":
    main()
