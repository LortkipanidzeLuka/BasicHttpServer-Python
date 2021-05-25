import json
from socket import *
from threading import Thread
from datetime import date
from os.path import isdir
from os.path import isfile
from os import listdir
from HttpUtils import *
import magic

NUMBER_OF_CONNECTIONS = 1024

class IpPortHandler:

    def __init__(self, ip, port, log_path):
        self.ip = ip
        self.port = port
        self.log_path = log_path
        self.vHosts = {}
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((ip, port))

    def addVirtualHost(self, vhost, document_root):
        self.vHosts[vhost] = document_root

    def serveClient(self, client_socket, client_address):

        client_socket.settimeout(5)
        while True:
            try:
                request = client_socket.recv(1000)
                if request == b"":
                    client_socket.close()
                    break
                parsed_request = ParsedHttpRequest(request)

                response = self.getResponse(parsed_request)
                client_socket.send(response)
          #      print(parsed_request.headers['connection'])

                if parsed_request.headers['connection'] == "close":
                    client_socket.close()
                    break
            except Exception as e:
             #print(e)
                client_socket.close()
                break

    def waitForClients(self):
        while True:
            client_socket, client_address = self.socket.accept()
            self.serveClient(client_socket, client_address)

    def openSocket(self):
        self.socket.listen(NUMBER_OF_CONNECTIONS)
        self.socket.listen()
        socket_thread = Thread(target=self.waitForClients)
        socket_thread.start()

    def getResponse(self, request):
        response = CustomHttpResponse()

        method = request.method
        path = request.path.replace(SPACE_SYMBOL, " ")
        http_version = request.http_version
        request_headers = request.headers
        domain = request_headers['host']
        connection_type = request_headers['connection']
        current_time = date.today()

        if domain not in self.vHosts:
            response.addAllHeaders(current_date=current_time, content_length=len(DOMAIN_NOT_FOUND_BODY),
                                   content_type="text/plain",
                                   connection_type=connection_type)
            response.setHttpInfo(http_version=http_version, status=NOT_FOUND_STATUS_CODE,
                                 status_message=INVALID_URL_STATUS_MESSAGE, method=method)
            response.setResponseBody(DOMAIN_NOT_FOUND_BODY.encode("UTF-8"))
            return response.getHttpResponse()

        full_path = self.vHosts[domain] + path

        try:
            mime = magic.Magic(mime=True)
            content_type = "text/html" if isdir(full_path) else mime.from_file(full_path)
            if 'range' in request_headers:
                range_header = request_headers['range']
                content_range = range_header.split('=')[1]
                range_start, range_end = getRange(content_range)
                file_content = getFileContent(full_path, start_byte=range_start, end_byte=range_end)
                status_code = SUCCESS_RANGE_STATUS_CODE
            else:
                file_content = getFileContent(full_path) if isfile(full_path) else getFolderContent(full_path, path).encode()
                status_code = SUCCESS_STATUS_CODE

        except OSError as e:
            response.addAllHeaders(current_date=current_time)
            response.setHttpInfo(http_version=http_version, status=NOT_FOUND_STATUS_CODE,
                                 status_message=NOT_FOUND_STATUS_MESSAGE, method=method)
            return response.getHttpResponse()

        response.addAllHeaders(server="python", current_date=current_time, content_length=len(file_content),
                               content_type=content_type, etag="")
        response.setHttpInfo(http_version=http_version, status=status_code, status_message=SUCCESS_STATUS_MESSAGE,
                             method=method)
        response.setResponseBody(file_content)
        return response.getHttpResponse()


def getFolderContent(full_path, path):
    return htmlGenerator([f for f in listdir(full_path)], path)


def getFileContent(full_path, start_byte=0, end_byte=-1):
    file = open(full_path, 'rb')
    file.seek(start_byte, 1)
    if end_byte == -1:
        file_content = file.read()
        file.close()
        return file_content

    num_bytes = end_byte - start_byte + 1
    file_content = file.read(num_bytes)
    file.close()
    return file_content




def getRange(content_range):
    content_range_splitted = content_range.split("-")
    if content_range[0] == '-':
        return 0, int(content_range_splitted[0])

    elif content_range[len(content_range) - 1] == '-':
        return int(content_range_splitted[0]), -1

    range_start = content_range_splitted[0]
    range_end = content_range_splitted[1]
    return int(range_start), int(range_end)


def readConfigFile():
    with open('config.json') as json_file:
        data = json.load(json_file)

    log_path = data['log']
    server_list = data['server']
    ip_port_handlers = {}

    for server in server_list:
        ip = server['ip']
        port = server['port']
        key = (ip, port)
        domain = server['vhost']
        root = server['documentroot']

        ip_port_handler = IpPortHandler(ip, port, log_path) if key not in ip_port_handlers else ip_port_handlers[key]
        ip_port_handlers[key] = ip_port_handler
        ip_port_handler.addVirtualHost(vhost=domain, document_root=root)

    return ip_port_handlers


def htmlGenerator(file_list, path):
    html_start = "<html>\n    <head>\n    </head>\n    <body>"
    html_links = ""
    if path == "/":
        path = ""
    for file in file_list:
        html_links += '        <a href=" ' + path + "/"  + file + '">' + file + '</a> <br>\n'

    html_end = "    </body>\n </html> "

    return html_start + html_links + html_end


ip_port_handlers2 = readConfigFile()
for handler in ip_port_handlers2:
    ip_port_handlers2[handler].openSocket()
