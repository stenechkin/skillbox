"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login_exists = 0
                new_client_name = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == new_client_name:
                        login_exists = 1
                if login_exists:
                    self.transport.write(
                        f"Логин {new_client_name} занят, попробуйте другой.".encode()
                    )
                    self.transport.close()
                else:
                    self.login = new_client_name
                    self.send_history()
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    # self.send_message(f"Присоединился к чату")
            # else:
            #     self.transport.write(
            #         f"Укажите логин!".encode()
            #     )
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

        self.server.message_history.append(format_string)
        if len(self.server.message_history) > 10:
            self.server.message_history.pop(0)

    def send_history(self):
        for message in self.server.message_history:
            self.transport.write(
                f"{message} \r\n".encode()
            )

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    message_history: list

    def __init__(self):
        self.clients = []
        self.message_history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
