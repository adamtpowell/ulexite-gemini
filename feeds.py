from os import stat
from typing import NamedTuple, List
import gemini
import re

FeedEntry = NamedTuple("FeedEntry", [
    ('feed_title', str),
    ('post_title', str),
    ('url', gemini.Url),
    ('date', str),
])

class Feed:
    def __init__(self, feed_title: str, entries: List[FeedEntry]):
        self.feed_title = feed_title
        self.entries = entries

    @staticmethod
    def from_page(page: gemini.Page, title: str = None) -> Feed: # type: ignore
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

        return Feed(
            feed_title,
            entries
        )