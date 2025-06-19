# 切换到项目根目录
cd solana-analyzer

# 创建并写入 __init__.py
echo "# 让 utils 成为一个 Python 模块" > utils/__init__.py

# 添加并提交
git add utils/__init__.py
git commit -m "fix: add __init__.py to utils folder"
git push