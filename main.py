from collections import defaultdict
from typing import List, Tuple, NamedTuple, DefaultDict, Dict
import gemini
import sys
import re

FeedEntry = NamedTuple("FeedEntry", [
    ('feed_title', str),
    ('link', gemini.GemtextLink),
    ('date', str),
])

def read_feed(page: gemini.Page) -> List[FeedEntry]:
    entries: List[FeedEntry] = []
    feed_title = page.title

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

def feed_output(followed_feeds: List[gemini.Page], updates_by_date: Dict[str, List[FeedEntry]]) -> str:
    follows = "\n".join("=> {} {}".format(feed.url, feed.title) for feed in followed_feeds)

    updates = ""
    for date in updates_by_date.keys():
        updates += "### {}".format(date)
        updates += "\n\n"
        for entry in updates_by_date[date]:
            updates += "=> {} {} | {}".format(entry.link.url, entry.feed_title, entry.link.label)
            updates += "\n"
        updates += "\n"
    
    result = """# {title}

## Follows

{follows}

## Updates

{updates}""".format(
        title = "Uxelite",
        follows = follows,
        updates = updates
    )
    
    return result

if __name__ == "__main__":
    feed_updates: DefaultDict[str, List[FeedEntry]] = defaultdict(list)
    followed_feeds: List[gemini.Page] = []

    with open(sys.argv[1]) as feed_file:
        feed_urls = feed_file.readlines()

    for feed_url in feed_urls:
        try:
            page = gemini.fetch_page(gemini.Url.from_str(feed_url))
        except Exception as e:
            print("Failure fetching feed", str(feed_url), ":", e, file=sys.stderr)
            continue # Just skip this url and you should be fine
        followed_feeds.append(page)

        entries = read_feed(page)
        for feed_entry in entries:
            feed_updates[feed_entry.date].append(feed_entry)
    
    with open(sys.argv[2], "w") as out_file:
        out_file.write(feed_output(followed_feeds, feed_updates))

            