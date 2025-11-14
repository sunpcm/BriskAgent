import re

from AgentTest.tools import ToolExecutor, search
from llm_client.llm_client import BriskAgentsLLM

# 提示词模板
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手

可用工具如下:
{tools}

请严格按照一下格式进行回应:

Thought:你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action:你决定采取的行动，必须是以下的格式之一:
- `{{tool_name}}[{{tool_input}}]`: 调用一个可用工具。
- `Finish[最终答案]`:当你任务已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在 Action:字段后使用finish(answer="...")来输出答案

现在，请开始以下问题:
Question:{question}
History: {history}
"""

class ReActAgent:
    def __init__(self, llm_client: BriskAgentsLLM, tool_executor: ToolExecutor, max_steps: int=5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def _parse_output(self, text: str):
        """解析 LLM 的输出， 提取 Thought 和 Action"""
        thought_match = re.search(r"Thought:(.*)", text)
        action_match = re.search(r"Action:(.*)", text)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """解析 Action字符串，提取工具名称和输入"""
        match = re.match(r"(\w+)\[(.*)\]", action_text)
        if match:
            return match.group(1), match.group(2)
        return None,None

    def _parse_action_input(self, action_text: str):

        match = re.match(r"\w+\[(.*)\]", action_text)
        print(match.group(0), match.group(1))

        return match.group(1) if match else ""

    def run(self, questionStr: str):
        """
        运行 ReAct Agent来回答问题
        """

        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"-----第{current_step}步------")

            # 格式化提示词
            tool_desc = self.tool_executor.get_all_tools_name()
            history_str = '\n'.join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tool_desc,
                question=questionStr,
                history=history_str
            )

            #调用 LLM 进行思考
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages)

            if not response_text:
                print("错误:LLM 没有返回")


            print(response_text)

            thought, action = self._parse_output(response_text)

            if thought:
                print(f"思考: {thought}")
            if not action:
                print("警告:未能找到工具，退出")
                break

            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                # 没能找到对应工具
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")

            tool_function = self.tool_executor.get_tool(tool_name)
            if not tool_function:
                observation = f"错误:未找到名为 '{tool_name}' 的工具。"
            else:
                observation = tool_function(tool_input) # 调用真实工具

            print(f"观察: {observation}")

            # 将本轮的Action和Observation添加到历史记录中
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        # 循环结束
        print("已达到最大步数，流程终止。")
        return None

if __name__ == '__main__':
    llm = BriskAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.register_tool("search", search_desc, search)
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "Apple最新款电脑芯片的型号是什么"
    agent.run(question)



"""
（1）ReAct 的主要特点
高可解释性：ReAct 最大的优点之一就是透明。通过 Thought 链，我们可以清晰地看到智能体每一步的“心路历程”——它为什么会选择这个工具，下一步又打算做什么。这对于理解、信任和调试智能体的行为至关重要。
动态规划与纠错能力：与一次性生成完整计划的范式不同，ReAct 是“走一步，看一步”。它根据每一步从外部世界获得的 Observation 来动态调整后续的 Thought 和 Action。如果上一步的搜索结果不理想，它可以在下一步中修正搜索词，重新尝试。
工具协同能力：ReAct 范式天然地将大语言模型的推理能力与外部工具的执行能力结合起来。LLM 负责运筹帷幄（规划和推理），工具负责解决具体问题（搜索、计算），二者协同工作，突破了单一 LLM 在知识时效性、计算准确性等方面的固有局限。
（2）ReAct 的固有局限性
对LLM自身能力的强依赖：ReAct 流程的成功与否，高度依赖于底层 LLM 的综合能力。如果 LLM 的逻辑推理能力、指令遵循能力或格式化输出能力不足，就很容易在 Thought 环节产生错误的规划，或者在 Action 环节生成不符合格式的指令，导致整个流程中断。
执行效率问题：由于其循序渐进的特性，完成一个任务通常需要多次调用 LLM。每一次调用都伴随着网络延迟和计算成本。对于需要很多步骤的复杂任务，这种串行的“思考-行动”循环可能会导致较高的总耗时和费用。
提示词的脆弱性：整个机制的稳定运行建立在一个精心设计的提示词模板之上。模板中的任何微小变动，甚至是用词的差异，都可能影响 LLM 的行为。此外，并非所有模型都能持续稳定地遵循预设的格式，这增加了在实际应用中的不确定性。
可能陷入局部最优：步进式的决策模式意味着智能体缺乏一个全局的、长远的规划。它可能会因为眼前的 Observation 而选择一个看似正确但长远来看并非最优的路径，甚至在某些情况下陷入“原地打转”的循环中。
（3）调试技巧
检查完整的提示词：在每次调用 LLM 之前，将最终格式化好的、包含所有历史记录的完整提示词打印出来。这是追溯 LLM 决策源头的最直接方式。
分析原始输出：当输出解析失败时（例如，正则表达式没有匹配到 Action），务必将 LLM 返回的原始、未经处理的文本打印出来。这能帮助你判断是 LLM 没有遵循格式，还是你的解析逻辑有误。
验证工具的输入与输出：检查智能体生成的 tool_input 是否是工具函数所期望的格式，同时也要确保工具返回的 observation 格式是智能体可以理解和处理的。
调整提示词中的示例 (Few-shot Prompting)：如果模型频繁出错，可以在提示词中加入一两个完整的“Thought-Action-Observation”成功案例，通过示例来引导模型更好地遵循你的指令。
尝试不同的模型或参数：更换一个能力更强的模型，或者调整 temperature 参数（通常设为0以保证输出的确定性），有时能直接解决问题。
"""




"""
工具search注册成功
-----第1步------
大模型正在思考...
Resp获取成功
Action:search[Apple最新款电脑芯片型号]
Action:search[Apple最新款电脑芯片型号]
🎬 行动: search[Apple最新款电脑芯片型号]
正在执行网页搜索 Apple最新款电脑芯片型号
观察: [1] Apple 发布搭载M5 芯片的全新14 英寸MacBook Pro
搭载M5 芯片的14 英寸MacBook Pro 速度更快更强大，AI 性能亦实现巨大飞跃。M5 芯片采用新一代图形处理器，每颗核心内皆配备神经网络加速器，与前代机型相比 ...

[2] 识别MacBook Pro 机型- 官方Apple 支持(中国)
这款机型搭载M4 Pro 或M4 Max 芯片，并配备三个雷雳5 端口。 颜色：银色、深空黑色. 机型标识符：Mac16,6、Mac16,8. 最新的兼容操作系统：macOS Tahoe 26.

[3] MacBook Pro
MacBook Pro 系列笔记本电脑现搭载M5、M4 Pro 或M4 Max 芯片，为AI 和Apple 智能预备好。最长达24 小时电池续航。Liquid 视网膜XDR 显示屏。
-----第2步------
大模型正在思考...
Resp获取成功
Action: Finish[Apple最新款电脑芯片的型号是M5。同时，M4 Pro和M4 Max也是Apple近期推出的高性能芯片。]
Action: Finish[Apple最新款电脑芯片的型号是M5。同时，M4 Pro和M4 Max也是Apple近期推出的高性能芯片。]
Finish[Apple最新款电脑芯片的型号是M5。同时，M4 Pro和M4 Max也是Apple近期推出的高性能芯片。] Apple最新款电脑芯片的型号是M5。同时，M4 Pro和M4 Max也是Apple近期推出的高性能芯片。
🎉 最终答案: Apple最新款电脑芯片的型号是M5。同时，M4 Pro和M4 Max也是Apple近期推出的高性能芯片。
"""