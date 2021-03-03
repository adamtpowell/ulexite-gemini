from os import stat
from typing import NamedTuple, List
import gemini
import re
import defusedxml.ElementTree as ElementTree
import dateutil.parser

class Feed:
    def __init__(self, title: str, entries: List['FeedEntry']):
        self.title = title
        self.entries = entries


    @staticmethod
    def from_page(page: gemini.Page, title: str = None) -> 'Feed':
        # Attempt to parse an atom feed.
        try:
            root: ElementTree = ElementTree.fromstring("".join(page.body))
            if root.tag != "{http://www.w3.org/2005/Atom}feed":
                raise ValueError("Not an atom feed")

            return Feed.from_atom_root(root, title)
        except Exception as e:
            # We silently fail parsing as an atom feed. The fallback is to try other methods
            print(e)
            pass
        
        # If the feed is not an atom feed, then try to pull a gemfeed from it
        return Feed.from_page_gemfeed(page, title)


    # Create a Feed from an ElementTree
    @staticmethod
    def from_atom_root(root: ElementTree, title: str = None) -> 'Feed':
        entries: List['FeedEntry'] = []
        feed_title = title or "TODO: Find title"

        new_feed = Feed(
            feed_title,
            entries
        )

        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text or "Post"

            link_text = entry.find("{http://www.w3.org/2005/Atom}link").attrib["href"]
            # TODO: Unhack this by splittling from_str and from_gemline            
            gemtext_line = f"=> {link_text} {title}" # Construct a gemtext line (hacky I know)
            link = gemini.GemtextLink.from_str(gemtext_line)

            raw_date = entry.find("{http://www.w3.org/2005/Atom}updated").text
            date = dateutil.parser.parse(raw_date)
            date_text = date.strftime("%Y-%m-%d")

            new_feed.entries.append(FeedEntry(
                new_feed, # Feed backlink
                title.strip(), # Title
                link.url, # URL
                date_text.strip() # Date
            ))

        return new_feed


    @staticmethod
    def from_page_gemfeed(page: gemini.Page, title: str = None) -> 'Feed':
        entries: List['FeedEntry'] = []

        feed_title = page.title if title is None else title

        new_feed = Feed(
            feed_title,
            entries
        )

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

            new_feed.entries.append(FeedEntry(
                new_feed,
                label_without_date,
                link.url,
                date
            ))

        return new_feed
    

FeedEntry = NamedTuple("FeedEntry", [
    ('feed', Feed),
    ('post_title', str),
    ('url', gemini.Url),
    ('date', str),
])