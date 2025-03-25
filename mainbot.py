import telebot
import requests
import json
from telebot import types
import config
import subprocess
import logging  # 导入 logging 模块

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置aria2c的RPC地址和密钥
aria2c_rpc_url = config.aria2c_rpc_url
aria2c_rpc_key = config.aria2c_rpc_key

# 设置Telegram bot的token
bot_token = config.bot_token
bot = telebot.TeleBot(bot_token)

# 常量定义
BUTTON_ADD_TASK = '添加下载任务'
BUTTON_ACTIVE_TASKS = '活跃任务'
BUTTON_WAITING_TASKS = '正在等待'
BUTTON_START_ALL = '全部开始'
BUTTON_PAUSE_ALL = '全部暂停'
BUTTON_DELETE_ALL = '全部删除'
BUTTON_STATUS = '下载器状态'
BUTTON_UPLOAD_FILE = '上传文件'
BUTTON_CLOSE_KEYBOARD = '关闭键盘'

ARIA2_METHOD_ADD_URI = "aria2.addUri"
ARIA2_METHOD_TELL_ACTIVE = "aria2.tellActive"
ARIA2_METHOD_TELL_WAITING = "aria2.tellWaiting"
ARIA2_METHOD_UNPAUSE_ALL = "aria2.unpauseAll"
ARIA2_METHOD_PAUSE_ALL = "aria2.pauseAll"
ARIA2_METHOD_REMOVE = "aria2.remove"
ARIA2_METHOD_GET_GLOBAL_STAT = "aria2.getGlobalStat"

# 定义发送请求的函数 (改进错误处理)
def send_request(method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": method,
        "params": params
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(aria2c_rpc_url, headers=headers, data=json.dumps(payload), timeout=10) # 添加超时时间
        response.raise_for_status() # 检查 HTTP 错误
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"网络请求错误: {e}") # 记录网络错误日志
        return {"error": {"message": f"网络请求错误: {e}"}} # 返回错误信息给调用者
    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析错误: {e}, 响应内容: {response.text if 'response' in locals() else 'N/A'}") # 记录 JSON 解析错误
        return {"error": {"message": f"JSON 解析错误: {e}"}} # 返回错误信息


@bot.message_handler(commands=['start'])
def handle_start(message):
    # 创建自定义键盘
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button1 = types.KeyboardButton(BUTTON_ADD_TASK)
    button2 = types.KeyboardButton(BUTTON_ACTIVE_TASKS)
    button3 = types.KeyboardButton(BUTTON_WAITING_TASKS)
    button4 = types.KeyboardButton(BUTTON_START_ALL)
    button5 = types.KeyboardButton(BUTTON_PAUSE_ALL)
    button6 = types.KeyboardButton(BUTTON_DELETE_ALL)
    button7 = types.KeyboardButton(BUTTON_STATUS)
    button8 = types.KeyboardButton(BUTTON_UPLOAD_FILE)
    button9 = types.KeyboardButton(BUTTON_CLOSE_KEYBOARD)
    keyboard.add(button1, button2, button3, button4, button5, button6, button7, button8, button9)

    # 发送欢迎消息和自定义键盘 (使用 Markdown)
    welcome_message = "👉欢迎使用下载机器人💓💓\n\n" \
                      "点击下方按钮开始操作："
    bot.send_message(message.chat.id, welcome_message, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == BUTTON_UPLOAD_FILE)
def handle_upload_button(message):
    try:
        # 执行同级目录下的 aa.py 文件
        bot.reply_to(message, "正在执行文件上传脚本...") # 添加执行脚本的提示
        result = subprocess.run(['python3', 'aa.py'], capture_output=True, text=True)
        if result.returncode == 0:
            bot.reply_to(message, f'文件 aa.py 执行成功！\n```{result.stdout}```', parse_mode='Markdown') # 使用 Markdown 代码块
        else:
            bot.reply_to(message, f'文件 aa.py 执行失败！\n```{result.stderr}```', parse_mode='Markdown') # 使用 Markdown 代码块
    except Exception as e:
        error_msg = f'执行文件时发生错误: {str(e)}'
        logging.error(error_msg) # 记录错误日志
        bot.reply_to(message, error_msg)

@bot.message_handler(func=lambda message: message.text == BUTTON_ADD_TASK)
def handle_add_download(message):
    bot.reply_to(message, '请回复一个HTTP或磁力链接：')
    bot.register_next_step_handler(message, process_link)

@bot.message_handler(func=lambda message: message.text == BUTTON_ACTIVE_TASKS)
def handle_downloading(message):
    bot.reply_to(message, "正在获取活跃任务列表...") # 添加获取任务列表的提示
    method = ARIA2_METHOD_TELL_ACTIVE
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        tasks = response["result"]
        if tasks:
            task_details = ["**正在下载的任务详情：**\n"] # 使用 Markdown 标题
            for task in tasks:
                filename = "N/A"
                if task['files'] and task['files'][0]['path']:
                    filename = task['files'][0]['path'].split('/')[-1] # 提取文件名
                total_length = int(task['totalLength'])
                completed_length = int(task['completedLength'])
                progress_percent = (completed_length / total_length) * 100 if total_length > 0 else 0
                task_details.append(f"任务ID: `{task['gid']}`") # 使用 Markdown 代码格式
                task_details.append(f"文件名: {filename}")
                task_details.append(f"下载进度: {progress_percent:.2f}% ({human_readable_size(completed_length)}/{human_readable_size(total_length)})") # 显示百分比和人性化大小
                task_details.append("---") # 分隔线
            bot.reply_to(message, "\n".join(task_details), parse_mode='Markdown') # 使用 Markdown
        else:
            bot.reply_to(message, "当前没有正在下载的任务。")
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取活跃任务详情出错：{error_message}')
    else:
        bot.reply_to(message, '获取活跃任务详情出错！')

