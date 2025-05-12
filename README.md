# 版本更新 2025/04/11

- 新增restore功能
- 新增接口，`generate_product` , `generate_codes`
- 新增前端独立编写，前端环境安装，前端资源打包


## 功能介绍

```python
def generate_product(
        idea,
        project_name="",
        logger_stream_obj=None,
        sid: str = "",
        local: bool = True
):
    """
    基于用户输入的需求生成产品。

    :param idea: 用户输入的需求，用于描述要生成的产品的具体要求。
    :param project_name: 项目的名称，可选参数。若为空，模型将根据需求自动命名项目。
    :param logger_stream_obj: 用于 OH（可能是某个特定系统或框架）的日志记录器会话对象，默认值为 None。
    :param sid: 会话 ID，用于标识当前的操作会话，方便跟踪和管理。
    :param local: 布尔值，指示是否进行 Metagpt 的本地调试。若为 True，则在本地进行操作；若为 False，则与 OH 进行通信。
    """
    pass

    """
    :return: 根据用户输入需求，生成的PRD文档，测试文档，架构文档

    """
def generate_codes(
        project_name="",
        logger_stream_obj=None,
        sid: str = "",
        local: bool = True
):
    """
    为指定项目生成代码。

    :param project_name: 项目的名称，可选参数。用于指定要生成代码的项目。
    :param logger_stream_obj: 用于 OH（可能是某个特定系统或框架）的日志记录器会话对象，默认值为 None。
    :param sid: 会话 ID，用于标识当前的操作会话，方便跟踪和管理。
    :param local: 布尔值，指示是否进行 Metagpt 的本地调试。若为 True，则在本地进行操作；若为 False，则与 OH 进行通信。

    """
    pass

    """
    :return: 根据传入sid值，从上一轮产生或修改后，用户确认的文档开始，生成代码以及代码测试。
    若联合使用，则需要sid，projetc_name保持一致
    """


```