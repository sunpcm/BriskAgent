"""
AutoGen 软件开发团队协作案例
"""

import os
import asyncio
import random
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console

print(os.getenv("LLM_MODEL_ID"),
      os.getenv("LLM_API_KEY"),
      os.getenv("LLM_BASE_URL"),)


def create_openai_model_client():
    """
    创建 OpenAI 模型客户端用于测试
    """
    print("=============================")
    # 从环境变量读取配置，确保类型为 str 并在缺失时给出明确提示
    model_id = os.getenv("LLM_MODEL_ID") or ""
    api_key = os.getenv("LLM_API_KEY") or ""
    base_url = os.getenv("LLM_BASE_URL") or ""

    if not (model_id and api_key and base_url):
        # 不直接抛出异常以便更友好地在控制台看到提示
        print("WARNING: One or more LLM environment variables are missing:")
        print(f"  LLM_MODEL_ID={bool(model_id)} LLM_API_KEY={bool(api_key)} LLM_BASE_URL={bool(base_url)}")
        print("Please set LLM_MODEL_ID, LLM_API_KEY and LLM_BASE_URL in your environment or .env file.")

    return OpenAIChatCompletionClient(
        model=model_id,
        api_key=api_key,
        base_url=base_url,
    )

def create_product_manager(model_client):
    """创建产品经理智能体"""
    system_message = """
你是一位经验丰富的产品经理，专门负责软件产品的需求分析和项目规划

你的核心职责:
1. **需求分析**：深入理解用户需求，识别核心功能和边界条件
2. **技术规划**：基于需求制定清晰的技术实现路径
3. **风险评估**：识别潜在的技术风险和用户体验问题
4. **协调沟通**：与工程师和其他团队成员进行有效沟通

当接到开发任务的时候，请按照以下结构进行分析:
1. 需求理解与分析
2. 功能模块划分
3. 技术选型建议
4. 实现优先级排序
5. 验收标准定义

请简洁明了地回应，并在分析完成后说"请工程师开始实现"。
    """

    return AssistantAgent(
        name="ProductManager",
        model_client=model_client,
        system_message=system_message
    )

def create_engineer(model_client):
    """创建软件工程师智能体"""
    system_message = """
你是一位资深的软件工程师，擅长 Python 开发和 Web 应用构建。

你的技术专长包括：
1. **Python 编程**：熟练掌握 Python 语法和最佳实践
2. **Web 开发**：精通 Streamlit、Flask、Django 等框架
3. **API 集成**：有丰富的第三方 API 集成经验
4. **错误处理**：注重代码的健壮性和异常处理

当收到开发任务时，请：
1. 仔细分析技术需求
2. 选择合适的技术方案
3. 编写完整的代码实现
4. 添加必要的注释和说明
5. 考虑边界情况和异常处理
6. 将代码写在当前目录下(/Users/sunpcm/code/BriskAgent/AgentFramework/AutoGen)并写相应的文档,如果是多个文件，请创建一个文件夹并将代码与文档置于其中

请提供完整的可运行代码，并在完成后说"请代码审查员检查"。
                      """
    return AssistantAgent(
        name="Engineer",
        model_client=model_client,
        system_message=system_message
                      )

def create_code_reviewer(model_client):
    """创建代码审查员智能体"""
    system_message = """
你是一位经验丰富的代码审查专家，专注于代码质量和最佳实践。

你的审查重点包括：
1. **代码质量**：检查代码的可读性、可维护性和性能
2. **安全性**：识别潜在的安全漏洞和风险点
3. **最佳实践**：确保代码遵循行业标准和最佳实践
4. **错误处理**：验证异常处理的完整性和合理性

审查流程：
1. 仔细阅读和理解代码逻辑
2. 检查代码规范和最佳实践
3. 识别潜在问题和改进点
4. 提供具体的修改建议
5. 评估代码的整体质量

请提供具体的审查意见，完成后说"代码审查完成，请用户代理测试"。    
    """
    return AssistantAgent(
        name="CodeReview",
        model_client=model_client,
    )

def create_user_proxy():
    """创建用户代理智能体"""
    return UserProxyAgent(
        name="UserProxy",
        description="""用户代理，负责以下职责：
1. 代表用户提出开发需求
2. 执行最终的代码实现
3. 验证功能是否符合预期
4. 提供用户反馈和建议

完成测试后请回复 TERMINATE。""",
    )

async def run_software_team():
    """运行软件开发团队"""

    print("正在初始化客户端...")

    model_client = create_openai_model_client()

    print("正在创建智能体团队...")

    product_manager = create_product_manager(model_client)
    engineer = create_engineer(model_client)
    code_reviewer = create_code_reviewer(model_client)
    user_proxy = create_user_proxy()

    #添加终止条件
    termination = TextMentionTermination("TERMINATE")

    # 创建团队聊天
    team_chat = RoundRobinGroupChat(
        participants=[
            product_manager,
            engineer,
            code_reviewer,
            user_proxy,
        ],
        termination_condition=termination,
        max_turns=24
    )

    #开发任务
    task = """
我们需要开发一个比特币价格显示应用，具体要求如下：

核心功能：
- 实时显示比特币当前价格（USD）
- 显示24小时价格变化趋势（涨跌幅和涨跌额）
- 提供价格刷新功能

技术要求：
- 使用 Streamlit 框架创建 Web 应用
- 界面简洁美观，用户友好
- 添加适当的错误处理和加载状态

请团队协作完成这个任务，从需求分析到最终实现。"""

    #执行（使用重试策略应对模型 503 / overloaded 错误）
    print("启动 AutoGen 软件开发团队协作")
    print("=" * 60)

    async def _run_once():
        # 单次运行协作会话并返回结果
        return await Console(team_chat.run_stream(task=task))

    async def _run_with_retries(coro_factory, max_retries: int = 5, base_delay: float = 1.0):
        """对特定的模型过载错误进行指数退避重试。

        只对明显的模型繁忙/503/UNAVAILABLE 错误做重试，其他错误会立即抛出。
        """
        for attempt in range(1, max_retries + 1):
            try:
                return await coro_factory()
            except Exception as e:
                msg = str(e).lower()
                # 针对 503 / overloaded / unavailable 做重试
                if ("503" in msg) or ("overloaded" in msg) or ("unavailable" in msg):
                    if attempt == max_retries:
                        print(f"重试次数用尽，最后错误：{e}")
                        raise
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    print(f"模型繁忙，重试 {attempt}/{max_retries}，等待 {delay:.1f}s...  错误: {e}")
                    await asyncio.sleep(delay)
                    continue
                # 非模型繁忙相关错误，直接抛出
                raise

    # 使用带重试的运行器执行团队协作
    result = await _run_with_retries(_run_once, max_retries=5, base_delay=1.0)

    print("\n" + "=" * 60)
    print("协作完成")

    return result

if __name__ == "__main__":
    try:
        result = asyncio.run(run_software_team())

        print(f"\n📋 协作结果摘要：")
        print(f"- 参与智能体数量：4个")
        print(f"- 任务完成状态：{'成功' if result else '需要进一步处理'}")

    except Exception as e:
        print(f"❌ 运行错误：{e}")
        import traceback
        traceback.print_exc()

