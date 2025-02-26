from typing import Tuple, Callable, List, Optional
import random


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