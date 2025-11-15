from pyexpat.errors import messages
from typing import List, Dict, Any, Optional

from llm_client.llm_client import BriskAgentsLLM


class Memory:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        向记忆中添加新的记录
        record_type: 记录的类型，execution、reflection
        content：记录的内容
        """
        record = {"type": record_type, "content": content}
        self.records.append(record)
        print(f"记忆更新，新增一条 {record_type}记录")

    def get_trajectory(self) -> str:
        """
        将所有记忆格式化为一个连串字符，用于构建提示词
        """
        trajectory_parts = []
        for record in self.records:
            if record["type"] == "execution":
                trajectory_parts.append(f"---上一轮创始(代码)---\n{record['content']}")
            elif record["type"] == "reflection":
                trajectory_parts.append(f"---评审员返库---\n{record['content']}")
        return "\n\n".join(trajectory_parts)

    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次的执行结果，例如，最新的代码，如果不存在，则返回 None
        """
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return None

INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在<strong>算法效率</strong>上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答“无需改进”。

请直接输出你的反馈，不要包含任何额外的解释。
"""

REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
```python
{last_code_attempt}
```
评审员的反馈：
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""


class ReflectionAgent:
    def __init__(self, llm_client, max_iterations = 3):
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.memory = Memory()

    def _get_llm_resp(self, prompt: str) -> str:
        """辅助方法，用于调用 LLM 并获取完整的流行响应"""
        messages_str = [{"role": "user", "content": prompt}]
        resp_text = self.llm_client.think(messages_str)
        return resp_text

    def run(self, task: str):
        print(f"\n---开始处理 ---\n任务: {task}")

        # 初始执行
        print(f"\n---正在进行初始尝试----")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_resp(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # 迭代：反思与优化
        for i in range(self.max_iterations):
            print(f"\n---第{i+1}/{self.max_iterations}轮迭代---")

            # 反思
            print("\n -> 正在进行反思...")
            last_code = self.memory.get_last_execution()
            reflection_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_resp(reflection_prompt)
            self.memory.add_record("reflection", feedback)

            # 检查是否要停止
            if '无需改进' in feedback:
                print("\n 反思认为代码已经无需改进，任务完成")
                break

            # 优化
            print("-> 正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refine_code = self._get_llm_resp(refine_prompt)
            self.memory.add_record("execution", refine_code)

        final_code = self.memory.get_last_execution()
        print(f"\n---任务完成---\n最终生成的代码： \n {final_code}\n")
        return final_code

if __name__ == "__main__":
    # 初始化 LLM 客户端
    try:
        llm_agent = BriskAgentsLLM()
    except Exception as e:
        print(f"初始化报错：{e}")

    # 初始化 Reflection Agent
    agent = ReflectionAgent(llm_agent, max_iterations = 3)

    # 定义任务并运行
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    agent.run(task)

    finial_code = agent.run(task)

    print("\n====================")
    print(finial_code)