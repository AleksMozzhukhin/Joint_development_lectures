import cmd
import shlex
import cowsay


class CowsayCmd(cmd.Cmd):
    prompt = "twocows> "


    def do_cowsay(self, arg):
        """
        cowsay <сообщение> [<название_коровы> [параметр=значение ...]] [reply <сообщение_ответа> [<название_коровы> [параметр=значение ...]]]

        Выводит ASCII‑арт, имитирующий речь коровы.
        Пример: cowsay "Hi there" moose eyes="^^" reply "Ahoy!" sheep
        Допустимые параметры: eyes и tongue.
        """
        self._handle_cow_command(arg, func=cowsay.cowsay)

    def do_cowthink(self, arg):
        """
        cowthink <сообщение> [<название_коровы> [параметр=значение ...]] [reply <сообщение_ответа> [<название_коровы> [параметр=значение ...]]]

        Выводит ASCII‑арт, имитирующий размышления коровы.
        Пример использования аналогичен команде cowsay.
        Допустимые параметры: eyes и tongue.
        """
        self._handle_cow_command(arg, func=cowsay.cowthink)

    def _handle_cow_command(self, arg, func):
        try:
            tokens = shlex.split(arg)
        except ValueError as e:
            print("Ошибка разбора командной строки:", e)
            return

        if not tokens:
            print("Ошибка: отсутствует сообщение. Использование:")
            print(
                "  <команда> <сообщение> [<название_коровы> [параметр=значение ...]] [reply <сообщение_ответа> [<название_коровы> [параметр=значение ...]]]")
            return

        if "reply" in tokens:
            index_reply = tokens.index("reply")
            group1_tokens = tokens[:index_reply]
            group2_tokens = tokens[index_reply + 1:]
            try:
                group1 = self._parse_cow_group(group1_tokens)
                group2 = self._parse_cow_group(group2_tokens)
            except ValueError as e:
                print("Ошибка:", e)
                return

            art1 = func(
                message=group1["message"],
                cow=group1["cow"],
                eyes=group1["eyes"],
                tongue=group1["tongue"]
            )
            art2 = func(
                message=group2["message"],
                cow=group2["cow"],
                eyes=group2["eyes"],
                tongue=group2["tongue"]
            )
            self._print_side_by_side(art1, art2)
        else:
            try:
                group = self._parse_cow_group(tokens)
            except ValueError as e:
                print("Ошибка:", e)
                return
            art = func(
                message=group["message"],
                cow=group["cow"],
                eyes=group["eyes"],
                tongue=group["tongue"]
            )
            print(art)

    def _parse_cow_group(self, tokens):
        if not tokens:
            raise ValueError("Отсутствует сообщение для коровы.")
        result = {
            "message": tokens[0],
            "cow": "default",
            "eyes": "oo",
            "tongue": "  "
        }
        i = 1
        if i < len(tokens) and "=" not in tokens[i]:
            result["cow"] = tokens[i]
            i += 1
        while i < len(tokens):
            token = tokens[i]
            if "=" in token:
                key, value = token.split("=", 1)
                if key in ("eyes", "tongue"):
                    result[key] = value
                else:
                    print(f"Предупреждение: неизвестный параметр '{key}' будет проигнорирован.")
            else:
                print(f"Предупреждение: токен '{token}' не распознан и будет проигнорирован.")
            i += 1
        return result

    def _print_side_by_side(self, art1, art2):
        cow1_lines = art1.split('\n')
        cow2_lines = art2.split('\n')

        max_height = max(len(cow1_lines), len(cow2_lines))

        cow1_padded = [' ' * len(cow1_lines[0])] * (max_height - len(cow1_lines)) + cow1_lines
        cow2_padded = [' ' * len(cow2_lines[0])] * (max_height - len(cow2_lines)) + cow2_lines

        max_len = max(map(len, cow1_padded))
        for line1, line2 in zip(cow1_padded, cow2_padded):
            print(line1 + " " * (max_len - len(line1)) + line2)


CowsayCmd().cmdloop()
