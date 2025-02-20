import argparse

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
print(args)