from typing import List, Tuple
import socket
import ssl
import re

class GemUrl:
    def __init__(self, hostname: str, path: str):
        self.hostname = hostname
        self.path = path

    @staticmethod
    def from_str(url: str):
        try:
            hostname, path = re.match("gemini://([^/]*)(/.*)?", url).groups()
            if path == None: path = ""
        except:
            raise ValueError("Malformed URL ", url)

        return GemUrl(hostname, path)

    def __repr__(self):
        return "gemini://" + self.hostname + self.path

# Gets a raw response from the server.
# Does not handle response codes
def get_response(url: GemUrl) -> Tuple[int, str, List[str]]:
    context = ssl.create_default_context()

    print("Fetching", str(url))

    with socket.create_connection((url.hostname, 1965)) as sock:
        with ssl.wrap_socket(sock) as secure_socket: # TODO: ssl.wrap_socket is deprecated. find other way of working with self signed certs
            req = str(url) + "\r\n"
            secure_socket.send(req.encode('utf-8'))

            response = ""

            while True:
                data = secure_socket.recv(16)
                if not data: break
                response += data.decode('utf-8')

            lines = response.splitlines()
            header = lines[0]
            body = lines[1:]

            response_code = int(header[0:2])
            meta = header[3:]
    
    return (response_code, meta, body)

# Handle response codes
def get_page(url: GemUrl):
    success = True
    while True:
        response = get_response(url)
        status = response[0] // 10
        if status == 3: # Redirect
            print("Redirected to:", response[1])
            url = GemUrl.from_str(response[1]) # Url is given in META
            continue # Try again

        if status != 2: # Failure / requires input / client cert needed
            print("Got failure code", response[0])
            success = False
            
        break
    
    if not success:
        print("Page load failed:", response[0], response[1])
    else:
        print(response)