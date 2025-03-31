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

            # Получаем приветственное сообщение
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
                    # Проверяем, является ли это сообщением от коровы (многострочное)
                    if message.startswith(' ') or '(' in message[:10]:
                        # Это, вероятно, сообщение от коровы, выводим его напрямую
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
                        # Ждем ответ с таймаутом
                        response = await asyncio.wait_for(self.message_queue.get(), 2.0)
                        return response
                    except asyncio.TimeoutError:
                        print("Превышено время ожидания ответа от сервера")
                        return None
                return None
            except Exception as e:
                print(f"Ошибка при выполнении команды: {e}")
                return None

    def run_async(self, coro):
        """Запустить корутину из синхронного кода"""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            # Ждем результат с небольшим таймаутом
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
            # Справка по конкретной команде
            super().do_help(arg)
        else:
            # Отправляем команду help на сервер
            response = self.run_async(self.execute_command("help"))
            if response:
                print(response)

    def do_quit(self, arg):
        """Отключиться от сервера"""
        # Отправляем команду quit на сервер
        self.run_async(self.execute_command("quit", False))

        print("Выход из чата...")
        self.running = False

        # Закрываем соединение
        if self.writer:
            self.writer.close()

        return True

    # Алиасы
    do_exit = do_quit
    do_bye = do_quit


def run_client(host, port):
    """Запустить клиент коровьего чата"""
    # Создаем клиент
    client = CowClient(host, port)

    # Запускаем асинхронный цикл в отдельном потоке
    def start_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client.loop = loop

        # Подключаемся к серверу
        if not loop.run_until_complete(client.connect()):
            return

        # Запускаем обработчик сообщений
        message_task = loop.create_task(client.message_receiver())

        try:
            # Запускаем цикл событий
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            # Отменяем задачу обработчика сообщений
            message_task.cancel()

            # Закрываем соединение, если оно ещё открыто
            if client.writer and not client.writer.is_closing():
                client.writer.close()
                loop.run_until_complete(client.writer.wait_closed())

            # Останавливаем цикл событий
            loop.close()

    # Запускаем асинхронный цикл в отдельном потоке
    async_thread = threading.Thread(target=start_async_loop, daemon=True)
    async_thread.start()

    try:
        # Даем немного времени, чтобы подключиться к серверу
        import time
        time.sleep(0.5)

        # Запускаем интерактивный режим cmd
        if client.running:
            client.cmdloop()

        # Останавливаем клиент
        client.running = False
    except KeyboardInterrupt:
        print("\nВыход из программы...")
    finally:
        # Ждем завершения потока
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