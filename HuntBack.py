import argparse
import socket
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import infoTest
from module import ipwhois_Search
from tqdm import tqdm
from module import domainwhois
import os
import time

def is_port_open(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=1):
            return True
    except (socket.timeout, socket.error):
        return False

def parse_ports(port_input):
    """
    解析用户指定的端口列表，支持单个端口、多个端口、以及端口范围。
    """
    ports = []
    for part in port_input.split(','):
        if '-' in part:
            # 处理端口范围
            start, end = map(int, part.split('-'))
            ports.extend(range(start, end + 1))
        else:
            # 处理单个端口
            ports.append(int(part))
    return ports

def scan_ports(target_ip, port_list, num_threads=10):
    open_ports = []
    
    # 创建进度条，指定总任务数
    with tqdm(total=len(port_list), desc="扫描端口中:", unit="port") as pbar:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(is_port_open, target_ip, port): port for port in port_list}

            for future in concurrent.futures.as_completed(futures):
                port = futures[future]
                try:
                    if future.result():
                        open_ports.append(port)
                except Exception as e:
                    print(f"Error scanning port {port}: {e}")
                # 每完成一个端口扫描，更新进度条
                pbar.update(1)
    
    return open_ports

def main_info(ipInput, porttype, custom_ports=None):
    target_ip = ipInput
    if custom_ports:
        port_list = custom_ports  # 用户指定的端口列表
    elif porttype == "common":
        port_list = [80, 81, 443, 8080, 22, 3389, 4567, 8010, 8099, 5003, 47808, 8888, 3443,60000, 1818, 5000, 6000,88, 9443, 7000, 8081, 5005, 3200, 8001, 8834, 8082, 8083, 8084, 8085, 11000, 8800]  # 常用端口列表
    elif porttype == "all":
        port_list = range(1, 65536)  # 全端口扫描
    
    open_ports = scan_ports(target_ip, port_list)
    results = []  # 存储当前IP地址的结果

    if open_ports:
        for it in open_ports:
            ip_port = f"{target_ip}:{it}"
            print(f"{target_ip}:{it}")
            
            results.extend(infoTest.finger(ip_port))

    return results

def import_file(file_path):
    with open(file_path, 'r') as f:
        ips = f.readlines()
    return [ip.strip() for ip in ips]

def process_ip(ip):
    print(f"处理 IP 地址: {ip}")

def main():
    parser = argparse.ArgumentParser(description="""本程序为蓝队在进行防守过程中，对威胁情报或者安全设备上恶意IP进行溯源的工具
    程序功能：文件导入、循环模式、单IP模式   By:ChinaRan404&知攻善防实验室""")
    
    # 文件导入方式
    parser.add_argument('--file', type=str, help="输入文件路径")
    
    # 循环模式
    parser.add_argument('--cmds', action='store_true', help="启用循环模式，用于常驻终端")
    
    # 单IP模式
    parser.add_argument('--ip', type=str, help="输入单个IP地址进行处理")

    parser.add_argument('--ipwhois', type=str, help="IPwhois查询")

    parser.add_argument('--domainwhois', type=str, help="域名Whois查询")

    # 可选参数，启用全端口扫描
    parser.add_argument('--fullscan', action='store_true', help="【可选参数】启用全端口扫描")
    
    # 新增参数，支持用户指定端口
    parser.add_argument('--ports', type=str, help="【可选参数】指定端口扫描（例如：80,90,8899,1000-2000）")

    args = parser.parse_args()

    custom_ports = None
    if args.ports:
        custom_ports = parse_ports(args.ports)

    all_results = []  # 存储所有IP地址的结果

    if args.file:
        # 文件导入方式
        print(f"从文件 {args.file} 导入 IP 地址列表")
        ips = import_file(args.file)
        for ip in ips:
            porttype = "all" if args.fullscan else "common"
            all_results.extend(main_info(ip, porttype, custom_ports))

    elif args.cmds:
        # 循环模式
        print("启用循环模式，处理多个IP地址")
        while True:
            ip = input("请输入一个 IP 地址 (或输入 'exit' 退出): ")
            if ip.lower() == 'exit':
                break
            porttype = "all" if args.fullscan else "common"
            all_results.extend(main_info(ip, porttype, custom_ports))

    elif args.ip:
        # 单IP模式
        print(f"处理单个 IP 地址: {args.ip}")
        porttype = "all" if args.fullscan else "common"
        all_results.extend(main_info(args.ip, porttype, custom_ports))

    elif args.ipwhois:
        ipwhois_Search.ipwhois(args.ipwhois)
    
    elif args.domainwhois:
        domainwhois.get_whois_info(args.domainwhois)

    else:
        print("请提供有效的参数。使用 -h 查看帮助信息。")

    # 将所有结果写入同一个文件
    if all_results:
        timestamp = int(time.time())
        filename = f"output/{timestamp}.html"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("""
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Results</title>
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        background: linear-gradient(to right, #0f0c29, #302b63, #24243e);
                        color: #fff;
                        padding: 20px;
                        margin: 0;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        border-radius: 10px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                    }
                    th, td {
                        padding: 12px 20px;
                        text-align: left;
                        font-size: 16px;
                        border-bottom: 2px solid #444;
                    }
                    th {
                        background-color: #1e1e2f;
                        color: #ff7f50;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                    tr:nth-child(even) {
                        background-color: #33334d;
                    }
                    tr:nth-child(odd) {
                        background-color: #2a2a3c;
                    }
                    tr:hover {
                        background-color: #444464;
                        transition: 0.3s;
                    }
                    td {
                        color: #b0c4de;
                    }
                    h1 {
                        font-size: 36px;
                        text-align: center;
                        color: #ff7f50;
                        margin-bottom: 40px;
                        text-transform: uppercase;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>HuntBack</h1>
                    <table>
                        <tr>
                            <th>IP</th>
                            <th>Port</th>
                            <th>Type</th>
                            <th>Name</th>
                        </tr>
            """)

            for result in all_results:
                f.write(f"""
                        <tr>
                            <td>{result['ip']}</td>
                            <td>{result['port']}</td>
                            <td>{result['type']}</td>
                            <td>{result['name']}</td>
                        </tr>
                """)

            f.write("""
            </table>
             <div class="footer" style="text-align:center;">
    <p>公众号：知攻善防实验室</p>
    <p><a href="https://github.com/ChinaRan0/HuntBack" target="_blank">HuntBack</a></p>
</div>
        </div>
    </body>
    </html>
    """)


        print(f"输出结果保存至：{filename}")


if __name__ == "__main__":
    main()