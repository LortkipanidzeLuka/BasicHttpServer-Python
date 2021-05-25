from email.parser import BytesParser


DOMAIN_NOT_FOUND_BODY = "REQUESTED DOMAIN NOT FOUND"
SPACE_SYMBOL = "%20"
NOT_FOUND_STATUS_CODE = "404"
INVALID_URL_STATUS_MESSAGE = "Invalid URL"
SUCCESS_STATUS_CODE = "200"
SUCCESS_RANGE_STATUS_CODE = "206"
SUCCESS_STATUS_MESSAGE = "OK"
NOT_FOUND_STATUS_MESSAGE = "Not Found"


class ParsedHttpRequest:

    def __init__(self, request_string):
        info, headers = parseHttpRequest(request_string)
        method = info[0]
        path = info[1]
        http_version = info[2]
        self.headers = headers
        self.http_version = http_version
        self.path = path
        self.method = method


def parseHttpRequest(request_string):
    request_line, headers_alone = request_string.split(b'\r\n', 1)
    request_line_splitted = request_line.decode().split(' ')
    headers = BytesParser().parsebytes(headers_alone)
    headers = {k.lower(): v for k, v in headers.items()}
    host = headers['host'].split(':')[0]

    headers['host'] = host
    return request_line_splitted, headers


class CustomHttpResponse:

    def __init__(self):
        self.response_headers = {}
        self.response_body = ""
        self.http_version = ""
        self.status = ""
        self.status_message = ""
        self.method = ""

    def addHeader(self, key, value):
        self.response_headers[key] = value

    def setHttpInfo(self, http_version, status, status_message, method):
        self.http_version = http_version
        self.status = status
        self.status_message = status_message
        self.method = method

    def addAllHeaders(self, current_date, content_length="", content_type="", server="python", etag="",
                      connection_type="keep-alive", connection_timeout=5, accept_ranges="bytes"):
        self.addHeader("server", server)
        self.addHeader("date", current_date)
        self.addHeader("content-length", content_length)
        self.addHeader("content-type", content_type)
        self.addHeader("etag", etag)
        self.addHeader("connection", connection_type)
        if connection_type == "keep-alive":
            self.addHeader("keep-alive", "keep-alive=" + str(connection_timeout))
        self.addHeader("ACCEPT-RANGES", accept_ranges)

    def setResponseBody(self, body):
        self.response_body = body

    def getRawResponseHeaders(self):
        response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in self.response_headers.items())
        return response_headers_raw

    def getHttpResponse(self):

        response = self.getRawResponseHeaders()
        response = self.http_version + " " + self.status + " " + self.status_message + "\r\n" + response + '\n'
        response = response.encode()
        if self.method == 'HEAD':
            return response
        if self.method == 'GET':
            if self.response_body != "":
                return response + self.response_body
            return response

