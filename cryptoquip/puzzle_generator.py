import random
import string
def parse_input_from_file(filename):
    unencrypted_puzzles = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            unencrypted_puzzles.append(line.strip().upper())
    if unencrypted_puzzles == []:
        raise ValueError("No puzzles found in file")
    return unencrypted_puzzles

def generate_random_solution(seed = None):
    if seed != None:
        random.seed(seed)
    alphabet = list(string.ascii_uppercase)
    random.shuffle(alphabet)
    return dict(zip(string.ascii_uppercase, alphabet))

def encrypt_puzzles(return_dict):
    return_dict['encrypted_puzzles'] = []
    for puzzle in return_dict["unencrypted_puzzles"]:
        curr_puzzle = []
        for word in puzzle.split(' '):
            encrypted_word = ''
            for char in word: 
                if char.isalpha():
                    encrypted_word+= return_dict['solution'][char]
            curr_puzzle.append(encrypted_word)
        return_dict['encrypted_puzzles'].append(curr_puzzle)

def generate_cryptoquip_dict(filename = 'raw_puzzles.txt',seed = None):
    return_dict = {}
    # ingest input from input file
    return_dict["unencrypted_puzzles"] = parse_input_from_file(filename)
    # generate a solution mapping, optional seed for repeatability
    return_dict["solution"] = generate_random_solution(seed)
    # use the mapping to convert the solutions into cryptographs
    encrypt_puzzles(return_dict)
    return return_dict



if __name__ == '__main__':
    generate_cryptoquip_dict()