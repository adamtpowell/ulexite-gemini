from collections import defaultdict
from typing import List, Tuple, NamedTuple, DefaultDict, Dict
import gemini
import sys
import re
import argparse
from multiprocessing import Pool

FeedEntry = NamedTuple("FeedEntry", [
    ('feed_title', str),
    ('link', gemini.GemtextLink),
    ('date', str),
])

def read_feed(page: gemini.Page, title: str) -> List[FeedEntry]:
    entries: List[FeedEntry] = []

    feed_title = page.title if title is None else title

    date_regex = re.compile("([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*(.*)?")

    for link in page.links:
        date_match = date_regex.match(link.label)
        if date_match is None:
            continue

        date, new_label = date_match.groups()

        if date is None:
            continue

        entries.append(FeedEntry(
            feed_title, 
            gemini.GemtextLink(
                link.url,
                new_label
            ),
            date
        ))

    return entries

def get_feed_list(updates_by_date: Dict[str, List[FeedEntry]]) -> str:

    updates = ""
    for date in sorted(updates_by_date.keys(), reverse=True):
        for entry in updates_by_date[date]:
            updates += "=> {} {} {} | {}".format(entry.link.url, date, entry.feed_title, entry.link.label)
            updates += "\n"
        updates += "\n"
    
    return updates

def page_with_title_from_url(feed_link: gemini.GemtextLink):
    try:
        return (gemini.fetch_page(feed_link.url), feed_link.label)
    except Exception as e:
        print("Failure fetching feed at", str(feed_link.url), ":", e, file=sys.stderr)
        return None

def write_feed(input_file, output_file, header_file, footer_file):
    feed_updates: DefaultDict[str, List[FeedEntry]] = defaultdict(list)

    links_to_feeds = [gemini.GemtextLink.from_str(line) for line in input_file.readlines()]

    with Pool(processes = 16) as pool:
        pages = pool.map(page_with_title_from_url, links_to_feeds)

    for page_with_title in pages:
        if page_with_title is None: continue # Ignore pages which failed to parse
        page, title = page_with_title
        entries = read_feed(page, title)
        for feed_entry in entries:
            feed_updates[feed_entry.date].append(feed_entry)

    header_value = "" if header_file == None else "".join(header_file.readlines())
    footer_value = "" if footer_file == None else "".join(footer_file.readlines())

    output_file.write(header_value)
    output_file.write(get_feed_list(feed_updates))
    output_file.write(footer_value)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read gemini feeds and generate gemtext from them.')
    parser.add_argument('--feeds',
                    help='The path of the feed list. Should be a gemtext file with only link lines. The label is optional and is used for the feed title. If "-" is passed, or no value is passed, uses stdin.')
    parser.add_argument('--output',
                    help='The path of the output file. If "-" is passed, or no value is passed, uses stdout.')
    parser.add_argument('--header', default=None,
                    help='The file path of the header (file prepended to the feed list)')
    parser.add_argument('--footer', default=None,
                    help='The file path of the footer (file appended to the feed list)')

    args = parser.parse_args()

    input_file = sys.stdin
    output_file = sys.stdout
    header_file = None
    footer_file = None

    if not args.feeds is None and not args.feeds == "-":
        try: 
            input_file = open(args.feeds) 
        except: 
            print("Failed to open feeds file {}. Make sure the file exists.".format(args.feeds), file=sys.stderr)
            exit()

    if not args.output is None and not args.output == "-":
        try:
            output_file = open(args.output, "w")
        except:
            print("Failed to open output file {}. Make sure the path is writable.".format(args.output), file=sys.stderr)
            exit()

    if not args.header is None:
        try:
            header_file = open(args.header)
        except:
            print("Failed to open header file {}. Make sure the file exists and is readable".format(args.header), file=sys.stderr)

    if not args.footer is None:
        try:
            footer_file = open(args.footer)
        except:
            print("Failed to open footer file {}. Make sure the file exists and is readable".format(args.header), file=sys.stderr)

    write_feed(input_file, output_file, header_file, footer_file)

    input_file.close()
    output_file.close()
    if not header_file is None: header_file.close()
    if not footer_file is None: footer_file.close()
    