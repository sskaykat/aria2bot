import telebot
import requests
import json
from telebot import types
import config
import subprocess

# 设置aria2c的RPC地址和密钥
aria2c_rpc_url = config.aria2c_rpc_url
aria2c_rpc_key = config.aria2c_rpc_key

# 设置Telegram bot的token
bot_token = config.bot_token
bot = telebot.TeleBot(bot_token)

# 定义发送请求的函数
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
    response = requests.post(aria2c_rpc_url, headers=headers, data=json.dumps(payload))
    return response.json()

@bot.message_handler(commands=['start'])
def handle_start(message):
    # 创建自定义键盘
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button1 = types.KeyboardButton('添加下载任务')
    button2 = types.KeyboardButton('活跃任务')
    button3 = types.KeyboardButton('正在等待')
    button4 = types.KeyboardButton('全部开始')
    button5 = types.KeyboardButton('全部暂停')
    button6 = types.KeyboardButton('全部删除')
    button7 = types.KeyboardButton('下载器状态')
    button8 = types.KeyboardButton('上传文件')
    button9 = types.KeyboardButton('关闭键盘')
    keyboard.add(button1, button2, button3, button4, button5, button6, button7, button8, button9)

    # 发送欢迎消息和自定义键盘
    bot.send_message(message.chat.id, '👉欢迎使用下载机器人💓💓', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == '上传文件')
def handle_upload_button(message):
    try:
        # 执行同级目录下的 aa.py 文件
        result = subprocess.run(['python3', 'aa.py'], capture_output=True, text=True)
        if result.returncode == 0:
            bot.reply_to(message, '文件 aa.py 执行成功！\n' + result.stdout)
        else:
            bot.reply_to(message, '文件 aa.py 执行失败！\n' + result.stderr)
    except Exception as e:
        bot.reply_to(message, f'执行文件时发生错误: {str(e)}')

@bot.message_handler(func=lambda message: message.text == '添加下载任务')
def handle_add_download(message):
    bot.reply_to(message, '请回复一个HTTP或磁力链接：')
    bot.register_next_step_handler(message, process_link)

@bot.message_handler(func=lambda message: message.text == '活跃任务')
def handle_downloading(message):
    method = "aria2.tellActive"
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        tasks = response["result"]
        task_details = []
        for task in tasks:
            task_details.append(f"任务ID: {task['gid']}\n文件名: {task['files'][0]['path']}\n下载进度: {task['completedLength']}/{task['totalLength']}")
        if task_details:
            bot.reply_to(message, "正在下载的任务详情：\n\n" + "\n\n".join(task_details))
        else:
            bot.reply_to(message, "当前没有正在下载的任务。")
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取任务详情出错：{error_message}')
    else:
        bot.reply_to(message, '获取任务详情出错！')

def process_link(message):
    file_url = message.text
    method = "aria2.addUri"
    params = [f"token:{aria2c_rpc_key}", [file_url], {}]
    response = send_request(method, params)
    if "result" in response:
        bot.reply_to(message, '文件下载已开始！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'文件下载出错：{error_message}')
    else:
        bot.reply_to(message, '文件下载出错！')

@bot.message_handler(func=lambda message: message.text == '全部开始')
def handle_resume_all(message):
    method = "aria2.unpauseAll"
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        bot.reply_to(message, '所有已暂停的任务已开始！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'开始任务出错：{error_message}')
    else:
        bot.reply_to(message, '开始任务出错！')

@bot.message_handler(func=lambda message: message.text == '全部暂停')
def handle_pause_all(message):
    method = "aria2.pauseAll"
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        bot.reply_to(message, '所有任务已暂停！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'暂停任务出错：{error_message}')
    else:
        bot.reply_to(message, '暂停任务出错！')

@bot.message_handler(func=lambda message: message.text == '全部删除')
def handle_delete_all(message):
    method = "aria2.tellActive"
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        gids = [task["gid"] for task in response["result"]]
        for gid in gids:
            method = "aria2.remove"
            params = [f"token:{aria2c_rpc_key}", gid]
            remove_response = send_request(method, params)
            if "error" in remove_response:
                error_message = remove_response["error"]["message"]
                bot.reply_to(message, f'删除任务出错：{error_message}')
                return
        bot.reply_to(message, '所有任务已删除！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取任务列表出错：{error_message}')
    else:
        bot.reply_to(message, '获取任务列表出错！')

@bot.message_handler(func=lambda message: message.text == '正在等待')
def handle_list_paused(message):
    method = "aria2.tellWaiting"
    params = [f"token:{aria2c_rpc_key}", 0, 1000]
    response = send_request(method, params)
    if "result" in response:
        paused_tasks = response["result"]
        if len(paused_tasks) > 0:
            task_list = ''
            for task in paused_tasks:
                task_list += f'任务ID：{task["gid"]}\n文件名：{task["files"][0]["path"]}\n\n'
            bot.reply_to(message, f'暂停中的任务列表：\n\n{task_list}')
        else:
            bot.reply_to(message, '暂停中的任务为空！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取任务列表出错：{error_message}')
    else:
        bot.reply_to(message, '获取任务列表出错！')

@bot.message_handler(func=lambda message: message.text == '下载器状态')
def handle_aria2_status(message):
    method = "aria2.getGlobalStat"
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)
    if "result" in response:
        status = response["result"]
        status_message = f"当前活跃任务数：{status['numActive']}\n"
        status_message += f"当前等待任务数：{status['numWaiting']}\n"
        status_message += f"当前暂停任务数：{status['numStopped']}\n"
        status_message += f"总下载速度：{status['downloadSpeed']}B/s\n"
        status_message += f"总上传速度：{status['uploadSpeed']}B/s\n"
        bot.reply_to(message, status_message)
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取下载器状态出错：{error_message}')
    else:
        bot.reply_to(message, '获取下载器状态出错！')

@bot.message_handler(func=lambda message: message.text == '关闭键盘')
def handle_close_keyboard(message):
    remove_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, '已关闭键盘！', reply_markup=remove_keyboard)

bot.polling()
