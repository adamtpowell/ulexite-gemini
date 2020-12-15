# TODO

[] More feed options (detected automatically)
    [] Atom
    [] Date tites (multiple formats)
    [] Page changes
        [] Add sqlite database for keeping track of feed info
    [x] Refactor feeds to seperate class
[] Package
[] Tests
[x] Add updated time to start of feeds
[x] Get rid of seperator characters at the start of feed entry names
[x] Use gemlink for feeds.txt. Get feed title from this.
[x] Handle header and footer
[x] stdin and stdout
[x] Command line help
[x] ...Correctly... make URLS fully qualified if they are not already.
    [x] Read RFC
[x] Fix vectorpoem error
[x] limit redirect depth
[x] refactor feed generation
[x] handle ports
[x] Show list of feeds with titles.

## Feed option rundown

try atom
try gemfeed
    if has correct link text, break
try date headings
    if it has wrong ones, try different date formats until one works
    if you find one, break
try update page
    this is the fallback
    requires access to a sqlite database of last page hash
    cannot give accurate date, but is useful as a last resort.