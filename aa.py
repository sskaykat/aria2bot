import os
import subprocess
import shutil

def upload_to_telegram(directory):
    telegram_target = 't.me/+lUDCI5QCgzRkYWM5'
    size_threshold = 100 * 1024 * 1024  # 100MB in bytes

    # 遍历目录及其子目录中的所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)

            # 只上传大于100MB的文件
            if file_size > size_threshold:
                command = ['telegram-upload', '--to', telegram_target, file_path]

                try:
                    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print(f"上传成功: {file_path}")
                except subprocess.CalledProcessError as e:
                    print(f"上传失败: {file_path}\n错误信息: {e.stderr}")

    # 删除目录中的所有文件和子目录
    try:
        shutil.rmtree(directory)
        os.makedirs(directory)  # 重新创建目录
        print("文件已成功删除")
    except OSError as e:
        print(f"删除文件失败: {e.strerror}")

# 调用上传函数
upload_to_telegram('/root/downloads')
