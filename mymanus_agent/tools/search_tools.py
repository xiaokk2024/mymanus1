import os
import requests # type: ignore
import json
import base64
import tiktoken # type: ignore
import time
import webbrowser
from lxml import etree # type: ignore
from dotenv import load_dotenv # type: ignore
from .utils import windows_compatible_name 

load_dotenv(override=True)

HTTP_PROXY = os.getenv('HTTP_PROXY')
HTTPS_PROXY = os.getenv('HTTPS_PROXY')
PROXIES = None
if HTTP_PROXY or HTTPS_PROXY:
    PROXIES = {}
    if HTTP_PROXY:
        PROXIES['http'] = HTTP_PROXY
    if HTTPS_PROXY:
        PROXIES['https'] = HTTPS_PROXY

def google_search(query, num_results=10, site_url=None):
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("CSE_ID")

    if not api_key or not cse_id:
        return "Google搜索API Key或CSE ID未配置。"
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,          
        'key': api_key,      
        'cx': cse_id,        
        'num': num_results   
    }
    if site_url:
        params['siteSearch'] = site_url
    
    try:
        response = requests.get(url, params=params, proxies=PROXIES) 
        response.raise_for_status() 
        search_results_json = response.json()
        search_items = search_results_json.get('items', [])
        
        results = [{
            'title': item['title'],
            'link': item['link'],
            'snippet': item['snippet']
        } for item in search_items]
        return results
    except requests.exceptions.RequestException as e:
        return f"Google搜索请求失败: {e}"
    except json.JSONDecodeError:
        return "Google搜索响应不是有效的JSON格式。"
    except KeyError:
        return "Google搜索响应中缺少预期的键。"

def get_search_text(q, url): 
    cookie = os.getenv('search_cookie')
    user_agent = os.getenv('search_ueser_agent')

    if not cookie or not user_agent:
        print("警告: 知乎爬虫所需的cookie或user_agent未配置，可能导致爬取失败。")

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'cookie': cookie,
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
    }
    
    title_text = None
    text_d_list = []
    code_list = []

    try:
        if 'zhihu.com/question' in url and 'answer' not in url: 
            headers['authority'] = 'www.zhihu.com'
            res_text = requests.get(url, headers=headers, proxies=PROXIES).text
            res_xpath = etree.HTML(res_text)
            title_elements = res_xpath.xpath('//div/div[1]/div/h1/text()')
            if title_elements: title_text = title_elements[0]
            text_d_list = res_xpath.xpath('//div/div/div/div[2]/div/div[2]/div/div/div[2]/span[1]/div/div/span/p/text()')
        
        elif 'zhuanlan.zhihu.com' in url: 
            headers['authority'] = 'zhuanlan.zhihu.com' 
            res_text = requests.get(url, headers=headers, proxies=PROXIES).text
            res_xpath = etree.HTML(res_text)
            title_elements = res_xpath.xpath('//div[1]/div/main/div/article/header/h1/text()')
            if title_elements: title_text = title_elements[0]
            text_d_list = res_xpath.xpath('//div/main/div/article/div[1]/div/div/div/p/text()')
            code_list = res_xpath.xpath('//div/main/div/article/div[1]/div/div/div//pre/code/text()')  
            
        elif 'zhihu.com/question' in url and 'answer' in url: 
            headers['authority'] = 'www.zhihu.com'
            res_text = requests.get(url, headers=headers, proxies=PROXIES).text
            res_xpath = etree.HTML(res_text)
            title_elements = res_xpath.xpath('//div/div[1]/div/h1/text()') 
            if title_elements: title_text = title_elements[0] 
            text_d_list = res_xpath.xpath('//div[contains(@class, "AnswerItem")]//div[contains(@class, "RichContent-inner")]//span[contains(@class, "RichText")]//p/text()')
            if not text_d_list: 
                 text_d_list = res_xpath.xpath('//div[1]/div/div[3]/div/div/div/div[2]/span[1]/div/div/span/p/text()')

        if not title_text: 
            print(f"警告: 未能从 {url} 提取到标题。")
            return None 

        title = windows_compatible_name(title_text if title_text else "untitled_zhihu_page")

        text_content = ''
        for t_item in text_d_list:
            txt = str(t_item).replace('\n', ' ').strip()
            if txt: text_content += txt + " " 

        if code_list:
            for c_item in code_list:
                co = str(c_item).replace('\n', ' ') 
                text_content += "\n```\n" + co.strip() + "\n```\n" 

        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")     
        json_data = [{
            "link": url,
            "title": title,
            "content": text_content.strip(),
            "tokens": len(encoding.encode(text_content.strip()))
        }]
        
        dir_path = f'./auto_search/{windows_compatible_name(q)}' 
        os.makedirs(dir_path, exist_ok=True)
    
        save_file_name = windows_compatible_name(title)
        with open(os.path.join(dir_path, f"{save_file_name}.json"), 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4) 

        return title 

    except requests.exceptions.RequestException as e:
        print(f"请求知乎页面 {url} 失败: {e}")
        return None
    except Exception as e_general:
        print(f"处理知乎页面 {url} 时发生错误: {e_general}")
        return None

