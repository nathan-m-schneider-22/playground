import json
import re
import string
import random
import time
import re
from queue import PriorityQueue
import sys


mappings = PriorityQueue()

letters = [l for l in string.ascii_uppercase]

short_words = set(open("short_words.txt").read().split("\n"))

frq = open("unigram_freq.csv").read().split("\n")
frq = [line.split(",") for line in frq]
frequencies = {}
for i in range(len(frq)):
    frequencies[frq[i][0]] = int(frq[i][1])

words = open("ordered_words.txt").read().split("\n")

words_by_length = {
    i: [w for w in words if len(w) == i] for i in range(len(max(words, key=len)))
}

words = set(words)


filename = "puzzle.txt"
if len(sys.argv) > 1:
    filename = sys.argv[1]

# remove special characters
puzzle = re.sub(r"[^A-Za-a ]", " ", open(filename).read()).strip()
puzzle = [p.strip() for p in puzzle.split(" ") if p.strip() != ""]
print(puzzle)


letter_mapping = {}

# trying with sample chosen mappings
# chosen = {"E": "A", "G": "O", "K": "F"}
# chosen = {"J": "T", "N": "H", "Z": "E", "E": "A", "G": "O", "K": "F"}
# cipher = "abcdefghijklmnopqrstuvwxyz".upper()
# clears = "pnxzakodltfrwhjiysuvqmcbge".upper()
# for i in range(len(cipher)-20):
#     letter_mapping[cipher[i]] = clears[i]

valid_solutions = set()

FIND_ALL_SOLUTIONS = True
PRINT_ALL_STEPS = False
SLOW_STEPS = False


mappings.put((0, json.dumps(letter_mapping)))

st = time.time()


def solve():
    global mappings
    val = mappings.get()
    score = val[0]
    mapping = json.loads(val[1])

    if PRINT_ALL_STEPS or random.randint(0, 1000) == 1:
        print(score, mapping)
        print_solved(mapping)

    if SLOW_STEPS:
        input()

    shortest_word, chosen_letter, unchosen_letters_left = get_shortest(mapping)
    chosen_values = set(mapping.values())

    if shortest_word is None:
        print(time.time() - st)
        print_solved(mapping)
        valid_solutions.add(solution(mapping))

        if not FIND_ALL_SOLUTIONS:
            mappings = PriorityQueue()

        return

    shortest_pattern = ""
    for l in shortest_word:
        if l in mapping:
            shortest_pattern += mapping[l]
        else:
            if len(chosen_values) == 0:
                shortest_pattern = "."
            else:
                shortest_pattern += "[^%s]" % "".join(chosen_values)

    shortest_pattern += ""

    pat = re.compile(shortest_pattern.lower())

    valid_words = [w for w in words_by_length[len(shortest_word)] if pat.match(w)]

    for chosen_word in valid_words:
        new_mapping = mapping.copy()

        for i in range(len(chosen_word)):
            new_mapping[shortest_word[i]] = chosen_word[i].upper()

        if not check_word(new_mapping, shortest_word) or not check_puzzle(new_mapping):
            return

        mappings.put((getscore(new_mapping), json.dumps(new_mapping)))

    return


def getscore(mapping):
    score = 0
    num = 0
    for word in puzzle:
        if all([l in mapping for l in word]):
            newWord = ""
            for l in word:
                newWord += mapping[l]
            score += 1 / frequencies[newWord.lower()] * 1000
            num += 1

    return -num + score


def check_puzzle(mapping):
    for word in puzzle:
        if all([l in mapping for l in word]):
            if check_word(mapping, word) == False:
                return False
    return True


def check_word(mapping, word: string):
    newWord = ""
    for l in word:
        newWord += mapping[l]

    d = newWord.lower() in short_words
    if len(word) <= 2:
        return newWord.lower() in short_words

    return newWord.lower() in words


def solution(mapping):
    solved = ""

    for word in puzzle:
        w = ""
        for l in word:
            if l in mapping:
                w += mapping[l]
            else:
                w += "_"
                w = " " * len(word)
                break

        solved += w + " "
    return solved


def print_solved(mapping):
    print(solution(mapping))


def get_shortest(mapping):
    lowest_num_unchosen = 10000
    shortest_word = None
    first_unchosen_letter = ""
    left_unchosen = 10000

    for word in puzzle:
        unchosen = 0
        unchosen_letter = ""
        for l in word:
            if not l in mapping:
                unchosen += 1
                if unchosen_letter == "":
                    unchosen_letter = l

        if unchosen < lowest_num_unchosen and unchosen != 0:
            lowest_num_unchosen = unchosen
            shortest_word = word
            left_unchosen = unchosen
            first_unchosen_letter = unchosen_letter

    return shortest_word, first_unchosen_letter, left_unchosen


while not mappings.empty():
    solve()

if len(valid_solutions) > 0:
    for sol in valid_solutions:
        print(sol)

print("Number of solutions found: ", len(valid_solutions))
print("Finished in ", time.time() - st, "seconds")
