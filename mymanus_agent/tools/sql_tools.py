import os
import pymysql # type: ignore
import json
import pandas as pd # type: ignore
from dotenv import load_dotenv # type: ignore

def sql_inter(sql_query, g_namespace=None): 
    """
    用于执行一段SQL代码，并最终获取SQL代码执行结果。
    """
    print("正在调用sql_inter工具运行SQL代码...")
    load_dotenv(override=True) 
    host = os.getenv('HOST')
    user = os.getenv('USER')
    mysql_pw = os.getenv('MYSQL_PW')
    db = os.getenv('DB_NAME')
    port = os.getenv('PORT')
    
    if not all([host, user, mysql_pw, db, port]):
        return "数据库连接信息未在.env文件中完全配置。"

    try:
        connection = pymysql.connect(
            host=host,  
            user=user, 
            passwd=mysql_pw,  
            db=db,
            port=int(port), # type: ignore
            charset='utf8',
        )
    except pymysql.Error as e:
        return f"数据库连接失败: {e}"
    
    results_json = "[]" 
    try:
        with connection.cursor() as cursor: # type: ignore
            cursor.execute(sql_query)
            results = cursor.fetchall()
            print("SQL代码已顺利运行，正在整理答案...")
            results_json = json.dumps(results)
    except pymysql.Error as e:
        return f"SQL执行错误: {e}"
    finally:
        if 'connection' in locals() and connection.open: # type: ignore
            connection.close() # type: ignore
    return results_json

def extract_data(sql_query, df_name, g_namespace):
    """
    借助pymysql将MySQL中的某张表读取并保存到g_namespace。
    """
    print("正在调用extract_data工具运行SQL代码...")
    load_dotenv(override=True)
    
    host = os.getenv('HOST')
    user = os.getenv('USER')
    mysql_pw = os.getenv('MYSQL_PW')
    db = os.getenv('DB_NAME')
    port = os.getenv('PORT')

    if not all([host, user, mysql_pw, db, port]):
        return "数据库连接信息未在.env文件中完全配置。"

    try:
        connection = pymysql.connect(
            host=host,  
            user=user, 
            passwd=mysql_pw,  
            db=db,
            port=int(port), # type: ignore
            charset='utf8',
        )
    except pymysql.Error as e:
        return f"数据库连接失败: {e}"
        
    try:
        g_namespace[df_name] = pd.read_sql(sql_query, connection) # type: ignore
        print("代码已顺利执行，正在进行结果梳理...")
        return "已成功创建pandas对象：%s，该变量保存了同名表格信息" % df_name
    except Exception as e: 
        return f"从数据库提取数据时出错: {e}"
    finally:
        if 'connection' in locals() and connection.open: # type: ignore
            connection.close() # type: ignore
