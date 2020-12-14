# Ulexite

Ulexite is a Gemini Feed reader (LINK TO SPEC) written in Python 3. It is designed to have full and optimal support for all gemini feeds / gemlogs in the wild, and to be as simple as possible to deploy and run.

## Usage


```
usage: python3 main.py [-h] [--feeds FEEDS] [--output OUTPUT] [--header HEADER] [--footer FOOTER]

Generate gemini feed

optional arguments:
  -h, --help       show this help message and exit
  --feeds FEEDS    The path of the feed list. Should be a plain text file with a list of feed URLS. If "-" is passed, or no value is passed, uses stdin.
  --output OUTPUT  The path of the output file. If "-" is passed, or no value is passed, uses stdout.
  --header HEADER  The file path of the header (file prepended to the feed list)
  --footer FOOTER  The file path of the footer (file appended to the feed list)
 ```
