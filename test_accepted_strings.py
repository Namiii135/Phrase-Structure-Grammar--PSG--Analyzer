#!/usr/bin/env python3
import sys
sys.path.insert(0, r'd:\Discrete math assigment')

from grammar_classifier import generate_accepted_strings, parse_productions

# Test case: S -> AB, A -> a, B -> b
productions = parse_productions("S->AB, A->a, B->b")
non_terminals = {'S', 'A', 'B'}

print("Testing: S->AB, A->a, B->b")
print("Start: S")
print("Non-terminals: ", non_terminals)
print("Productions: ", productions)

accepted = generate_accepted_strings('S', productions, non_terminals, max_depth=8)
print("\nAccepted strings:")
for s in accepted:
    print(f'  "{s if s else "ε"}"')

print("\n" + "="*50 + "\n")

# Test case 2: S -> aS | b (should accept: b, ab, aab, aaab, ...)
productions2 = parse_productions("S->aS, S->b")
non_terminals2 = {'S'}

print("Testing: S->aS | b")
print("Start: S")
print("Non-terminals: ", non_terminals2)
print("Productions: ", productions2)

accepted2 = generate_accepted_strings('S', productions2, non_terminals2, max_depth=6)
print("\nAccepted strings:")
for s in accepted2:
    print(f'  "{s if s else "ε"}"')
