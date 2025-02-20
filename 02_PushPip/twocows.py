import argparse
import cowsay

parser = argparse.ArgumentParser(description='Display two cows with messages.')

parser.add_argument('message1', type=str, help='Message for the first cow')
parser.add_argument('message2', type=str, help='Message for the second cow')

parser.add_argument('-e', '--eyes', type=str, default='oo', help='Eyes for the first cow')
parser.add_argument('-t', '--tongue', type=str, default='  ', help='Tongue for the first cow')
parser.add_argument('-f', '--cowfile', type=str, default='default', help='Cowfile for the first cow')

parser.add_argument('-E', type=str, default='oo', help='Eyes for the second cow')
parser.add_argument('-N', type=str, default='  ', help='Tongue for the second cow')
parser.add_argument('-F', type=str, default='default', help='Cowfile for the second cow')

args = parser.parse_args()

cow1 = cowsay.cowsay(message=args.message1, eyes=args.eyes, tongue=args.tongue, cow=args.cowfile)
cow2 = cowsay.cowsay(message=args.message2, eyes=args.E, tongue=args.N, cow=args.F)

cow1_lines = cow1.split('\n')
cow2_lines = cow2.split('\n')

max_height = max(len(cow1_lines), len(cow2_lines))

cow1_padded = [' ' * len(cow1_lines[0])] * (max_height - len(cow1_lines)) + cow1_lines
cow2_padded = [' ' * len(cow2_lines[0])] * (max_height - len(cow2_lines)) + cow2_lines

max_len=max(map(len, cow1_padded))
for line1, line2 in zip(cow1_padded, cow2_padded):
    print(line1 + " "*(max_len-len(line1)) +line2)
