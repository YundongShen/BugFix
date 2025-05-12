import os
from typing import List
import json

def find_frontend_root(file_list):
    assume_frontend_list = []
    # 用于存储每个可能的根路径及其对应的前端文件数量
    root_count = {}

    # 遍历文件列表，筛选出前端文件，并统计每个可能根路径下的文件数量
    for file in file_list:
        file_extension = file.split(".")[-1]
        if file_extension in ["css", "html", "js", "ts", "vue"]:
            assume_frontend_list.append(file)
            # 获取当前文件的目录路径
            dir_path = file.split("/")[0]
            # dir_path = os.path.dirname(file)
            # 若该路径已在字典中，文件数量加 1；否则初始化为 1
            root_count[dir_path] = root_count.get(dir_path, 0) + 1

    if not assume_frontend_list:
        return None

    # 找出包含前端文件数量最多的根路径
    most_common_root = max(root_count, key=root_count.get)
    return most_common_root

# 将前端文件统一在同一目录下
from typing import List
from collections import defaultdict

from typing import List
from collections import defaultdict

def check_frontend_files(file_list: List[List[str]], check_file: List[str] = ["package.json", "index.html", "vite.config.ts", ".eslintrc.cjs"]) -> List[List[str]]:
    file_list = check_files(file_list)
    frontend_root = find_frontend_root(file_list=[x for x, y in file_list])
    
    if not frontend_root:
        return file_list

    # 定义需要检查的文件描述
    check_file_desc = {
        "package.json": "Manages project metadata, dependencies, and scripts for installation, updates, and commands execution.",
        "index.html": "Serves as the entry point, providing the basic structure for web page rendering.",
        "vite.config.ts": "Customizes development and build processes, including server settings, module rules, and output configurations.",
        ".eslintrc.cjs": "Defines coding rules and style guidelines to detect errors and maintain code quality and consistency.",
        "main.ts": "The entry point of the application, responsible for initializing the Vue instance and configuring plugins."
    }

    # 动态推断子目录
    subdirectory_count = defaultdict(int)  # 用于统计每个子目录出现的次数
    for file_path, _ in file_list:
        if frontend_root in file_path:
            # 提取前端根目录之后的第一层子目录
            parts = file_path[len(frontend_root) + 1:].split("/")
            if len(parts) > 1:  # 确保有子目录
                subdirectory_count[parts[0]] += 1

    # 找到出现次数最多的子目录作为默认子目录
    subdirectory = max(subdirectory_count, key=subdirectory_count.get, default="src")

    # 添加 main.ts 到检查列表
    check_file.append("main.ts")
    check_file.append("App.vue")

    new_file_list = []
    for file in file_list:
        found = False
        for sub_file in check_file:
            if sub_file == "main.ts" or sub_file == "App.vue":
                # 检查 main.ts 是否存在于子目录中
                if f"{frontend_root}/{subdirectory}/{sub_file}" in file[0]:
                    new_file_list.append([f"{frontend_root}/{subdirectory}/{sub_file}", file[1] if len(file) > 1 else check_file_desc.get(sub_file, "")])
                    found = True
                    break
            elif sub_file in file[0]:
                new_file_list.append([file[0], file[1] if len(file) > 1 else check_file_desc.get(sub_file, "")])
                found = True
                break
        if not found:
            new_file_list.append(file)

    # 确保所有检查文件都存在
    for sub_file in check_file:
        if sub_file == "main.ts" or sub_file == "App.vue":
            expected_path = f"{frontend_root}/{subdirectory}/{sub_file}"
        else:
            expected_path = f"{frontend_root}/{sub_file}"

        # 如果文件不存在，则添加默认路径和描述
        if not any(expected_path == x[0] for x in new_file_list):
            new_file_list.append([expected_path, check_file_desc.get(sub_file, "")])

    return new_file_list


def check_backend_files(file_list: List[List[str]], language="python"):
    file_list = check_files(file_list)
    main_dict = {
        "python": "main.py"
    }
    main_list = []
    new_file_list = []
    for file, desc in file_list:
        if main_dict.get(language, "main.py") in file:
            main_list.append(file)
        else:
            new_file_list.append([file, desc])
    new_file_list.append([main_dict.get(language, "main.py"), "The main entry point of the backend application, responsible for initializing the application and starting the server."])
    return new_file_list


def check_files(file_list: List[List[str]]):
    new_file_list = []
    # 可能会出现部分文件以/开头的，检查一下,去掉开头的"/“
    for file, desc in file_list:
        if file.startswith("/"):
            new_file_list.append([file[1:], desc])
        else:
            new_file_list.append([file, desc])
    return new_file_list


def chekc_file_realtion(file_list, file_relation):
    def find_full_name(short_name):
        for full_name, desc in file_list:
            if full_name.endswith(short_name):
                return full_name
        return short_name

    new_file_rela = []
    for file, dependencies in file_relation:
        full_file = find_full_name(file)
        full_dependencies = [find_full_name(dep) for dep in dependencies]
        new_file_rela.append([full_file, full_dependencies])

    return new_file_rela

def get_values(data, key, default_return=""):
    if isinstance(data, str):
        data_dict = json.loads(data)
    else:
        data_dict = json.loads(data.content)
    if isinstance(key, str):
        return data_dict.get(key, default_return)
    else:
        return data_dict.get(key.key, default_return)

if __name__ == "__main__":
    file_list = [
        # "main.py",
        # "backend/app/core/main.py",
        # "backend/app/main.py",
        "requirements.txt",
        "backend/app/core/config.py",
        "backend/app/database/connection.py",
        "backend/app/database/models.py",
        "backend/app/modules/calculator/api.py",
        "backend/app/modules/calculator/services.py",
        "backend/app/modules/calculator/models.py",
        "frontend/src/main.ts",
        "frontend/src/App.vue",
        "frontend/src/components/Calculator.vue",
        "frontend/src/stores/calculatorStore.ts",
        "frontend/src/router/index.ts",
        "frontend/src/assets/styles.css",
        "frontend/sss/index.html",
        "frontend/vite.config.ts",
        "package.json"
    ]
    print(check_backend_files(file_list=file_list))
    