def get_answer(q, g_namespace=None): 
    """
    当你无法回答某个问题时，调用该函数，能够获得答案 (主要针对知乎)
    """
    print('正在接入谷歌搜索，查找和问题相关的答案...')
    search_results = google_search(query=q, num_results=5, site_url='https://zhihu.com/')
    
    if isinstance(search_results, str): 
        return f"搜索失败: {search_results}"
    if not search_results:
        return "未能找到相关的知乎搜索结果。"

    search_with_browser_env = os.getenv("search_with_broswer")
    should_open_browser = search_with_browser_env == '1'
    
    if should_open_browser:
        edge_path = os.getenv("EDGE_BROWSER_PATH", "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe") 
        try:
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
        except Exception as e_wb_reg:
            print(f"注册Edge浏览器失败: {e_wb_reg}. 将不自动打开浏览器。")
            should_open_browser = False 
    
    safe_q_foldername = windows_compatible_name(q)
    folder_path = f'./auto_search/{safe_q_foldername}'
    os.makedirs(folder_path, exist_ok=True)
    
    num_tokens = 0
    content_accumulator = ''
    processed_titles = []

    for item in search_results:
        url = item.get('link')
        if not url:
            continue
        
        print('正在检索：%s' % url)
        
        if should_open_browser:
            try:
                webbrowser.get('edge').open(url)
                time.sleep(3)  
            except Exception as e_wb_open:
                print(f"打开浏览器访问 {url} 失败: {e_wb_open}")
            
        processed_filename = get_search_text(q, url) 
        
        if processed_filename: 
            json_file_path = os.path.join(folder_path, f"{processed_filename}.json")
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    jd = json.load(f)
                
                current_content = jd[0].get('content', '')
                current_tokens = jd[0].get('tokens', 0)

                if num_tokens + current_tokens <= 12000: 
                    content_accumulator += current_content + "\n\n" 
                    num_tokens += current_tokens
                    processed_titles.append(jd[0].get('title', '未知标题'))
                else:
                    print("已达到Token上限，停止添加更多内容。")
                    break
            except FileNotFoundError:
                print(f"未找到保存的JSON文件: {json_file_path}")
            except (json.JSONDecodeError, IndexError, KeyError) as e_json:
                print(f"读取或解析JSON文件 {json_file_path} 失败: {e_json}")
        else:
            print(f"未能从 {url} 获取内容。")

    if not content_accumulator:
        return "未能从搜索结果中提取到有效内容。"
        
    print(f"已处理以下文章标题: {', '.join(processed_titles)}")
    return content_accumulator.strip()

def get_github_readme(dic):
    github_token = os.getenv('GITHUB_TOKEN')
    user_agent = os.getenv('search_user_agent', 'MyPythonApp/1.0') 

    owner = dic.get('owner')
    repo = dic.get('repo')

    if not owner or not repo:
        return "Owner或Repo信息不完整。"
    if not github_token: 
        print("警告: GITHUB_TOKEN未配置，请求可能受限或失败。")

    headers = {
        "Accept": "application/vnd.github.v3.raw", 
        "User-Agent": user_agent
    }
    if github_token: 
        headers["Authorization"] = f"token {github_token}"

    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    
    try:
        response = requests.get(readme_url, headers=headers, proxies=PROXIES)
        response.raise_for_status()
        
        try:
            readme_data = response.json() 
            encoded_content = readme_data.get('content', '')
            if not encoded_content:
                return f"未能从 {readme_url} 的JSON响应中获取README内容。"
            decoded_content = base64.b64decode(encoded_content).decode('utf-8')
            return decoded_content
        except json.JSONDecodeError: 
             return response.text 

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404: # type: ignore
            return f"项目 {owner}/{repo} 的README文件未找到。"
        return f"请求GitHub README失败: {e}"
    except requests.exceptions.RequestException as e:
        return f"请求GitHub README时发生网络错误: {e}"
    except Exception as e_general:
        return f"处理GitHub README时发生未知错误: {e_general}"

