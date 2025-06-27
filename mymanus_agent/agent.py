import os
import json
from dotenv import load_dotenv # type: ignore
from openai import OpenAI # type: ignore 

from .tools.python_tools import python_inter, fig_inter
from .tools.sql_tools import sql_inter, extract_data
from .tools.search_tools import get_answer, get_answer_github
from .tools.utils import print_code_if_exists, save_markdown_to_file

load_dotenv(override=True)

class mymanusClass:
    def __init__(self, 
                 api_key=None, 
                 model=None,
                 base_url=None,
                 messages=None,
                 tools_config=None):
        
        self.api_key = api_key if api_key is not None else os.getenv("API_KEY")
        self.model_name = model if model is not None else os.getenv("MODEL")
        self.base_url = base_url if base_url is not None else os.getenv("BASE_URL")
        
        # 初始化会话历史
        if messages is not None:
            self.messages = list(messages) # 确保是列表的副本
        else:
            # 初始系统消息，只在第一次创建实例或clear_messages后设置
            self.messages = [{"role":"system", "content":"你是MyManus,是大师级的智能助手。"}]
            
        if not all([self.api_key, self.model_name, self.base_url]):
            print("错误：API_KEY, MODEL, 或 BASE_URL 未配置。请检查.env文件或初始化参数。")
            self.client = None
            return

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        self.available_functions = {
            "python_inter": python_inter,
            "fig_inter": fig_inter,
            "sql_inter": sql_inter,
            "extract_data": extract_data,
            "get_answer": get_answer,
            "get_answer_github": get_answer_github,
        }
        self.tools_definitions = tools_config if tools_config else self._get_default_tools_definitions()
        # 初始化 g_namespace 用于 python_inter, fig_inter, extract_data
        self.g_namespace = {} 

        try:
            print("正在测试模型能否正常调用...")
            models_list = self.client.models.list()
            if models_list and models_list.data:
                available_model_names = [m.id for m in models_list.data]
                if self.model_name not in available_model_names:
                    print(f"警告：配置的模型 '{self.model_name}' 不在可用模型列表中。可用模型: {available_model_names}")
                print("▌ mymanus初始化完成，欢迎使用！")
            else:
                print("未能获取到模型列表，请检查API Key和Base URL配置以及网络连接。")
        except Exception as e:
            print(f"初始化失败，可能是网络或配置错误。详细信息： {str(e)}")

    def _get_default_tools_definitions(self):
        python_inter_args_example = '{"py_code": "import numpy as np\\narr = np.array([1, 2, 3, 4])\\nsum_arr = np.sum(arr)\\nsum_arr"}'
        sql_inter_args_example = '{"sql_query": "SHOW TABLES;"}'
        extract_data_args_example = '{"sql_query": "SELECT * FROM user_churn", "df_name": "user_churn"}'
        get_answer_args_example = '{"q": "什么是MCP?"}'
        get_answer_github_args_example = '{"q": "DeepSeek-R1"}'
        return [
            {
                "type": "function",
                "function": {
                    "name": "python_inter",
                    "description": f"当用户需要编写Python程序并执行时，请调用该函数。该函数可以执行一段Python代码并返回最终结果，需要注意，本函数只能执行非绘图类的代码，若是绘图相关代码，则需要调用fig_inter函数运行。\n同时需要注意，编写外部函数的参数消息时，必须是满足json格式的字符串，例如如以下形式字符串就是合规字符串：{python_inter_args_example}",
                    "parameters": {
                        "type": "object",
                        "properties": {"py_code": {"type": "string", "description": "The Python code to execute."}},
                        "required": ["py_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fig_inter",
                    "description": "当用户需要使用 Python 进行可视化绘图任务时，请调用该函数。该函数会执行用户提供的 Python 绘图代码，并自动将生成的图像对象保存为图片文件并展示。\n\n调用该函数时，请传入以下参数：\n\n1. `py_code`: 一个字符串形式的 Python 绘图代码，**必须是完整、可独立运行的脚本**，代码必须创建并返回一个命名为 `fname` 的 matplotlib 图像对象；\n2. `fname`: 图像对象的变量名（字符串形式），例如 'fig'；\n\n📌 请确保绘图代码满足以下要求：\n- 包含所有必要的 import（如 `import matplotlib.pyplot as plt`, `import seaborn as sns` 等）；\n- 必须包含数据定义（如 `df = pd.DataFrame(...)`），不要依赖外部变量；\n- 推荐使用 `fig, ax = plt.subplots()` 显式创建图像；\n- 使用 `ax` 对象进行绘图操作（例如：`sns.lineplot(..., ax=ax)`）；\n- 最后明确将图像对象保存为 `fname` 变量（如 `fig = plt.gcf()`）。\n\n📌 不需要自己保存图像，函数会自动保存并展示。\n\n✅ 合规示例代码：\n```python\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport pandas as pd\n\ndf = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})\nfig, ax = plt.subplots()\nsns.lineplot(data=df, x='x', y='y', ax=ax)\nax.set_title('Line Plot')\nfig = plt.gcf()  # 一定要赋值给 fname 指定的变量名\n```",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "py_code": {"type": "string", "description": "需要执行的 Python 绘图代码（字符串形式）。代码必须创建一个 matplotlib 图像对象，并赋值为 `fname` 所指定的变量名。"},
                            "fname": {"type": "string", "description": "图像对象的变量名（例如 'fig'），代码中必须使用这个变量名保存绘图对象。"}
                        },
                        "required": ["py_code", "fname"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sql_inter",
                    "description": f"当用户需要进行数据库查询工作时，请调用该函数。该函数用于在指定MySQL服务器上运行一段SQL代码，完成数据查询相关工作，并且当前函数是使用pymsql连接MySQL数据库。本函数只负责运行SQL代码并进行数据查询，若要进行数据提取，则使用另一个extract_data函数。同时需要注意，编写外部函数的参数消息时，必须是满足json格式的字符串，例如如以下形式字符串就是合规字符串：{sql_inter_args_example}",
                    "parameters": {
                        "type": "object",
                        "properties": {"sql_query": {"type": "string", "description": "The SQL query to execute in MySQL database."}},
                        "required": ["sql_query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_data",
                    "description": f"用于在MySQL数据库中提取一张表到当前Python环境中，注意，本函数只负责数据表的提取，并不负责数据查询，若需要在MySQL中进行数据查询，请使用sql_inter函数。同时需要注意，编写外部函数的参数消息时，必须是满足json格式的字符串，例如如以下形式字符串就是合规字符串：{extract_data_args_example}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql_query": {"type": "string", "description": "The SQL query to extract a table from MySQL database."},
                            "df_name": {"type": "string", "description": "The name of the variable to store the extracted table in the local environment."}
                        },
                        "required": ["sql_query", "df_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_answer",
                    "description": f"联网搜索工具，当用户提出的问题超出你的知识库范畴时，或该问题你不知道答案的时候，请调用该函数来获得问题的答案。该函数会自动从知乎上搜索得到问题相关文本，而后你可围绕文本内容进行总结，并回答用户提问。需要注意的是，当用户点名要求想要了解GitHub上的项目时候，请调用get_answer_github函数。示例参数：{get_answer_args_example}",
                    "parameters": {
                        "type": "object",
                        "properties": {"q": {"type": "string", "description": "一个满足知乎搜索格式的问题，用字符串形式进行表示。" }},
                        "required": ["q"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_answer_github",
                    "description": f"GitHub联网搜索工具，当用户提出的问题超出你的知识库范畴时，或该问题你不知道答案的时候，请调用该函数来获得问题的答案。该函数会自动从GitHub上搜索得到问题相关文本，而后你可围绕文本内容进行总结，并回答用户提问。需要注意的是，当用户提问点名要求在GitHub进行搜索时，例如“请帮我介绍下GitHub上的Qwen2项目”，此时请调用该函数，其他情况下请调用get_answer外部函数并进行回答。示例参数：{get_answer_github_args_example}",
                    "parameters": {
                        "type": "object",
                        "properties": {"q": {"type": "string", "description": "一个满足GitHub搜索格式的问题，往往是需要从用户问题中提出一个适合搜索的项目关键词，用字符串形式进行表示。"}},
                        "required": ["q"]
                    }
                }
            }
        ]

    def _chat_base_agent(self, current_messages_for_api_call):
        # 这个方法现在直接修改传入的 current_messages_for_api_call 列表
        if not self.client:
            print("客户端未初始化。")
            return None # 或者返回一个表示错误的特定响应
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,  
                messages=current_messages_for_api_call, # 使用传入的消息列表
                tools=self.tools_definitions,
                tool_choice="auto"
            )
        except Exception as e:
            print(f"模型调用报错: {str(e)}")
            return None

        response_message = None
        if response and response.choices and len(response.choices) > 0:
            response_message = response.choices[0].message
        
        tool_calls = getattr(response_message, 'tool_calls', None)

        while tool_calls: 
            print("模型请求工具调用...")
            # 将模型的工具调用请求添加到传入的消息列表中
            current_messages_for_api_call.append(response_message.model_dump()) # type: ignore
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args_str = tool_call.function.arguments
                print(f"调用工具: {function_name}，参数: {function_args_str}")
                try:
                    function_args = json.loads(function_args_str)
                except json.JSONDecodeError as e:
                    print(f"解析工具参数失败: {e}")
                    function_response_content = f"错误：工具 '{function_name}' 的参数不是有效的JSON: {function_args_str}"
                    current_messages_for_api_call.append({ # 添加到传入的消息列表
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response_content,
                    })
                    continue

                print_code_if_exists(function_args=function_args)

                if function_name in self.available_functions:
                    function_to_call = self.available_functions[function_name]
                    if function_name in ["python_inter", "fig_inter", "extract_data"]:
                        function_args['g_namespace'] = self.g_namespace # 使用实例的 g_namespace
                    try:
                        function_response_content = function_to_call(**function_args)
                    except Exception as e_func:
                        print(f"工具 '{function_name}' 执行失败: {e_func}")
                        function_response_content = f"错误: 工具 '{function_name}' 执行时发生错误: {str(e_func)}"
                else:
                    print(f"未找到工具: {function_name}")
                    function_response_content = f"错误: 未知的工具 '{function_name}'"

                current_messages_for_api_call.append({ # 添加到传入的消息列表
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response_content),
                })
            
            print("所有工具调用处理完毕，再次请求模型...")
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=current_messages_for_api_call, # 使用更新后的消息列表
                    tools=self.tools_definitions,
                    tool_choice="auto"
                )
                if response and response.choices and len(response.choices) > 0:
                    response_message = response.choices[0].message
                    tool_calls = getattr(response_message, 'tool_calls', None)
                    if response.choices[0].finish_reason != "tool_calls": 
                        tool_calls = None 
                else: 
                    tool_calls = None
            except Exception as e:
                print(f"模型再次调用报错: {str(e)}")
                return None
        return response

    def chat(self):
        if not self.client:
            print("无法启动聊天：客户端未初始化。")
            return

        print("你好，我是mymanus，有什么需要帮助的？")
        # chat方法现在直接使用和修改 self.messages
        
        # 确保 self.messages 的第一个消息是 system message (如果它是空的或不符合预期)
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages = [{"role":"system", "content":"你mymanus，是一名助人为乐的助手。"}]
            self.g_namespace = {} # 如果重置消息，也重置g_namespace

        while True:
            try:
                question = input("请输入您的问题(输入 退出 以结束对话): ")
            except EOFError:
                print("输入结束，对话终止。")
                break
            if question.lower() == "退出":
                print("感谢使用mymanus，再见！")
                break  
                
            self.messages.append({"role": "user", "content": question})
            # 限制历史消息长度（可选），操作 self.messages
            if len(self.messages) > 20: # 例如保留最近20条（包括系统消息）
                 # 保留系统消息和最新的19条用户/助手消息
                self.messages = [self.messages[0]] + self.messages[-19:]
            
            # _chat_base_agent 会直接修改 self.messages 列表
            response = self._chat_base_agent(current_messages_for_api_call=self.messages) 
            
            if response and response.choices and response.choices[0].message and response.choices[0].message.content:
                final_content = response.choices[0].message.content
                print(f"\n**mymanus**:\n{final_content}\n") 
                # 将模型的最终回复添加到 self.messages
                self.messages.append(response.choices[0].message.model_dump())
            elif response and response.choices and response.choices[0].finish_reason == "tool_calls":
                print("模型在工具调用后未返回最终文本内容。请尝试继续对话或检查工具输出。")
            else:
                print("抱歉，我无法处理您的请求或模型未返回有效内容。")
                # 如果用户最后一条消息未得到回复，可以选择移除它
                if self.messages and self.messages[-1].get("role") == "user":
                    self.messages.pop()

    def research_task(self, question):
        if not self.client:
            print("无法执行研究任务：客户端未初始化。")
            return

        # research_task 使用 self.messages 作为基础，但添加特定的系统提示
        # current_research_messages = list(self.messages) # 开始于当前会话历史
        
        # 为了让 research_task 有一个更专注的上下文，可以考虑为其创建一个临时的消息列表
        # 或者，如果希望它继承当前聊天历史：
        if not self.messages or self.messages[0].get("role") != "system": # 确保有系统消息开头
             current_research_messages = [{"role":"system", "content":"你是一名专业的研究助手，善于引导用户明确需求并进行深度调研。"}]
        else:
            current_research_messages = [self.messages[0]] # 从主系统消息开始
            current_research_messages.append({"role":"system", "content":"现在切换到研究任务模式。你是一名专业的研究助手，善于引导用户明确需求并进行深度调研。"})


        prompt_style1_template = """
        你是一名专业且细致的助手，你的任务是在用户提出问题后，通过友好且有引导性的追问，更深入地理解用户真正的需求背景。这样，你才能提供更精准和更有效的帮助。
        当用户提出一个宽泛或者不够明确的问题时，你应当积极主动地提出后续问题，引导用户提供更多背景和细节，以帮助你更准确地回应。
        现在用户提出问题如下：{question}，请按照要求进行回复。
        """
        
        prompt_style2_template = """
        你是一位知识广博、擅长利用多种外部工具的资深研究员。当用户已明确提出具体需求：{new_question}，现在你的任务是：
        首先明确用户问题的核心及相关细节。
        尽可能调用可用的外部工具（例如：联网搜索工具get_answer、GitHub搜索工具get_answer_github、本地代码运行工具python_inter以及其他工具），围绕用户给出的原始问题和补充细节，进行广泛而深入的信息收集。
        综合利用你从各种工具中获取的信息，提供详细、全面、专业且具有深度的解答。你的回答应尽量达到2000字以上，内容严谨准确且富有洞察力。
        清晰展示你是如何运用各种外部工具进行深入研究并形成专业结论的。
        """
        
        initial_prompt = prompt_style1_template.format(question=question)
        current_research_messages.append({"role": "user", "content": initial_prompt})
        
        try:
            # 对于引导性提问，通常不需要工具调用，所以可以直接调用 completions.create
            response1 = self.client.chat.completions.create(
                model=self.model_name,
                messages=current_research_messages
            )
        except Exception as e:
            print(f"研究任务第一步模型调用失败: {e}")
            return None
        
        if not (response1 and response1.choices and response1.choices[0].message and response1.choices[0].message.content):
            print("研究任务第一步未能从模型获取有效响应。")
            return None

        assistant_reply1 = response1.choices[0].message.content
        print(f"\n**mymanus (引导提问):**\n{assistant_reply1}\n")
        current_research_messages.append(response1.choices[0].message.model_dump())
        
        try:
            new_question_input = input("请输入您的补充说明 (或直接回车使用原始问题，输入 退出 以结束): ")
        except EOFError:
            print("输入结束，研究任务终止。")
            return None

        if new_question_input.lower() == "退出":
            print("研究任务已由用户终止。")
            return None
        
        if not new_question_input.strip():
            print("未提供补充说明，将基于原始问题和引导进行深度研究。")
            new_question_for_prompt2 = f"原始问题是：'{question}'。根据你的引导性提问 '{assistant_reply1}'，我希望你深入研究。请继续。"
        else:
            new_question_for_prompt2 = new_question_input

        deep_dive_prompt = prompt_style2_template.format(new_question=new_question_for_prompt2)
        current_research_messages.append({"role": "user", "content": deep_dive_prompt})
            
        # 深度研究步骤可能需要工具调用
        response2 = self._chat_base_agent(current_messages_for_api_call=current_research_messages) 
            
        if response2 and response2.choices and response2.choices[0].message and response2.choices[0].message.content:
            final_report_content = response2.choices[0].message.content
            print(f"\n**mymanus (深度报告):**\n{final_report_content}\n")
            save_markdown_to_file(content=final_report_content, 
                                  filename_hint=question,
                                  directory="research_task")
            # 将研究任务的最后回复也加入到主消息历史中
            self.messages.extend(current_research_messages[1:]) # 添加除了初始系统消息外的所有研究消息
            self.messages.append(response2.choices[0].message.model_dump())
        else:
            print("研究任务未能生成最终报告。")
        
        # 限制 self.messages 长度
        if len(self.messages) > 20:
            self.messages = [self.messages[0]] + self.messages[-19:]


    def clear_messages(self):
        """
        清除当前会话历史和Python工具的命名空间。
        """
        self.messages = [{"role":"system", "content":"你mymanus，是一名助人为乐的助手。"}]
        self.g_namespace = {} # 清空python工具的命名空间
        print("会话历史和Python命名空间已清除。")
