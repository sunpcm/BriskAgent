import os

from serpapi import SerpApiClient
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

def search(query: str) -> str:
    """
    基于 serpapi的网页搜索引擎工具，可以解析搜索结果，优先返回直接答案或者图谱信息
    """

    print(f"正在执行网页搜索 {query}")

    try:
        api_key = os.getenv("SERP_API_KEY")
        if not api_key:
            return "错误：需要在 .env文件中配置 SERP_API_KEY"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn", # 语言代码
        }

        client = SerpApiClient(params)
        result = client.get_dict()

        #解析result，寻找最直接答案
        if "answer_box_list" in result:
            return "\n".join(result["answer_box_list"])
        if "answer_box" in result and "answer" in result["answer_box"]:
            return result["answer_box"]["answer"]
        if "knowledge_graph" in result and "description" in result["knowledge_graph"]:
            return result["knowledge_graph"]["description"]
        if "organic_results" in result and result["organic_results"]:
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(result["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        return f"没有检索到 ‘{query}’ 的信息"
    except Exception as e:
        return f"搜索时发生错误 {e}"


class ToolExecutor:
    """
    工具执行器，负责管理和执行工具
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, str]] = {}

    def register_tool(self, name: str, description: str, func: callable) -> None:
        """
        向工具相中注册一个新工具
        """
        if name in self.tools:
            print(f"工具{name}已经存在，将会被覆盖掉")
        self.tools[name] = {
            "description": description,
            "func": func
        }
        print(f"工具{name}注册成功")
    def get_tool(self, name: str) -> callable:
        """
        根据工具名称获取工具
        """
        return self.tools.get(name, {}).get("func")

    def get_all_tools_name(self) -> Dict[str, str]:
        return "\n".join([
            f"{name}: {info['description']}"
            for name, info in self.tools.items()
        ])


if __name__ == "__main__":
    # 初始化工具
    toolExecutor = ToolExecutor()

    # 注册搜索工具
    search_desc = "一个网络搜索引擎，可以检索不在知识库或者实时的问题"
    toolExecutor.register_tool("search", search_desc, search)

    # 打印所有可用工具
    print("\n ------打印可用的 tools name")
    print(toolExecutor.get_all_tools_name())

    # 测试实时问题
    print("\n----执行 Action： search['Apple最新款电脑芯片的型号']----")
    tool_name = "search"
    tool_input = "Apple最新款电脑芯片的型号"

    tool_func = toolExecutor.get_tool(tool_name)
    if tool_func:
        resp = tool_func(tool_input)
        print("\n -----TOOL 返回--------")
        print(resp)
    else:
        print(f"没找到工具 {tool_name}")




