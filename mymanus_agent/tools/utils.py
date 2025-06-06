import os
import json
import tiktoken # type: ignore
import base64
import webbrowser
import time
from lxml import etree # type: ignore
# from IPython.display import display, Markdown, Image # 已移除 IPython.display 的直接依赖

def windows_compatible_name(s, max_length=255):
    """
    将字符串转化为符合Windows文件/文件夹命名规范的名称。
    
    参数:
    - s (str): 输入的字符串。
    - max_length (int): 输出字符串的最大长度，默认为255。
    
    返回:
    - str: 一个可以安全用作Windows文件/文件夹名称的字符串。
    """
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in forbidden_chars:
        s = s.replace(char, '_')
    s = s.rstrip(' .')
    reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", 
                      "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    if s.upper() in reserved_names:
        s += '_'
    if len(s) > max_length:
        s = s[:max_length]
    return s

def print_code_if_exists(function_args):
    """
    如果存在代码片段，则打印代码 (Markdown格式)。
    """
    def convert_to_markdown(code, language):
        return f"```{language}\n{code}\n```"
    
    if function_args.get('sql_query'):
        code = function_args['sql_query']
        markdown_code = convert_to_markdown(code, 'sql')
        print("即将执行以下代码：")
        print(markdown_code) # 替换 display(Markdown(...))

    elif function_args.get('py_code'):
        code = function_args['py_code']
        markdown_code = convert_to_markdown(code, 'python')
        print("即将执行以下代码：")
        print(markdown_code) # 替换 display(Markdown(...))

def save_markdown_to_file(content: str, filename_hint: str, directory="research_task"):
    """
    将内容保存为Markdown文档。
    """
    save_dir = os.path.join(os.getcwd(), directory)
    os.makedirs(save_dir, exist_ok=True)
    
    compatible_filename_hint = windows_compatible_name(filename_hint)
    filename = f"{compatible_filename_hint[:20]}....md" 
    
    file_path = os.path.join(save_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"文件已成功保存到：{file_path}")
