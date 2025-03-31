import asyncio
import cmd
import sys


class CowClient(cmd.Cmd):
    prompt = '> '
    intro = 'Добро пожаловать в клиент коровьего чата! Используйте help для получения списка команд.\n'

    def __init__(self, host='localhost', port=1337):
        super().__init__()
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.logged_in = False
        self.running = False
        self.cow_name = None

    async def connect(self):
        """Установить соединение с сервером"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.running = True

            # Получаем приветственное сообщение
            welcome = await self.reader.readline()
            print(welcome.decode().strip())

            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    async def send_command(self, command):
        """Отправить команду на сервер и получить ответ"""
        if not self.running or not self.writer:
            print("Не подключен к серверу")
            return None

        try:
            self.writer.write(f"{command}\n".encode())
            await self.writer.drain()

            # Ждем и получаем ответ от сервера
            data = await self.reader.readline()
            return data.decode().strip()
        except Exception as e:
            print(f"Ошибка при отправке команды: {e}")
            return None

    # Синхронные обёртки для команд cmd

    def do_login(self, arg):
        """Зарегистрироваться как корова: login <название_коровы>"""
        asyncio.run(self.send_command(f"login {arg}"))
        return False

    def do_say(self, arg):
        """Послать сообщение пользователю: say <название_коровы> <текст сообщения>"""
        if not arg:
            print("Используйте: say <название_коровы> <текст сообщения>")
            return False
        asyncio.run(self.send_command(f"say {arg}"))
        return False

    def do_yield(self, arg):
        """Послать сообщение всем пользователям: yield <текст сообщения>"""
        if not arg:
            print("Используйте: yield <текст сообщения>")
            return False
        asyncio.run(self.send_command(f"yield {arg}"))
        return False

    def do_who(self, arg):
        """Просмотр зарегистрированных пользователей"""
        asyncio.run(self.send_command("who"))
        return False

    def do_cows(self, arg):
        """Просмотр свободных имён коров"""
        asyncio.run(self.send_command("cows"))
        return False

    def do_help(self, arg):
        """Показать список доступных команд"""
        if arg:
            # Справка по конкретной команде
            super().do_help(arg)
        else:
            # Отправляем команду help на сервер
            asyncio.run(self.send_command("help"))
        return False

    def do_quit(self, arg):
        """Отключиться от сервера"""
        asyncio.run(self.send_command("quit"))
        self.running = False
        if self.writer:
            self.writer.close()
        return True

    # Алиасы
    do_exit = do_quit
    do_bye = do_quit


async def main():
    # Получаем хост и порт из аргументов командной строки
    host = 'localhost'
    port = 1337

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Неверный порт: {sys.argv[2]}")
            return

    # Создаем и подключаем клиент
    client = CowClient(host, port)
    if not await client.connect():
        return

    # Запускаем интерпретатор команд
    client.cmdloop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nВыход...")