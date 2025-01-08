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
    keyboard = types.ReplyKeyboardMarkup(row_width=3,resize_keyboard=True)
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

@bot.message_handler(func=lambda message: message.text == '添加下载任务')
def handle_add_download(message):
    # 提示用户回复一个链接
    bot.reply_to(message, '请回复一个HTTP或磁力链接：')

    # 设置Bot等待用户回复的处理函数
    bot.register_next_step_handler(message, process_link)

@bot.message_handler(func=lambda message: message.text == '活跃任务')
def handle_downloading(message):
    # 调用远程aria2获取正在下载的任务
    method = "aria2.tellActive"
    params = [
        f"token:{aria2c_rpc_key}"
    ]
    response = send_request(method, params)

    # 检查响应结果
    if "result" in response:
        # 提取任务详情
        tasks = response["result"]
        task_details = []
        for task in tasks:
            task_details.append(f"任务ID: {task['gid']}\n文件名: {task['files'][0]['path']}\n下载进度: {task['completedLength']}/{task['totalLength']}")

        # 将任务详情回复给用户
        if task_details:
            bot.reply_to(message, "正在下载的任务详情：\n\n" + "\n\n".join(task_details))
        else:
            bot.reply_to(message, "当前没有正在下载的任务。")
    elif "error" in response:
        # 回复用户获取任务详情出错的消息
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取任务详情出错：{error_message}')
    else:
        # 回复用户获取任务详情出错的消息
        bot.reply_to(message, '获取任务详情出错！')

def process_link(message):
    # 获取用户回复的链接
    file_url = message.text
    
    # 调用远程aria2进行文件下载
    method = "aria2.addUri"
    params = [
        f"token:{aria2c_rpc_key}",
        [file_url],
        {}
    ]
    response = send_request(method, params)
    
    # 检查响应结果
    if "result" in response:
        # 回复用户下载完成的消息
        bot.reply_to(message, '文件下载已开始！')
    elif "error" in response:
        # 回复用户下载出错的消息
        error_message = response["error"]["message"]
        bot.reply_to(message, f'文件下载出错：{error_message}')
    else:
        # 回复用户下载出错的消息
        bot.reply_to(message, '文件下载出错！')


@bot.message_handler(func=lambda message: message.text == '全部开始')
def handle_resume_all(message):
    # 调用远程aria2开始所有已暂停任务
    method = "aria2.unpauseAll"
    params = [
        f"token:{aria2c_rpc_key}"
    ]
    response = send_request(method, params)

    # 检查响应结果
    if "result" in response:
        bot.reply_to(message, '所有已暂停的任务已开始！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'开始任务出错：{error_message}')
    else:
        bot.reply_to(message, '开始任务出错！')

@bot.message_handler(func=lambda message: message.text == '全部暂停')
def handle_pause_all(message):
    # 调用远程aria2暂停所有任务
    method = "aria2.pauseAll"
    params = [
        f"token:{aria2c_rpc_key}"
    ]
    response = send_request(method, params)

    # 检查响应结果
    if "result" in response:
        bot.reply_to(message, '所有任务已暂停！')
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'暂停任务出错：{error_message}')
    else:
        bot.reply_to(message, '暂停任务出错！')

@bot.message_handler(func=lambda message: message.text == '全部删除')
def handle_delete_all(message):
    # 调用远程aria2获取所有任务
    method = "aria2.tellActive"
    params = [
        f"token:{aria2c_rpc_key}"
    ]
    response = send_request(method, params)

    # 检查响应结果
    if "result" in response:
        # 获取所有活跃任务的GID（任务ID）
        gids = [task["gid"] for task in response["result"]]

        # 遍历所有活跃任务，调用aria2.remove方法逐个删除
        for gid in gids:
            method = "aria2.remove"
            params = [
                f"token:{aria2c_rpc_key}",
                gid
            ]
            remove_response = send_request(method, params)

            if "error" in remove_response:
                # 删除任务出错
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
    # 调用远程aria2获取暂停中的任务
    method = "aria2.tellWaiting"
    params = [
        f"token:{aria2c_rpc_key}",
        0,  # 从任务列表的第一个任务开始
        1000,  # 最多返回1000个任务
    ]
    response = send_request(method, params)

    # 检查响应结果
    if "result" in response:
        # 获取所有暂停中任务的信息
        paused_tasks = response["result"]

        if len(paused_tasks) > 0:
            # 遍历所有暂停中任务，获取任务信息并发送给用户
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
    # 调用远程aria2获取下载器状态
    method = "aria2.getGlobalStat"
    params = [f"token:{aria2c_rpc_key}"]
    response = send_request(method, params)

    # 检查响应结果
    if "result" in response:
        # 获取下载器状态信息
        status = response["result"]

        # 构建状态消息
        status_message = f"当前活跃任务数：{status['numActive']}\n"
        status_message += f"当前等待任务数：{status['numWaiting']}\n"
        status_message += f"当前暂停任务数：{status['numStopped']}\n"
        status_message += f"总下载速度：{status['downloadSpeed']}B/s\n"
        status_message += f"总上传速度：{status['uploadSpeed']}B/s\n"

        # 发送状态消息给用户
        bot.reply_to(message, status_message)
    elif "error" in response:
        error_message = response["error"]["message"]
        bot.reply_to(message, f'获取下载器状态出错：{error_message}')
    else:
        bot.reply_to(message, '获取下载器状态出错！')

# @bot.message_handler(commands=['upload'])
@bot.message_handler(func=lambda message: message.text == '上传文件')
def handle_upload(message):
    try:
        # 执行同级目录下的 aa.py 文件
        result = subprocess.run(['python3', 'aa.py'], capture_output=True, text=True)
        if result.returncode == 0:
            bot.reply_to(message, '文件 aa.py 执行成功！\n' + result.stdout)
        else:
            bot.reply_to(message, '文件 aa.py 执行失败！\n' + result.stderr)
    except Exception as e:
        bot.reply_to(message, f'执行文件时发生错误: {str(e)}')
        
@bot.message_handler(func=lambda message: message.text == '关闭键盘')
def handle_close_keyboard(message):
    # 创建 ReplyKeyboardRemove 对象来关闭键盘
    remove_keyboard = types.ReplyKeyboardRemove()

    # 发送关闭键盘的消息
    bot.send_message(message.chat.id, '已关闭键盘！', reply_markup=remove_keyboard)

bot.polling()
