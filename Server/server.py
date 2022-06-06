import socket
from _thread import *
import threading
from os.path import exists
from PIL import Image
import io

print_lock = threading.Lock()
inc_dec_lock = threading.Lock()
number_of_active_connections = 0


def request_parser(data):
    print("data received in bytes:")
    print(data)
    print("--------------------------------------------------------------------------------------------------")
    data = str(data, 'UTF-8')
    method = data.split(' /')[0]
    filename = data.split(' ')[1][1:]
    http_ver = data.split('\r\n')[0][-3:]
    body = ""
    if method == "POST":
        body = data.split("\r\n\r\n")[1]
    return method, filename, http_ver, body


def connection_parser(data):
    data = str(data, 'UTF-8')
    try:
        connection = data.split("Connection: ")[1][0]
        if connection == 'k':
            return 'k'
        else:
            return 'c'
    except IndexError:
        return 'c'


def keep_alive_parser(data):
    data = str(data, 'UTF-8')
    try:
        timeout = data.split("Keep-Alive: ")[1].split(", ")[0].split("=")[1]
        print("Time out: ", timeout)
        return int(timeout)
    except IndexError:
        return 10


def get_handler(filename, sock, http_ver):
    body = ""
    if filename[-3:] == "png":
        print("png File")
        image = Image.open(filename)
        output = io.BytesIO()
        image.save(output, format="png")
        body = output.getvalue()
    else:
        f = open(filename, "r")
        body = bytes(f.read(), 'utf-8')
        f.close()
    data_to_be_send = "HTTP/" + http_ver + " 200 OK\r\n\r\n"
    data_to_be_send = bytes(data_to_be_send, 'utf-8')
    data_to_be_send = data_to_be_send + body
    print("Data to be send in bytes:")
    print(data_to_be_send[:1024])
    print("------------------------------------------")
    sock.send(data_to_be_send)
    print("data has been sent")


def post_handler(filename, body, sock, http_ver):
    print("body to be written in file:")
    print(body)
    print("------------------------------------------")
    f = open(filename, "w+")
    f.write(body)
    print("body has been wrote")
    f.close()
    ok_message = "HTTP/" + http_ver + " 200 OK\r\n\r\n"
    ok_message = bytes(ok_message, 'utf-8')
    sock.send(ok_message)
    print("OK message has been sent")


def threaded(c):
    global number_of_active_connections
    inc_dec_lock.acquire()
    number_of_active_connections += 1
    print("number of active connections: ", number_of_active_connections)
    inc_dec_lock.release()
    while True:
        data = b''
        try:
            recv_data = []
            recv_data.append(c.recv(1024))
            c.settimeout(0.5)
            i = 0
            while recv_data[i]:
                data += recv_data[i]
                i += 1
                recv_data.append(c.recv(1024))
            c.settimeout(None)
        except TimeoutError:
            c.settimeout(None)

        if not data:
            break

        method, filename, http_ver, body = request_parser(data)
        print("method: " + method)
        print("filename: " + filename)
        print("http_ver: " + http_ver)
        print("--------------------------------------------------------------------------------------------------")

        if method == "POST":
            print("in POST")
            post_handler(filename, body, c, http_ver)
            print(
                "--------------------------------------------------------------------------------------------------")

        elif method == "GET":
            print("in GET")
            is_exist = exists(filename)
            if is_exist:
                print("file exists")
                print("------------------------------------------")
                get_handler(filename, c, http_ver)
                print(
                    "--------------------------------------------------------------------------------------------------")
            else:
                print("file not exists")
                error_message = "HTTP/" + http_ver + " 404 Not Found\r\n\r\n"
                error_message = bytes(error_message, 'utf-8')
                c.send(error_message)
                print("Error message has been sent")
                print(
                    "--------------------------------------------------------------------------------------------------")

        if http_ver == "1.1":
            connection = connection_parser(data)
            if connection == 'k':
                timeout = keep_alive_parser(data)
                print("Waitting... 1.1, keep-alive")
                c.settimeout(timeout / number_of_active_connections)
            else:
                print("Not waitting... 1.1, close")
                break
        else:
            print("Not waitting... 1.0")
            break

    c.close()
    print("connection closed")
    inc_dec_lock.acquire()
    number_of_active_connections -= 1
    print("number of active connections: ", number_of_active_connections)
    inc_dec_lock.release()
    print("--------------------------------------------------------------------------------------------------")
    print("--------------------------------------------------------------------------------------------------")
    #print_lock.release()


def Main():
    host = "127.0.0.1"
    port = 65432
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("--------------------------------------------------------------------------------------------------")
    print("socket binded to port", port)

    s.listen()
    print("socket is listening")
    print("--------------------------------------------------------------------------------------------------")

    while True:

        c, addr = s.accept()

        #print_lock.acquire()

        print('Connected to :', addr[0], ':', addr[1])

        start_new_thread(threaded, (c,))

    s.close()


if __name__ == '__main__':
    Main()
