import socket
import asyncio
import urllib.parse
async def handle_client(client_socket):
    loop=asyncio.get_running_loop()
    try:

        request_data = await loop.sock_recv(client_socket,1024)
        if not request_data:
            client_socket.close()
            return
        request_lines = request_data.decode().split("\r\n")
        method, url, protocol = request_lines[0].split()
        
        if method.upper()=="CONNECT":
            host,port=url.split(":")
            port=int(port)
            remote=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            remote.setblocking(False)
            await loop.sock_connect(remote,(host,port))

            await loop.sock_sendall(client_socket,b"HTTP/1.1 200 Connection Established\r\n\r\n")

            async def forward(reader,writer):
                while True:
                        data=await loop.sock_recv(reader,4096)
                        if not data:
                            break
                        await loop.sock_sendall(writer,data)
            await asyncio.gather(
                forward(client_socket,remote),
                forward(remote,client_socket)
            )
            client_socket.close()
            remote.close()
        else:
            url_parts = urllib.parse.urlparse(url)
            hostname = url_parts.netloc
            
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.setblocking(False)

            await loop.sock_connect(remote,(hostname, 80))
            await loop.sock_sendall(remote,request_data)
            while True:
                response_data = await loop.sock_recv(remote,4096)
                if response_data:
                    await loop.sock_sendall(client_socket,response_data)
                else:
                    break
            client_socket.close()
            remote.close()
    except Exception as e:
        print(f"[ERROR] {e}")
        client_socket.close()
async def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(False)
    server_address = ("127.0.0.1", 8888)
    server_socket.bind(server_address)
    server_socket.listen(100)
    print("代理服务器已启动，监听地址：%s:%d" % server_address)

    loop=asyncio.get_running_loop()
    while True:
        client_socket=(await loop.sock_accept(server_socket))[0]
        asyncio.create_task(handle_client(client_socket))
if __name__ == "__main__":
    asyncio.run(main())
