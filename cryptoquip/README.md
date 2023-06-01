# Cryptoquip solver
Cryptoquip is another simple word game, popular in newspapers. In it players must crack a simple [mono-alphabetic substitution cipher](https://en.wikipedia.org/wiki/Substitution_cipher) to decipher a secret phrase. For example:

`"MNEJ WGSIH RGVZGBZ WEII JNZ AIEWZ GK JNZ GELRVEB RPJSEJZH WIGRZRJ JG JNZ NZEH GK E RNPA? JNZ KLGBJ-LGM RZEJ."`

Would translate to:

`"WHAT COULD SOMEONE CALL THE PLACE OF THE OARSMAN SITUATED CLOSEST TO THE HEAD OF A SHIP? THE FRONT-ROW SEAT."`

## Approach
I don't have any experience with cracking substitution ciphers, and I didn't want to be influenced with real-world approaches, so I tried going into this blind. 

The solution to the puzzle is some letter mapping `{M:W, N:H, E:A ...}`, so I decided to search a bunch of different letter mappings until it gets to the answer. 

The algorithm starts with an empty letter mapping, and chooses the word with the fewest unknown letters. In the example above, `"E"`. It then considers each possible word (I or a), and adds the resulting letter mappings `{E:I}` and `{E:A}` to a priority queue, with a priority weighted between word frequency and number of solved words. 

It then draws from the priority queue and repeats this process, trying to solve `"GK"`. It then takes all possible words, builds the resultant letter maps eg: `{E:I, G:A, K:N}...` and adds them to the priority queue. It does this until it finds a solution, which will be made from the most common english words possible.  


## Improvements
To reduce the time in querying all valid words for a cipher word and letter mapping, we created a dictionary data structure indexed by length and positioning for each letter. While it took much more memory than the dictionary array, it significantly reduced the runtime of this approach. 


## Credit
After I wrote the initial algorithm, I collaborated with [Thomas Clark](https://www.linkedin.com/in/wesley-thomas-clark/) on improving it, and testing across multiple puzzles. 