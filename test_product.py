from metagpt.product_roles import generate_product


repo = generate_product(idea="请生成一个计算器应用，包含加减乘除", project_name="123",
                        sid="x12", local=True)