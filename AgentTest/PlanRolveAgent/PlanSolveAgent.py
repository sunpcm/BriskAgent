import ast

from llm_client.llm_client import BriskAgentsLLM

PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""

class Planner:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        """
        根据用户问题，生成计划
        """
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)

        # 消息列表
        messages = [{"role": "user", "content": prompt}]

        print("-----正在生产计划-----")
        # 获取计划
        resp_text = self.llm_client.think(messages)

        print(f"计划已生成: {resp_text}")

        # 解析 LLM 输出的列表字符
        try:
            # 找到```python 和```之间的内容
            plan_str = resp_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {resp_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

class Executor:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        """
        根据计划，逐步执行并解决问题
        """
        history= ""

        print("\n-----正在执行-----")

        for i, step in enumerate(plan):
            print(f"\n -> 正在执行步骤 {i+1} / {len(plan)}")

            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history,
                current_step=step,
            )

            message = [{"role": "user", "content": prompt}]

            resp_text = self.llm_client.think(message) or ""

            history += f"步骤 {i+1} / {len(plan)}: {step}\n 结果: {resp_text} \n\n"

            print(f"步骤{i+1} / {len(plan)}已完成，结果：{resp_text}")

        # 循环结束后，最后一步的响应就是最终结果
        final_answer = resp_text
        return final_answer

class PlanSolverAngent:
    def __init__(self, llm_client):
        """
        初始化智能体，创建规划器和执行器
        """
        self.llm_client = llm_client
        self.executor = Executor(self.llm_client)
        self.planner = Planner(self.llm_client)

    def run(self, questionStr: str):
        """
        运行流程：先规划，后执行
        """

        print(f"\n----开始处理问题-----\n 问题：{question}")

        # 生成计划
        plan = self.planner.plan(question)

        # 检查计划
        if not plan:
            print("-----计划生成失败，任务终止-----")
            return

        # 调用执行器执行计划
        final_answer = self.executor.execute(questionStr, plan)

        print(f"\n ---- 任务完成 ---- \n 最终答案：{final_answer}")

if __name__ == "__main__":
    try:
        llm_client = BriskAgentsLLM()
        agent = PlanSolverAngent(llm_client)
        question="小明的妈妈有四个孩子，大的叫大毛，第二大的叫二毛，第三大的叫三毛，最后一个孩子叫什么？"
        agent.run(question)
    except Exception as e:
        print(e)



"""
----开始处理问题-----
 问题：小明的妈妈有四个孩子，大的叫大毛，第二大的叫二毛，第三大的叫三毛，最后一个孩子叫什么？
-----正在生产计划-----
大模型正在思考...
Resp获取成功
```python
["识别问题中提到的孩子总数。", "列出问题中已经明确给出的孩子的名字。", "计算还剩下多少个孩子没有被命名。", "检查问题描述中是否还提到了其他可能属于孩子的人名。", "根据剩余孩子数量和发现的人名，确定最后一个孩子的名字。"]
```
计划已生成: ```python
["识别问题中提到的孩子总数。", "列出问题中已经明确给出的孩子的名字。", "计算还剩下多少个孩子没有被命名。", "检查问题描述中是否还提到了其他可能属于孩子的人名。", "根据剩余孩子数量和发现的人名，确定最后一个孩子的名字。"]
```

-----正在执行-----

 -> 正在执行步骤 1 / 5
大模型正在思考...
Resp获取成功
四个
步骤1 / 5已完成，结果：四个

 -> 正在执行步骤 2 / 5
大模型正在思考...
Resp获取成功
大毛、二毛、三毛
步骤2 / 5已完成，结果：大毛、二毛、三毛

 -> 正在执行步骤 3 / 5
大模型正在思考...
Resp获取成功
1
步骤3 / 5已完成，结果：1

 -> 正在执行步骤 4 / 5
大模型正在思考...
Resp获取成功
小明
步骤4 / 5已完成，结果：小明

 -> 正在执行步骤 5 / 5
大模型正在思考...
Resp获取成功
小明
步骤5 / 5已完成，结果：小明

 ---- 任务完成 ---- 
 最终答案：小明
"""
