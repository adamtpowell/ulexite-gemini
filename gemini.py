from typing import List, Tuple, NamedTuple, Optional
import socket
import ssl
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

class Url:
    def __init__(self, protocol: str, hostname: str, port: int, path: str):
        self.hostname = hostname
        self.protocol = protocol
        self.port = 1965 if port is None else int(port)
        self.path = path

    _url_re = re.compile("(.*)://([^/^:]*):?([0-9]+)?(/.*)?") # Compile this for the from_str method

    @staticmethod
    def from_str(url: str):
        match = Url._url_re.match(url)
        if match is None:
            raise ValueError("Malformed URL ", url) 

        protocol, hostname, port_str, path = match.groups()
        if path == None: path = ""
            
        if port_str == None:
            port = 1965
        else:
            port = int(port_str)

        return Url(protocol, hostname, int(port), path)

    # Append a relative url as str
    def with_relative(self, relative: str):

        try:
            return Url.from_str(relative)
        except:
            pass # If you can't make the url from the relative string (that is, it is actually relative), continue

        split = urlsplit(str(self))
        with_http = urlunsplit(("http", split[1], split[2], split[3], split[4])) # Ugly hack to make url join work
        res_with_http = urljoin(with_http, relative)
        with_http_split = urlsplit(res_with_http)
        with_gemini = urlunsplit(("gemini", with_http_split[1], with_http_split[2], with_http_split[3], with_http_split[4]))
        return Url.from_str(with_gemini)


    def __repr__(self):
        return "{}://{}:{}{}".format(self.protocol,self.hostname, self.port, self.path)

class GemtextLink:
    def __init__(self, url: Url, label: Optional[str]):
        self.url = url
        self.label = label

    @staticmethod
    def from_str(link_line: str, base_url: Url = None):
        link_pattern = re.compile(
            "=>\s+"
            "([^\s]*)" # URL contains anything but whitespace
            "\s*"
            "(.*)"
        )

        matches = link_pattern.match(link_line)

        if matches is None:
            return None

        partial_url = matches.group(1)
        link_name: Optional[str] = matches.group(2)

        if link_name == "":
            link_name = None

        if not base_url is None:
            full_url = base_url.with_relative(partial_url)
        else:
            full_url = Url.from_str(partial_url)

        return GemtextLink(
            full_url,
            link_name
        )

class Page:
    def __init__(self, url: Url, status: int, meta: str, body: List[str]):
        self.url = url
        self.status = status
        self.meta = meta
        self.body = body

    @property
    def title(self) -> str:
        title_pattern = re.compile("#\s*(.*)")

        for line in self.body: # Find title
            if (len(line) == 0):
                continue

            if (line[0] == "#"):
                match = title_pattern.match(line)
                if not match is None:
                    return match.group(1) or str(self.url)

        return str(self.url.hostname)

    @property
    def links(self) -> List[GemtextLink]:
        links: List[GemtextLink] = []
        for line in self.body: # Read links
            if line[0:2] != "=>":
                continue # ignore lines which aren't links to speed things up.

            link = GemtextLink.from_str(line, base_url = self.url) # If its a non-fully qualifed url, use self.url as the base

            if not link is None:
                links.append(link)
        
        return links
    

# Gets a raw response from the server.
# Does not handle response codes
def _fetch_response(url: Url) -> Page:
    context = ssl.SSLContext()
    context.verify_mode = ssl.CERT_NONE
    context.check_hostname = False

    with socket.create_connection((url.hostname, 1965), 2) as sock:
        with context.wrap_socket(sock, server_hostname=url.hostname) as secure_socket: # server_hostname is required or else internal ssl error
            request = str(url) + "\r\n"
            secure_socket.send(request.encode('utf-8'))

            response = b""

            while True:
                data = secure_socket.recv(4096)
                if not data: break
                response += data

    lines = response.decode("utf-8").splitlines()
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