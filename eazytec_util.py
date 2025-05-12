# 尝试获取机器的IP作为实例ID
# 尝试获取一个稳定的机器标识符，重启后不会改变
# 首先尝试获取机器的MAC地址作为稳定标识符
import uuid
import os
import platform
import socket

def get_stable_machine_id():
    """获取稳定的机器ID，重启后不变"""
    # 首先检查环境变量中是否已定义机器ID
    if os.environ.get("OPENHANDS_MACHINE_ID"):
        return os.environ.get("OPENHANDS_MACHINE_ID")
        
    system = platform.system()
    
    # 检查是否在K8s环境中
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        # 使用主机名作为标识符（在K8s中通常是Pod名称）
        return f"k8s-{os.environ.get('HOSTNAME', '')}"
    
    # 尝试使用各平台特定的方法获取稳定ID
    if system == "Linux":
        # 在Linux上尝试读取machine-id
        try:
            with open("/etc/machine-id", "r") as f:
                return f"linux-{f.read().strip()}"
        except:
            # 检查是否在K8s环境中
            if os.environ.get("KUBERNETES_SERVICE_HOST"):
                # 使用主机名作为标识符（在K8s中通常是Pod名称）
                return f"k8s-{os.environ.get('HOSTNAME', '')}"
    
    elif system == "Darwin":  # macOS
        try:
            # 使用macOS的IOPlatformUUID
            import subprocess
            result = subprocess.check_output(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]).decode()
            for line in result.split("\n"):
                if "IOPlatformUUID" in line:
                    return f"mac-{line.split('=')[1].strip().strip(chr(34))}"
        except:
            pass
            
    elif system == "Windows":
        try:
            # 使用Windows的MachineGuid
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\Microsoft\Cryptography") as key:
                machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                return f"win-{machine_guid}"
        except:
            pass
    
    # 如果以上方法都失败，使用主机名和一个持久化的UUID
    try:
        hostname = socket.gethostname()
        
        # 尝试从文件读取之前生成的UUID
        uuid_file = os.path.join(os.path.expanduser("~"), ".openhands_machine_id")
        if os.path.exists(uuid_file):
            with open(uuid_file, "r") as f:
                return f"{hostname}-{f.read().strip()}"
        else:
            # 生成新UUID并保存
            machine_uuid = str(uuid.uuid4())
            try:
                with open(uuid_file, "w") as f:
                    f.write(machine_uuid)
            except:
                pass
            return f"{hostname}-{machine_uuid}"
    except:
        # 最后的后备方案：生成一个新的UUID
        return f"unknown-{str(uuid.uuid4())}"