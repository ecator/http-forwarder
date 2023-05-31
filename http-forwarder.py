#!/usr/bin/env python

import argparse
import yaml
import sys
import http.server
import http.client
import requests

configFile = 'config.yaml'
configDefault = {'server': {'host': "127.0.0.1", 'port': 2323},
                 'proxies': None,
                 'forwarder': {'host': "127.0.0.1", 'headers': ["Content-Type"]}}
config = {}


def GetRealHost(headers: http.client.HTTPMessage) -> str:
    '''获取实际的Host信息'''
    # print(headers,flush=True)
    for header, value in headers.items():
        if header.lower() == 'x-forwarded-host' or header.lower() == 'host':
            return value


def GetForwarder(forwardHost: str) -> dict:
    '''从配置文件中获取跟host相匹配的forwarder配置

    没有匹配的就返回None
    '''
    for forwarder in config['forwarders']:
        if forwarder['host'] == forwardHost:
            return forwarder
    return None


def TransformProxies(proxies: list) -> dict:
    '''将[{target,proxy}]转换成{target:proxy}形式'''
    return {x['target']: x['proxy'] for x in proxies}


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def badresponse(self, msg: str):
        self.send_response(http.HTTPStatus.BAD_REQUEST)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(msg.encode())

    def do_request(self, method: str):
        targetPath = self.path

        forwardHost = GetRealHost(self.headers)
        forwarder = GetForwarder(forwardHost)
        if forwarder is None:
            self.badresponse('no matching forwarder')
            return
        forwardTarget = forwarder['target']
        proxies = None
        if not config['proxies'] is None:
            proxies = TransformProxies(config['proxies'])

        # 获取请求的headers
        forwarderHeaders = {}
        for header, value in self.headers.items():
            if header.lower() in [x.lower() for x in forwarder['headers']]:
                forwarderHeaders[header] = value

        # 从客户端读取请求体
        contentLength = int(self.headers.get('Content-Length', 0))
        forwardBody = self.rfile.read(contentLength)

        # 发送请求到代理服务器
        try:
            response = None
            response = requests.request(
                method=method, url=f'{forwardTarget}{targetPath}', headers=forwarderHeaders, data=forwardBody, proxies=proxies)

            # 转发响应给客户端
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                if not header.lower() in ('transfer-encoding', 'content-encoding', 'content-length', 'connection', 'date', 'server'):
                    self.send_header(header, value)
            self.send_header('Connection', 'close')
            self.end_headers()
            r = response.content
            self.wfile.write(r)
        except Exception as e:
            self.badresponse(str(e))
        finally:
            # 关闭连接
            if not response is None:
                response.close()

    def do_GET(self):
        self.do_request("GET")

    def do_POST(self):
        self.do_request("POST")

    def do_PUT(self):
        self.do_request("PUT")

    def do_DELETE(self):
        self.do_request("DELETE")

    def do_PATCH(self):
        self.do_request("PATCH")

    def do_HEAD(self):
        self.do_request("HEAD")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='http forwarder')
    parser.add_argument('-c', '--config', default=configFile,
                        help=f'config file default is {configFile}')
    args = parser.parse_args()
    configFile = args.config
    # 初始化配置文件
    with open(configFile) as file:
        config = yaml.safe_load(file)
        if config is None:
            config = {}
        config['server'] = config.get('server', configDefault['server'])
        config['server']['host'] = config['server'].get(
            'host', configDefault['server']['host'])
        config['server']['port'] = config['server'].get(
            'port', configDefault['server']['port'])
        config['proxies'] = config.get('proxies', configDefault['proxies'])
        if type(config['proxies']) == list:
            for i in range(len(config['proxies'])):
                if not 'target' in config['proxies'][i]:
                    print(f"proxies[{i}].target is not defined",
                          file=sys.stderr)
                    exit(1)
                if not 'proxy' in config['proxies'][i]:
                    print(f"proxies[{i}].proxy is not defined",
                          file=sys.stderr)
                    exit(1)
        config['forwarders'] = config.get('forwarders', [])
        for i in range(len(config['forwarders'])):
            if (not 'target' in config['forwarders'][i]) or (not type(config['forwarders'][i]['target']) is str):
                print(f"forwarder[{i}].target is not defined", file=sys.stderr)
                exit(1)
            target = config['forwarders'][i]['target']
            if (not target.startswith('http://')) and (not target.startswith('https://')):
                print(
                    f"forwarder[{i}].target not startswith http:// or https://", file=sys.stderr)
                exit(1)
            elif target.endswith('/'):
                print(
                    f"forwarder[{i}].target can not endswith /", file=sys.stderr)
                exit(1)
            config['forwarders'][i]['description'] = config['forwarders'][i].get(
                'description', f'forward {target}')
            config['forwarders'][i]['host'] = config['forwarders'][i].get(
                'host', configDefault['forwarder']['host'])
            config['forwarders'][i]['headers'] = config['forwarders'][i].get(
                'headers', configDefault['forwarder']['headers'])
    print(config)
    host = config['server']['host']
    port = config['server']['port']
    # 启动服务
    serverAddress = (host, port)
    httpd = http.server.HTTPServer(serverAddress, RequestHandler)
    print(f'Starting HTTP Forward server on {host}:{port}...', flush=True)
    httpd.serve_forever()
