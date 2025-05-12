from metagpt.software_company import generate_repo, ProjectRepo
# repo: ProjectRepo = generate_repo(idea="请生成一个前后端分离且可以运行的项目。具体的要求如下： 社情民意分析平台功能清单，具体需要以下功能："
# "一、工单标签管理 "
# "1、标签管理：用户可以在此模块新增、删除标签。 "
# "2、标签匹配：选择相应标签，点击“匹配”按钮，系统将会自动匹配与标签内容相关联的工单，并将工单打上相应标签。 "
# "3、标签查询：用户可以通过选择标签查询该标签下的所有工单信息，点击可以查看工单详情，用户也可以将工单从相应的标签目录下删除。 "
# "二、工单查询 该模块通过关键字、诉求类型、所属区域、工单时间等内容查询工单信息，点击查询按钮可以得到查询结果列表，点击列表里的某一条工单，可以查看工单详情。 "
# "三、工单统计 "
# "1、热门事项排名：通过时间段查询热门事项排名，可以选择诉求类型（单选或多选），系统自动统计所有热门事项的数量排名情况； "
# "2、热门板块排名：通过时间段统计一段时间内各个板块的工单数量排名，按每个板块的事项数量总数排名，后面展示该板块里数量排名前三的事项。 "
# "3、热门小区排名：通过时间段查询宜兴市各个小区发生的事项数量排名，可以按小区数量排名或者按事项数量排名。"
# "", n_round=100, code_review=False, project_name="11")
repo = ProjectRepo = generate_repo(idea="写一个todo list", code_review=False,n_round=100, sid="0430", sio=None,local = True, project_name="project", simulate=True)
                                #    investment=30000000000.0,
								#   n_round=80,
    							#   code_review=True,
    							#   run_tests=True,
    							#   implement=True)
