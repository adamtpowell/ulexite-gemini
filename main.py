from collections import defaultdict
from typing import List, DefaultDict, Optional
import gemini
import sys
import argparse
from multiprocessing import Pool
from datetime import datetime
from feeds import FeedEntry, Feed


def feed_from_link(feed_link: gemini.GemtextLink) -> Optional[Feed]:
    try:
        page = gemini.fetch_page(feed_link.url)
        return Feed.from_page(page, feed_link.label)
    except Exception as e:
        print("Failure fetching feed at", str(feed_link.url), ":", e, file=sys.stderr)
        return None


def write_body(input_file, output_file, header_file, footer_file):

    links_to_feeds = [gemini.GemtextLink.from_str(line) for line in input_file.readlines()]

    with Pool(processes = 16) as pool:
        feeds = pool.map(feed_from_link, links_to_feeds)
        feeds = [feed for feed in feeds if not feed is None]
   
    feed_updates_by_date: DefaultDict[str, List[FeedEntry]] = defaultdict(list)

    for feed in feeds:
        for feed_entry in feed.entries:
            feed_updates_by_date[feed_entry.date].append(feed_entry)

    # Build the list of feeds given the updates by date.
    feed_list = ""
    for date in sorted(feed_updates_by_date.keys(), reverse=True):
        for entry in feed_updates_by_date[date]:
            feed_list += "=> {} {} {} | {}".format(entry.url, date, entry.feed.title, entry.post_title)
            feed_list += "\n"
        feed_list += "\n"

    header_value = "" if header_file == None else "".join(header_file.readlines())
    footer_value = "" if footer_file == None else "".join(footer_file.readlines())

    today_utc = datetime.utcnow().isoformat(sep=" ",timespec="minutes")

    output_file.write(header_value)

    output_file.write("Last fetched on {} utc\n\n".format(today_utc))

    output_file.write(feed_list)
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

    write_body(input_file, output_file, header_file, footer_file)

    input_file.close()
    output_file.close()
    if not header_file is None: header_file.close()
    if not footer_file is None: footer_file.close()