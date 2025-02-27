from typing import Tuple, Callable, List, Optional
import random
import urllib.request
import sys
import cowsay


def bullscows(guess: str, secret: str) -> Tuple[int, int]:
    bulls = sum(g == s for g, s in zip(guess, secret))

    guess_chars = {}
    secret_chars = {}

    for char in guess:
        guess_chars[char] = guess_chars.get(char, 0) + 1

    for char in secret:
        secret_chars[char] = secret_chars.get(char, 0) + 1

    common_chars = sum(min(guess_chars.get(char, 0), secret_chars.get(char, 0))
                       for char in set(guess_chars) | set(secret_chars))

    cows = common_chars - bulls

    return bulls, cows


def gameplay(ask: Callable[[str, Optional[List[str]]], str],
             inform: Callable[[str, int, int], None],
             words: List[str]) -> int:
    secret_word = random.choice(words)
    attempts = 0

    while True:
        guess = ask("Введите слово: ", words)
        attempts += 1

        bulls, cows = bullscows(guess, secret_word)
        inform("Быки: {}, Коровы: {}", bulls, cows)

        if bulls == len(secret_word):
            return attempts


def read_dictionary(source: str) -> List[str]:
    if source.startswith(('http://', 'https://')):
        with urllib.request.urlopen(source) as response:
            content = response.read().decode('utf-8')
    else:
        with open(source, 'r', encoding='utf-8') as file:
            content = file.read()

    return [word.strip() for word in content.split() if word.strip()]


def main():
    if len(sys.argv) < 2:
        print("Использование: python -m bullscows словарь [длина]")
        return

    dictionary_source = sys.argv[1]
    word_length = 5

    if len(sys.argv) > 2:
        try:
            word_length = int(sys.argv[2])
        except ValueError:
            print("Ошибка: длина должна быть целым числом")
            return

    all_words = read_dictionary(dictionary_source)
    words_of_length = [word for word in all_words if len(word) == word_length]

    if not words_of_length:
        print(f"Ошибка: в словаре нет слов длины {word_length}")
        return

    def ask_func(prompt: str, valid: List[str] = None) -> str:
        while True:
            user_input = input(cowsay.cowsay(message=prompt, cow=random.choice(cowsay.list_cows())))
            if valid is None or not valid:
                return user_input
            if user_input in valid:
                return user_input
            print(cowsay.cowsay(message="Такого слова нет в списке. Попробуйте еще раз.",
                                cow=random.choice(cowsay.list_cows())))
            print("##########: ")

    def inform_func(format_string: str, bulls: int, cows: int) -> None:
        print(cowsay.cowsay(message=format_string.format(bulls, cows), cow=random.choice(cowsay.list_cows())))
        print('###########:  ')

    attempts = gameplay(ask_func, inform_func, words_of_length)
    print(f"Поздравляем! Вы угадали слово за {attempts} попыток.")


if __name__ == "__main__":
    main()
