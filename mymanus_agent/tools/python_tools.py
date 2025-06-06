import matplotlib # type: ignore
import os
import matplotlib.pyplot as plt # type: ignore
import seaborn as sns # type: ignore
import pandas as pd # type: ignore
# from IPython.display import display, Image # 已移除 IPython.display 的直接依赖

def python_inter(py_code, g_namespace=None):
    """
    专门用于执行python代码，并获取最终查询或处理结果。
    :param py_code: 字符串形式的Python代码，
    :param g_namespace: 字典形式变量，表示环境变量，如果为None，则使用新的空字典
    :return：代码运行的最终结果
    """    
    print("正在调用python_inter工具运行Python代码...")
    if g_namespace is None:
        g_namespace = {} 

    try:
        return str(eval(py_code, g_namespace)) 
    except Exception: # 更通用的捕获初始eval的失败
        vars_before_exec = set(g_namespace.keys())
        try:            
            exec(py_code, g_namespace)
        except Exception as e_exec:
            return f"代码执行时报错 {e_exec}"
        
        vars_after_exec = set(g_namespace.keys())
        new_vars = vars_after_exec - vars_before_exec
        
        if new_vars:
            result = {var: g_namespace[var] for var in new_vars}
            print("代码已顺利执行，正在进行结果梳理...")
            try:
                return str(result)
            except Exception as e_str:
                return f"结果转换字符串失败: {e_str}. New vars: {list(new_vars)}"
        else:
            print("代码已顺利执行（无新变量或返回），正在进行结果梳理...")
            try:
                # 尝试获取py_code中最后一个非空行的表达式值
                stripped_code_lines = [line for line in py_code.strip().split('\n') if line.strip()]
                if stripped_code_lines:
                    last_expr = stripped_code_lines[-1]
                    last_expr_val = eval(last_expr, g_namespace)
                    return str(last_expr_val)
            except Exception:
                pass # 如果最后一行不是表达式或eval失败，则忽略
            return "已经顺利执行代码"


def fig_inter(py_code, fname, g_namespace=None):
    """
    执行Python绘图代码，保存图像。
    :param py_code: 字符串形式的Python绘图代码。
    :param fname: 图像对象的变量名（字符串形式）。
    :param g_namespace: 字典形式变量，表示环境变量，如果为None，则使用新的空字典。
    :return: 图像保存路径或错误信息。
    """
    print("正在调用fig_inter工具运行Python代码...")
    if g_namespace is None:
        g_namespace = {}

    g_namespace.setdefault('plt', plt)
    g_namespace.setdefault('sns', sns)
    g_namespace.setdefault('pd', pd)
    
    current_backend = matplotlib.get_backend()
    matplotlib.use('Agg') 

    pics_dir = 'pics'
    if not os.path.exists(pics_dir):
        os.makedirs(pics_dir)

    try:
        exec(py_code, g_namespace)

        fig = g_namespace.get(fname, None) 
        if fig and hasattr(fig, 'savefig'): 
            rel_path = os.path.join(pics_dir, f"{fname}.png")
            fig.savefig(rel_path, bbox_inches='tight')
            # display(Image(filename=rel_path)) # 在纯Python脚本中，图片已保存，此处不直接显示
            print(f"图片已保存到: {os.path.abspath(rel_path)}")
            print("代码已顺利执行，正在进行结果梳理...")
            return f"✅ 图片已保存，相对路径: {rel_path}"
        elif fig:
             return f"⚠️ 代码执行成功，但变量 '{fname}' 不是一个有效的matplotlib图像对象。"
        else:
            return f"⚠️ 代码执行成功，但未找到名为 '{fname}' 的图像对象，请确保在py_code中创建了该图像对象。"
    except Exception as e:
        return f"❌ 执行失败：{e}"
    finally:
        matplotlib.use(current_backend)
        plt.close('all') 
