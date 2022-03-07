# 1. github-to-gitea
将github用户关注的仓库同步克隆到自建的Gitea服务上

# 2. 部署
## 2.1. 二进制运行
下载并解压Releases中的二进制文件（基于Ubuntu1804打包测试，其他系统自行测试）

根据需要修改app.conf文件

运行如下
```bash
./gta -c app.conf
```

## 2.2. 源码运行
安装Python3.7.2，并克隆仓库后使用终端打开该仓库，使用pip安装依赖库
```bash
pip3 install -r requirements.txt
```

运行 main.py
```bash
python3 main.py -c app.conf
```

# 3. 二次开发
安装Python3.7.2，2，并克隆仓库后使用终端打开该仓库，使用pip安装依赖库
```bash
pip3 install -r requirements.txt
```

使用VSCode开发项目，配置如下
```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceRoot}/src/main.py",
            "args": [
                "--config=conf/app.conf"
            ],
            "console": "internalConsole"
        }
    ]
}
```