def extract_github_repos(search_results):
    if isinstance(search_results, str): 
        return []
    if not search_results:
        return []
        
    repo_links = [result['link'] for result in search_results 
                  if result.get('link') and 
                     'github.com' in result['link'] and 
                     '/issues/' not in result['link'] and 
                     '/blob/' not in result['link'] and 
                     len(result['link'].split('/')) == 5] 

    repos_info = []
    for link in repo_links:
        parts = link.split('/')
        if len(parts) >= 5: 
            repos_info.append({'owner': parts[3], 'repo': parts[4]})
    return repos_info

def get_search_text_github(q, dic):
    owner = dic.get('owner')
    repo = dic.get('repo')

    if not owner or not repo:
        return None 

    title = windows_compatible_name(f"{owner}_{repo}") 
    
    text_content = get_github_readme(dic)
    if "失败" in text_content or "未找到" in text_content or "错误" in text_content: 
        print(f"获取 {owner}/{repo} 的README失败: {text_content}")
        return None

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")     
    json_data = [{
        "title": title, 
        "content": text_content,
        "tokens": len(encoding.encode(text_content))
    }]
    
    safe_q_foldername = windows_compatible_name(q)
    dir_path = f'./auto_search/{safe_q_foldername}'
    os.makedirs(dir_path, exist_ok=True)
    
    with open(os.path.join(dir_path, f"{title}.json"), 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    return title 

def get_answer_github(q, g_namespace=None): 
    """
    当你无法回答某个问题时，调用该函数，能够获得答案 (主要针对GitHub)
    """
    print('正在接入谷歌搜索，查找和问题相关的GitHub项目...')
    search_results_google = google_search(query=q, num_results=5, site_url='https://github.com/')
    
    if isinstance(search_results_google, str): 
        return f"GitHub项目搜索失败: {search_results_google}"
    if not search_results_google:
        return "未能找到相关的GitHub项目。"

    repos_to_check = extract_github_repos(search_results_google)
    if not repos_to_check:
        return "从搜索结果中未能提取到有效的GitHub仓库信息。"
    
    safe_q_foldername = windows_compatible_name(q)
    folder_path = f'./auto_search/{safe_q_foldername}'
    os.makedirs(folder_path, exist_ok=True)
    
    print('正在读取相关项目说明文档 (READMEs)...')
    num_tokens = 0
    content_accumulator = ''
    processed_repo_titles = []

    for repo_info_dict in repos_to_check:
        processed_filename = get_search_text_github(q, repo_info_dict) 
        
        if processed_filename:
            json_file_path = os.path.join(folder_path, f"{processed_filename}.json")
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    jd = json.load(f)
                
                current_content = jd[0].get('content', '')
                current_tokens = jd[0].get('tokens', 0)

                if num_tokens + current_tokens <= 12000:
                    content_accumulator += f"\n\n--- 内容来源: {repo_info_dict['owner']}/{repo_info_dict['repo']} ---\n" + current_content
                    num_tokens += current_tokens
                    processed_repo_titles.append(jd[0].get('title', f"{repo_info_dict['owner']}_{repo_info_dict['repo']}"))
                else:
                    print("已达到Token上限，停止添加更多GitHub README内容。")
                    break
            except FileNotFoundError:
                print(f"未找到保存的GitHub项目JSON文件: {json_file_path}")
            except (json.JSONDecodeError, IndexError, KeyError) as e_json:
                 print(f"读取或解析GitHub项目JSON文件 {json_file_path} 失败: {e_json}")
        else:
            print(f"未能获取或处理仓库 {repo_info_dict.get('owner')}/{repo_info_dict.get('repo')} 的README。")
            
    if not content_accumulator:
        return "未能从搜索到的GitHub项目中提取到有效的README内容。"

    print(f"已处理以下GitHub项目: {', '.join(processed_repo_titles)}")
    print('正在进行最后的整理...')
    return content_accumulator.strip()
