from typing import List, Tuple, NamedTuple
import socket
import ssl
import re
import functools


class Url:
    def __init__(self, hostname: str, port: int, path: str):
        self.hostname = hostname
        self.port = 1965 if port is None else int(port)
        self.path = path

    @staticmethod
    def from_str(url: str):
        try:
            hostname, port, path = re.match("gemini://([^/^:]*):?([0-9]+)?(/.*)?", url).groups()
            print(hostname, port, path)
            if path == None: path = ""
        except:
            raise ValueError("Malformed URL ", url)

        return Url(hostname, port, path)

    def __repr__(self):
        return "gemini://{}:{}{}".format(self.hostname, self.port, self.path)

GemtextLink = NamedTuple("GemtextLink", [
    ('url', Url),
    ('label', str)
])

class Page:
    def __init__(self, url: Url, status: int, meta: str, body: List[str]):
        self.url = url
        self.status = status
        self.meta = meta
        self.body = body

    @functools.cached_property
    def title(self) -> str:
        title_pattern = re.compile("#\s*(.*)")

        for line in self.body: # Find title
            if (len(line) == 0):
                continue

            if (line[0] == "#"):
                return title_pattern.match(line).group(1) or str(self.url)

        return str(self.url.hostname)

    @functools.cached_property
    def links(self) -> List[GemtextLink]:
        url_pattern = re.compile( # Three groups: protocol, url, date, text
            "=>\s+" # => 
            "(gemini://|http://|https://|finger://|gopher://)?" # Protocol
            "([^\s]*)" # URL (continues until first whitespace)
            "\s*" # URL is seperated from title by arbitrary whitespace
            "(.*)" # title is the rest of the line
        )
        links: List[GemtextLink] = []
        for line in self.body: # Read links
            if line[0:2] != "=>":
                continue # ignore lines which aren't links

            link_protocol, link_url, link_text = url_pattern.match(line).groups()

            # Create a fully qualified link from the fragments
            # This is WRONG but works for now, TODO: read RFC
            if link_protocol == None:
                link = str(self.url) + link_url
            else:
                link = link_protocol + link_url

            link = Url.from_str(link)

            links.append(GemtextLink(link, link_text))
        
        return links
    

# Gets a raw response from the server.
# Does not handle response codes
def _fetch_response(url: Url) -> Page:
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE
    context.check_hostname = False

    # TODO: Vectorpoems site doesn't work...
    with socket.create_connection((url.hostname, 1965), 2) as sock:
        with context.wrap_socket(sock) as secure_socket: # it fails here with errno 0 which is strange
            request = str(url) + "\r\n"
            secure_socket.send(request.encode('utf-8'))

            response = b""

            while True:
                data = secure_socket.recv(4096)
                if not data: break
                response += data

    response = response.decode("utf-8")

    lines = response.splitlines()
    header = lines[0]
    body = lines[1:]

    response_code = int(header[0:2])
    meta = header[3:]
    
    return Page(url, response_code, meta, body)

# Handle response codes
def fetch_page(url: Url) -> Page:
    success = True
    redirects = 0
    while True:
        response = _fetch_response(url)
        status = response.status // 10
        if status == 3: # Redirect
            url = Url.from_str(response.meta) # Url is given in META
            redirects += 1
            if redirects > 10:
                success = False
                break
            continue # Try again

        if status != 2: # Failure / requires input / client cert needed
            success = False
            
        break
    
    if not success:
        raise Exception("Page load failed: {} {}".format(response.status, response.meta))
    
    return response