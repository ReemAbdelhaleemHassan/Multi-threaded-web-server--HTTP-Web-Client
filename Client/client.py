import socket


def request_parser(line):
    method = line.split(" ")[0]
    filename = line.split(" ")[1][1:]
    host = line.split(" ")[2]
    try:
        port = int(line.split(" ")[3].strip())
    except IndexError:
        port = 80

    body = ""
    if method == "POST":
        f = open(filename, "r")
        body = f.read()
        f.close()

    print("Method: ", method)
    print("Filename: ", filename)
    print("Host:", host)
    print("Port: ", port)
    print("Body: ", body)
    print("--------------------------------------------------------------------------------------------------")

    #http_ver = input("http version: ")
    http_ver = "1.0"

    request = method + " /" + filename + " HTTP/" + http_ver + "\r\n"
    request = request + "Host: " + host + ":" + str(port) + "\r\n"
    request = request + "\r\n" + body

    return request, host, port


old_requests = []
old_reponses = []


def has_been_cached(request):
    i = old_requests.index(request)
    print("********************Cached********************")
    print("Cashed response:")
    print(old_reponses[i])
    print("--------------------------------------------------------------------------------------------------")
    print("----------------------------------------------------------------")


#file_path = input("File path: ")
file_path = "client_commands.txt"

file = open(file_path, 'r')
lines = file.readlines()
file.close()


for line in lines:

    request, HOST, PORT = request_parser(line)
    if request in old_requests:
        has_been_cached(request)
        continue
    else:
        old_requests.append(request)
    request = bytes(request, 'utf-8')
    print("request in bytes:")
    print(request)
    print("--------------------------------------------------------------------------------------------------")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))

            s.sendall(request)

            data = b''
            try:
                recv_data = []
                recv_data.append(s.recv(1024))
                s.settimeout(0.5)
                i = 0
                while recv_data[i]:
                    data += recv_data[i]
                    i += 1
                    recv_data.append(s.recv(1024))
                s.settimeout(None)
            except TimeoutError:
                s.settimeout(None)

            print("Received in bytes: ")
            print(data[:1024])
            old_reponses.append(data)
        except ConnectionRefusedError:
            print("Couldnt connect with the server")

        print("--------------------------------------------------------------------------------------------------")
        print("----------------------------------------------------------------")
