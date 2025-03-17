import asyncio
import cowsay

clients = {}

connections = {}


async def chat(reader, writer):
    addr = "{}:{}".format(*writer.get_extra_info('peername'))
    print(f"Подключен новый клиент: {addr}")

    welcome_message = (
        "Добро пожаловать в коровий чат!\n"
        "Для регистрации введите: login <название_коровы>\n"
        "Для просмотра команд введите: help\n"
    )
    writer.write(welcome_message.encode())
    await writer.drain()

    cow_name = None

    while not reader.at_eof():
        data = await reader.readline()
        if not data:
            break

        message = data.decode().strip()

        if message.startswith("login"):
            parts = message.split(maxsplit=1)
            if len(parts) != 2:
                writer.write("Ошибка: Используйте 'login <название_коровы>'\n".encode())
                await writer.drain()
                continue

            requested_name = parts[1]

            if requested_name not in cowsay.list_cows():
                writer.write(f"Ошибка: Корова '{requested_name}' не существует\n".encode())
                await writer.drain()
                continue

            if requested_name in clients:
                writer.write(f"Ошибка: Имя '{requested_name}' уже занято\n".encode())
                await writer.drain()
                continue

            cow_name = requested_name
            clients[cow_name] = asyncio.Queue()
            connections[cow_name] = (reader, writer)

            writer.write(f"Вы успешно зарегистрировались как '{cow_name}'\n".encode())
            await writer.drain()

        elif message == "help":
            help_message = (
                "Доступные команды:\n"
                "- who — просмотр зарегистрированных пользователей\n"
                "- cows — просмотр свободных имён коров\n"
                "- login <название_коровы> — зарегистрироваться под именем коровы\n"
                "- say <название_коровы> <текст сообщения> — послать сообщение пользователю\n"
                "- yield <текст сообщения> — послать сообщение всем пользователям\n"
                "- quit — отключиться\n"
                "- help — показать это сообщение\n"
            )
            writer.write(help_message.encode())
            await writer.drain()
        elif message == "who":
            if not clients:
                response = "Нет зарегистрированных пользователей\n"
            else:
                response = "Зарегистрированные пользователи:\n"
                for name in clients.keys():
                    response += f"- {name}\n"
            writer.write(response.encode())
            await writer.drain()

        elif message == "cows":
            all_cows = set(cowsay.list_cows())
            used_cows = set(clients.keys())
            free_cows = all_cows - used_cows

            if not free_cows:
                response = "Все коровы заняты\n"
            else:
                response = "Свободные коровы:\n"
                for cow in sorted(free_cows):
                    response += f"- {cow}\n"

            writer.write(response.encode())
            await writer.drain()
        elif message.startswith("say"):
            if not cow_name:
                writer.write("Ошибка: Сначала зарегистрируйтесь с помощью 'login <название_коровы>'\n".encode())
                await writer.drain()
                continue

            parts = message.split(maxsplit=2)
            if len(parts) != 3:
                writer.write("Ошибка: Используйте 'say <название_коровы> <текст сообщения>'\n".encode())
                await writer.drain()
                continue

            target_cow = parts[1]
            msg_text = parts[2]

            if target_cow not in clients:
                writer.write(f"Ошибка: Пользователь '{target_cow}' не найден\n".encode())
                await writer.drain()
                continue

            cow_message = cowsay.cowsay(f"От {cow_name}: {msg_text}", cow=cow_name)
            await clients[target_cow].put(cow_message)

            writer.write(f"Сообщение отправлено пользователю '{target_cow}'\n".encode())
            await writer.drain()

        elif message.startswith("yield"):
            if not cow_name:
                writer.write("Ошибка: Сначала зарегистрируйтесь с помощью 'login <название_коровы>'\n".encode())
                await writer.drain()
                continue

            parts = message.split(maxsplit=1)
            if len(parts) != 2:
                writer.write("Ошибка: Используйте 'yield <текст сообщения>'\n".encode())
                await writer.drain()
                continue

            msg_text = parts[1]
            cow_message = cowsay.cowsay(f"От {cow_name} всем: {msg_text}", cow=cow_name)
            for name, queue in clients.items():
                if name != cow_name:
                    await queue.put(cow_message)
            writer.write("Сообщение отправлено всем пользователям\n".encode())
            await writer.drain()

        elif message == "quit":
            writer.write("До свидания!\n".encode())
            await writer.drain()
            break

        else:
            if not cow_name:
                writer.write("Ошибка: Сначала зарегистрируйтесь с помощью 'login <название_коровы>'\n".encode())
            else:
                writer.write("Ошибка: Неизвестная команда. Введите 'help' для списка команд\n".encode())
            await writer.drain()

    if cow_name and cow_name in clients:
        del clients[cow_name]
        del connections[cow_name]

    print(f"Клиент отключился: {addr}")
    writer.close()
    await writer.wait_closed()


async def message_handler():
    while True:
        for cow_name, (reader, writer) in list(connections.items()):
            try:
                if not clients[cow_name].empty():
                    message = await clients[cow_name].get()
                    writer.write(f"{message}\n".encode())
                    await writer.drain()
            except Exception as e:
                print(f"Ошибка при отправке сообщения для {cow_name}: {e}")

        await asyncio.sleep(0.1)


async def main():
    server = await asyncio.start_server(chat, '0.0.0.0', 1337)

    message_task = asyncio.create_task(message_handler())

    addr = server.sockets[0].getsockname()
    print(f"Сервер запущен на {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Сервер остановлен")
