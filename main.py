import os
from dotenv import load_dotenv # type: ignore
from mymanus_agent.agent import mymanusClass

def main():
    load_dotenv() 

    api_key = os.getenv("API_KEY")
    model_name = os.getenv("MODEL")
    base_url = os.getenv("BASE_URL")

    if not all([api_key, model_name, base_url]):
        print("错误：API_KEY, MODEL, 或 BASE_URL 未在 .env 文件中设置。")
        print("请确保 .env 文件存在于项目根目录，并包含所有必要的变量。")
        return

    print("mymanusClass 初始化中...")
    # 创建一个 agent 实例，在整个程序运行期间使用
    agent = mymanusClass(api_key=api_key, model=model_name, base_url=base_url)
    
    if agent.client is None:
        print("Agent 初始化失败，无法继续。")
        return
    
    print("\n欢迎来到 mymanus 控制台！")
    print("你可以选择以下操作：")
    print("1. 开始/继续交互式聊天")
    print("2. 执行深度研究任务")
    print("3. 清除当前会话记录")
    print("4. 退出")

    while True:
        choice = input("\n请输入您的选择 (1, 2, 3, 或 4): ").strip()

        if choice == '1':
            print("\n--- 开始/继续交互式聊天 ---")
            agent.chat() # 调用同一个 agent 实例的 chat 方法
            print("--- 交互式聊天结束 ---\n")
        elif choice == '2':
            research_question = input("请输入您要研究的问题: ").strip()
            if research_question:
                print(f"\n--- 开始研究任务：{research_question} ---")
                agent.research_task(question=research_question) # 调用同一个 agent 实例的 research_task 方法
                print("--- 研究任务结束 ---\n")
            else:
                print("研究问题不能为空。")
        elif choice == '3':
            agent.clear_messages() # 清除同一个 agent 实例的记录
        elif choice == '4':
            print("感谢使用，再见！")
            break
        else:
            print("无效的选择，请输入 1, 2, 3, 或 4。")

if __name__ == "__main__":
    main()
