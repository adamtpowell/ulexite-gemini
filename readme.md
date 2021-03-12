# Ulexite

Ulexite is a feed reader for the gemini:// protocol, supporting gemfeed (list of links with ISO dates), and atom feeds, with support for more on the way. It's usable in its current state, but there are probably better options.

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
