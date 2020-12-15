from collections import defaultdict
from typing import List, Tuple, NamedTuple, DefaultDict, Dict
import gemini
import sys
import re
import argparse
from multiprocessing import Pool
from datetime import datetime

FeedEntry = NamedTuple("FeedEntry", [
    ('feed_title', str),
    ('post_title', str),
    ('url', gemini.Url),
    ('date', str),
])

def get_entries_from_page(page: gemini.Page, title: str) -> List[FeedEntry]:
    entries: List[FeedEntry] = []

    feed_title = page.title if title is None else title

    date_re = re.compile("([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*(.*)?")

    seperator_removal_re = re.compile("\s*[-=|~:]+\s+") # Matches seperator between date and text.

    for link in page.links:
        if link.label is None: continue # Link cannot have date if it has no label
        
        date_match = date_re.match(link.label)
        if date_match is None: continue

        date, label_without_date = date_match.groups()

        if date is None: continue

        # Many feeds use a seperator character between the date and the text. Remove it.
        label_without_date = seperator_removal_re.sub("", label_without_date)

        entries.append(FeedEntry(
            feed_title,
            label_without_date,
            link.url,
            date
        ))

    return entries

def get_feed_list(updates_by_date: Dict[str, List[FeedEntry]]) -> str:
    updates = ""
    for date in sorted(updates_by_date.keys(), reverse=True):
        for entry in updates_by_date[date]:
            updates += "=> {} {} {} | {}".format(entry.url, date, entry.feed_title, entry.post_title)
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
    feed_updates_by_date: DefaultDict[str, List[FeedEntry]] = defaultdict(list)

    links_to_feeds = [gemini.GemtextLink.from_str(line) for line in input_file.readlines()]

    with Pool(processes = 16) as pool:
        pages = pool.map(page_with_title_from_url, links_to_feeds)

    for page_with_title in filter(lambda pages: not pages is None, pages):
        page, title = page_with_title
        
        entries = get_entries_from_page(page, title)
        
        for feed_entry in entries:
            feed_updates_by_date[feed_entry.date].append(feed_entry)

    feed_list = get_feed_list(feed_updates_by_date)

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

    write_feed(input_file, output_file, header_file, footer_file)

    input_file.close()
    output_file.close()
    if not header_file is None: header_file.close()
    if not footer_file is None: footer_file.close()
    