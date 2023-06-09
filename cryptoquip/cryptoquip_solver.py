import json
import re
import string
import random
import time
import re
from queue import PriorityQueue
import sys

# local imports
from puzzle_generator import generate_cryptoquip_dict
from line_profiler import LineProfiler
from collections import defaultdict

profiler = LineProfiler()


def profile(func):
    def inner(*args, **kwargs):
        profiler.add_function(func)
        profiler.enable_by_count()
        return func(*args, **kwargs)

    return inner


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
words_by_length[1] = [w for w in short_words if len(w) == 1]
words_by_length[2] = [w for w in short_words if len(w) == 2]

words = set(words)
words_by_position = {}
t = time.time()
for length in words_by_length.keys():
    if len(words_by_length[length]) != 0:
        sub_words = words_by_length[length]
        words_by_position[length] = {}
        sub_dict = words_by_position[length]
        for i in range(len(sub_words[0])):
            sub_dict[i] = {}
        for word in sub_words:
            for i in range(length):
                if word[i].upper() not in sub_dict[i].keys():
                    sub_dict[i][word[i].upper()] = {word}
                else:
                    sub_dict[i][word[i].upper()].add(word)

# to get all words matching _T__, you would call
# super_word_map[length][position][letter]
# super_word_map[4][1]["T"]
super_word_map = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for length in range(len(words_by_length)):
    for word in words_by_length[length]:
        for p in range(len(word)):
            letter = word[p].upper()
            super_word_map[length][p][letter].append(word)
filename = "raw_puzzles.txt"
if len(sys.argv) > 1:
    filename = sys.argv[1]
    puzzles_dict = generate_cryptoquip_dict(filename, seed=10)


# remove special characters
# puzzle = re.sub(r"[^A-Za-a ]", " ", open(filename).read()).strip()
# puzzle = [p.strip() for p in puzzle.split(" ") if p.strip() != ""]
puzzle = puzzles_dict["encrypted_puzzles"][0]
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

WAIT_BETWEEN_STEPS = False
FIND_ALL_SOLUTIONS = False
PRINT_ALL_STEPS = False
PRINT_EVERY_ONE_IN = 1000


# priority queue with format (priority , str(letter mapping))
mapping_priority_queue = PriorityQueue()
mapping_priority_queue.put((0, json.dumps(letter_mapping)))

print("pre-processing cost: {}".format(time.time() - t))

# start the timer
st = time.time()


# pull a mapping from the priority queue
@profile
def solve():
    global mapping_priority_queue
    val = mapping_priority_queue.get()
    score = val[0]
    mapping = json.loads(val[1])

    # every now and then, print the current attempt
    if PRINT_ALL_STEPS or random.randint(0, PRINT_EVERY_ONE_IN) == 1:
        print(score, mapping)
        print(solution_string(mapping))

    if WAIT_BETWEEN_STEPS:
        input()

    best_word = get_best_word(mapping)

    if best_word is None:
        print(time.time() - st)
        print(solution_string(mapping))
        valid_solutions.add(solution_string(mapping))

        if not FIND_ALL_SOLUTIONS:
            mapping_priority_queue = PriorityQueue()
        return

    # get all the possible words that the "best word" could be (given the mapping)

    # valid_words = get_valid_words(best_word, mapping)
    valid_words = get_valid_words_no_regex(best_word, mapping)

    for chosen_word in valid_words:  # choose a word, generate a next mapping from it
        new_mapping = mapping.copy()

        for i in range(len(chosen_word)):
            new_mapping[best_word[i]] = chosen_word[i].upper()

        # check if the mapping gives a valid word, and doesn't make the puzzle gibberish
        if check_word(new_mapping, best_word) and is_puzzle_valid(new_mapping):
            mapping_priority_queue.put(
                (
                    calc_score(new_mapping),
                    json.dumps(new_mapping),
                )
            )  # calc the score and put it in the queue

    return


# for a cipher word and mapping, return all english words that could match that (ordered by frequency)
def get_valid_words(cipher_word, mapping):
    chosen_values = set(mapping.values())

    word_pattern = ""
    known_letter = None
    known_position = -1
    for i in range(len(cipher_word)):
        l = cipher_word[i]
        if l in mapping:
            word_pattern += mapping[l]
            known_letter = mapping[l]
            known_position = i
        else:
            if len(chosen_values) == 0:
                word_pattern = "."
            else:
                word_pattern += "[^%s]" % "".join(chosen_values)
    word_pattern += ""

    if known_letter == None:
        possible_words = words_by_length[len(cipher_word)]

    else:
        possible_words = super_word_map[len(cipher_word)][known_position][known_letter]

    pat = re.compile(word_pattern.lower())
    same_length_words = possible_words
    valid_words = [w for w in same_length_words if pat.match(w)]

    return valid_words


def get_valid_words_no_regex(cipher_word, mapping):
    chosen_values = set(mapping.values())

    set_list = []
    length = len(cipher_word)
    for pos in range(length):
        l = cipher_word[pos]
        if l in mapping:
            set_list.append(words_by_position[length][pos][mapping[l]])

    if set_list == []:
        return words_by_length[length]
    else:
        total_set = set_list[0]
        for subset in set_list:
            total_set = subset & total_set
        return total_set


# calculate a priority score for a new letter mapping
def calc_score(mapping):
    score = 0
    num = 0
    for cipher_word in puzzle:
        if all([l in mapping for l in cipher_word]):
            plain_word = get_plain_word(cipher_word, mapping)

            score += 1 / frequencies[plain_word.lower()] * 1000
            num += 1

    return score * (2**-num)
    return -num + score


# check all completed words from a mapping for validity
def is_puzzle_valid(mapping):
    if len(mapping.keys()) != len(set(mapping.values())):
        return False

    for cipher_word in puzzle:
        if all([l in mapping for l in cipher_word]):
            if check_word(mapping, cipher_word) == False:
                return False
    return True


# convert a cipher word to a plain word using a letter mapping
def get_plain_word(cipher_word, mapping):
    newWord = ""
    for l in cipher_word:
        newWord += mapping[l]
    return newWord


# check that a mapping will map a cipher word to an english word
def check_word(mapping, cipher_word: string):
    plain_word = get_plain_word(cipher_word, mapping)

    if len(set([l for l in cipher_word])) != len(set([l for l in plain_word])):
        return False

    if len(cipher_word) <= 2:
        return plain_word.lower() in short_words

    return plain_word.lower() in words


# print the current solution, excluding incomplete words
def solution_string(mapping):
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


# find the word with the fewest letters in already in the mapping, to reduce possible words it could be
def get_best_word(mapping):
    lowest_num_unchosen = 10000
    best_word = None

    for word in puzzle:
        unchosen = 0
        for l in word:
            if not l in mapping:
                unchosen += 1

        if unchosen < lowest_num_unchosen and unchosen != 0:
            lowest_num_unchosen = unchosen
            best_word = word

    return best_word


# solve it lol
while not mapping_priority_queue.empty():
    solve()

for sol in valid_solutions:
    print(sol)

print("Number of solutions found: ", len(valid_solutions))
print("Finished in ", time.time() - st, "seconds")