def process_link(message):
    file_url = message.text
    bot.reply_to(message, "正在添加下载任务...") # 添加添加任务的提示
    method = ARIA2_METHOD_ADD_URI
    params = [f"token:{aria2c_rpc_key}", [file_url], {}]
    response = send_request(method, params)
    if "result" in response:
        bot.reply_to(message, '文件下载已开始！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'文件下载出错：{error_message}')
    else:
        bot.reply_to(message, '文件下载出错！')

@bot.message_handler(func=lambda message: message.text == BUTTON_START_ALL)
def handle_resume_all(message):
    bot.reply_to(message, "正在恢复所有任务...") # 添加恢复任务的提示
    method = ARIA2_METHOD_UNPAUSE_ALL
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        bot.reply_to(message, '所有已暂停的任务已开始！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'开始任务出错：{error_message}')
    else:
        bot.reply_to(message, '开始任务出错！')

@bot.message_handler(func=lambda message: message.text == BUTTON_PAUSE_ALL)
def handle_pause_all(message):
    bot.reply_to(message, "正在暂停所有任务...") # 添加暂停任务的提示
    method = ARIA2_METHOD_PAUSE_ALL
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        bot.reply_to(message, '所有任务已暂停！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'暂停任务出错：{error_message}')
    else:
        bot.reply_to(message, '暂停任务出错！')

@bot.message_handler(func=lambda message: message.text == BUTTON_DELETE_ALL)
def handle_delete_all(message):
    bot.reply_to(message, "正在删除所有活跃任务...") # 添加删除任务的提示
    method = ARIA2_METHOD_TELL_ACTIVE
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        gids = [task["gid"] for task in response["result"]]
        if not gids:
            bot.reply_to(message, '当前没有活跃任务可以删除！')
            return

        deleted_count = 0
        error_occurred = False
        for gid in gids:
            method = ARIA2_METHOD_REMOVE
            params = [f"token:{aria2c_rpc_key}", gid]
            remove_response = send_request(method, params)
            if "error" in remove_response:
                error_message = remove_response["error"]["message"]
                bot.reply_to(message, f'删除任务 {gid} 出错：{error_message}')
                error_occurred = True # 标记发生错误
            else:
                deleted_count += 1

        if not error_occurred:
            bot.reply_to(message, f'成功删除 {deleted_count} 个任务！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取任务列表出错：{error_message}')
    else:
        bot.reply_to(message, '获取任务列表出错！')

@bot.message_handler(func=lambda message: message.text == BUTTON_WAITING_TASKS)
def handle_list_paused(message):
    bot.reply_to(message, "正在获取等待中的任务列表...") # 添加获取等待任务列表的提示
    method = ARIA2_METHOD_TELL_WAITING
    params = [f"token:{aria2c_rpc_key}", 0, 1000]
    response = send_request(method, params)
    if "result" in response:
        paused_tasks = response["result"]
        if paused_tasks:
            task_list = ["**暂停中的任务列表：**\n"] # 使用 Markdown 标题
            for task in paused_tasks:
                filename = "N/A"
                if task['files'] and task['files'][0]['path']:
                    filename = task['files'][0]['path'].split('/')[-1] # 提取文件名
                task_list.append(f"任务ID: `{task['gid']}`") # 使用 Markdown 代码格式
                task_list.append(f"文件名: {filename}")
                task_list.append("---") # 分隔线
            bot.reply_to(message, "\n".join(task_list), parse_mode='Markdown') # 使用 Markdown
        else:
            bot.reply_to(message, '暂停中的任务为空！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取任务列表出错：{error_message}')
    else:
        bot.reply_to(message, '获取任务列表出错！')

@bot.message_handler(func=lambda message: message.text == BUTTON_STATUS)
def handle_aria2_status(message):
    bot.reply_to(message, "正在获取下载器状态...") # 添加获取下载器状态的提示
    method = ARIA2_METHOD_GET_GLOBAL_STAT
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        status = response["result"]
        status_message = "**下载器状态：**\n" # 使用 Markdown 标题
        status_message += f"当前活跃任务数：`{status['numActive']}`\n" # 使用 Markdown 代码格式
        status_message += f"当前等待任务数：`{status['numWaiting']}`\n"
        status_message += f"当前停止任务数：`{status['numStopped']}`\n"
        status_message += f"总下载速度：`{human_readable_size(int(status['downloadSpeed']))}/s`\n" # 人性化显示速度
        status_message += f"总上传速度：`{human_readable_size(int(status['uploadSpeed']))}/s`\n" # 人性化显示速度
        bot.reply_to(message, status_message, parse_mode='Markdown') # 使用 Markdown
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取下载器状态出错：{error_message}')
    else:
        bot.reply_to(message, '获取下载器状态出错！')

@bot.message_handler(func=lambda message: message.text == BUTTON_CLOSE_KEYBOARD)
def handle_close_keyboard(message):
    remove_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, '已关闭键盘！', reply_markup=remove_keyboard)

# 辅助函数：将字节大小转换为更易读的格式
def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    units = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    import math
    i = math.floor(math.log(size_bytes, 1024))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"


bot.polling()
