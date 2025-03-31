import asyncio
import cmd
import sys
import threading


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

        # Кэш для списков коров и пользователей
        self.available_cows = []
        self.registered_users = []

        # Блокировки для предотвращения конфликтов чтения/записи
        self.command_lock = None

        # Очередь для входящих сообщений
        self.message_queue = None

        # Эвент-луп для асинхронных операций
        self.loop = None

    async def connect(self):
        """Установить соединение с сервером"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.running = True

            # Инициализируем блокировку и очередь
            self.command_lock = asyncio.Lock()
            self.message_queue = asyncio.Queue()

            welcome = await self.reader.readline()
            print(welcome.decode().strip())

            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    async def message_receiver(self):
        """Асинхронный обработчик входящих сообщений"""
        while self.running:
            try:
                data = await self.reader.readline()
                if not data:
                    print("\nСоединение с сервером потеряно")
                    self.running = False
                    break

                message = data.decode().strip()
                if message:
                    if message.startswith(' ') or '(' in message[:10]:
                        print(f"\n{message}")
                        print(self.prompt, end='', flush=True)
                    else:
                        # Добавляем сообщение в очередь для обработки командами
                        await self.message_queue.put(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"\nОшибка при получении сообщения: {e}")
                break

    async def execute_command(self, command, wait_response=True):
        """Отправить команду на сервер и опционально получить ответ"""
        if not self.running or not self.writer:
            print("Не подключен к серверу")
            return None

        async with self.command_lock:
            try:
                self.writer.write(f"{command}\n".encode())
                await self.writer.drain()

                if wait_response:
                    try:
                        response = await asyncio.wait_for(self.message_queue.get(), 2.0)
                        return response
                    except asyncio.TimeoutError:
                        print("Превышено время ожидания ответа от сервера")
                        return None
                return None
            except Exception as e:
                print(f"Ошибка при выполнении команды: {e}")
                return None

    async def get_cows_list(self):
        """Получить список доступных коров с сервера"""
        response = await self.execute_command("cows")
        self.available_cows = []

        if response:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('- '):
                    self.available_cows.append(line[2:])

        return self.available_cows

    async def get_users_list(self):
        """Получить список зарегистрированных пользователей с сервера"""
        response = await self.execute_command("who")
        self.registered_users = []

        if response:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('- '):
                    self.registered_users.append(line[2:])

        return self.registered_users

    def run_async(self, coro):
        """Запустить корутину из синхронного кода"""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=3.0)
        except asyncio.TimeoutError:
            print("Операция заняла слишком много времени")
            return None
        except Exception as e:
            print(f"Ошибка при выполнении асинхронной задачи: {e}")
            return None

    # Команды cmd

    def do_login(self, arg):
        """Зарегистрироваться как корова: login <название_коровы>"""
        if not arg:
            print("Используйте: login <название_коровы>")
            return

        response = self.run_async(self.execute_command(f"login {arg}"))
        if response and 'успешно зарегистрировались' in response:
            self.logged_in = True
            self.cow_name = arg

        if response:
            print(response)

    def complete_login(self, text, line, begidx, endidx):
        """Автодополнение для команды login"""
        cows = self.run_async(self.get_cows_list())

        if not cows:
            return []

        if not text:
            return cows
        else:
            return [cow for cow in cows if cow.startswith(text)]

    def do_say(self, arg):
        """Послать сообщение пользователю: say <название_коровы> <текст сообщения>"""
        if not self.logged_in:
            print("Сначала зарегистрируйтесь с помощью 'login <название_коровы>'")
            return

        parts = arg.split(maxsplit=1)
        if len(parts) != 2:
            print("Используйте: say <название_коровы> <текст сообщения>")
            return

        response = self.run_async(self.execute_command(f"say {arg}"))
        if response:
            print(response)

    def complete_say(self, text, line, begidx, endidx):
        """Автодополнение для команды say"""
        parts = line.split()

        # Если вводится имя пользователя (части: "say" и возможно часть имени)
        if len(parts) <= 2:
            users = self.run_async(self.get_users_list())

            if not users:
                return []

            if not text:
                return users
            else:
                return [user for user in users if user.startswith(text)]
        return []

    def do_yield(self, arg):
        """Послать сообщение всем пользователям: yield <текст сообщения>"""
        if not self.logged_in:
            print("Сначала зарегистрируйтесь с помощью 'login <название_коровы>'")
            return

        if not arg:
            print("Используйте: yield <текст сообщения>")
            return

        response = self.run_async(self.execute_command(f"yield {arg}"))
        if response:
            print(response)

    def do_who(self, arg):
        """Просмотр зарегистрированных пользователей"""
        response = self.run_async(self.execute_command("who"))
        if response:
            print(response)

    def do_cows(self, arg):
        """Просмотр свободных имён коров"""
        response = self.run_async(self.execute_command("cows"))
        if response:
            print(response)

    def do_help(self, arg):
        """Показать список доступных команд"""
        if arg:
            super().do_help(arg)
        else:
            response = self.run_async(self.execute_command("help"))
            if response:
                print(response)

    def do_quit(self, arg):
        """Отключиться от сервера"""
        self.run_async(self.execute_command("quit", False))

        print("Выход из чата...")
        self.running = False

        if self.writer:
            self.writer.close()

        return True

    do_exit = do_quit
    do_bye = do_quit


def run_client(host, port):
    """Запустить клиент коровьего чата"""
    client = CowClient(host, port)

    def start_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client.loop = loop

        if not loop.run_until_complete(client.connect()):
            return

        message_task = loop.create_task(client.message_receiver())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            message_task.cancel()

            if client.writer and not client.writer.is_closing():
                client.writer.close()
                loop.run_until_complete(client.writer.wait_closed())

            loop.close()

    async_thread = threading.Thread(target=start_async_loop, daemon=True)
    async_thread.start()

    try:
        import time
        time.sleep(0.5)

        if client.running:
            client.cmdloop()

        client.running = False
    except KeyboardInterrupt:
        print("\nВыход из программы...")
    finally:
        if client.loop and client.loop.is_running():
            client.loop.call_soon_threadsafe(client.loop.stop)
        async_thread.join(timeout=1.0)


if __name__ == "__main__":
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
            sys.exit(1)

    try:
        run_client(host, port)
    except KeyboardInterrupt:
        print("\nВыход из программы...")