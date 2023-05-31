# 概览
一个转发http请求的服务，主要用于在内网中转发API请求，比如OpenAI。

# 用法

首先需要有一个类似下面的yaml配置文件：

```yml
server:
  host: "0.0.0.0"   # 服务监听的地址
  port: 2323        # 服务监听的端口
proxies:            # 配置代理信息，是一个[{target,proxy}]的数组，最后会转换成{target:proxy}这样的字典，支持协议和域名匹配（这里的target和下面的forwarders里面的target是对应的），详细参考https://requests.readthedocs.io/en/latest/user/advanced/#proxies
  - target: "https://api.openai.com"  # 转发"https://api.openai.com"的时候使用"http://proxy1:1204"这个代理
    proxy: "http://proxy1:1204"
  - target: "https://www.baidu.com"
    proxy: "http://user1:pass1@proxy2:1205"
forwarders:         # 配置转发信息，通过请求的host来确定转发到哪一个地址
  - description: "forward openai test"
    host: "127.0.0.1:2323"   # 如果请求的主机名是"127.0.0.1:2323"那么就转发到"https://api.openai.com"
    target: "https://api.openai.com"
    headers: ["Content-Type", "Authorization"]  # 当前需要转发的请求头，主要用于转发认证信息
  - description: "forward baidu test"
    host: "127.0.0.2:2323"
    target: "https://www.baidu.com"
```

将上面文件保存为`config.yaml`后可以直接通过下面命令启动：

```sh
python http-forwarder.py
```

或者通过docker：

```sh
docker run -d -v $PWD/config.yaml:/app/config.yaml -p 2323:2323 ecat/http-forwarder
```

也可以带上`-c /path/to/config.yaml`参数手动指定`config.yaml`文件路径。

