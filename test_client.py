import termios
import socket
import select
import sys
from datetime import datetime
import time


start_time = time.time()
stop_time = 360
message_count = 0


def shutdown(message, username, client_socket, default = True):
  print(message)
  
  if not default:
    exit_message = set_protocol(username, "exit")
    client_socket.sendall(exit_message)
  
  client_socket.close()
  sys.exit(0)


def recieve_message(client_socket):
  default_size = 1024
  full_message = b''

  while True:
    message_chunk = client_socket.recv(default_size)
    full_message += message_chunk

    if len(message_chunk) <= default_size:
      break

  return full_message.decode("UTF-8")


def set_protocol(username, message):
  timestamp = datetime.now() 
  formatted_message = f"[{timestamp}] {username}: {message}\n"

  return formatted_message.encode("UTF-8")


def main():
  global message_count

  try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if len(sys.argv) != 4:
      print("format: python test_client.py <SERVER_HOST> <SERVER_PORT> <USERNAME>")
      sys.exit(0)

    client_host = sys.argv[1]
    client_port = int(sys.argv[2]) 
    username = sys.argv[3]

    client_socket.connect((client_host, client_port))

    client_socket.sendall(username.encode("UTF-8"))
    print("To exit the chat enter 'quit chat' or 'exit'")
   
    while True:
      try:
        inputs = [client_socket, sys.stdin]
        readable, writable, exceptional = select.select(inputs, [], inputs)

        for source in readable:
          if source is client_socket:
            message = recieve_message(client_socket)
  
            if message:
              print(message, flush = True, end = '')
            else:
              shutdown("Connection was closed by the server.", username, client_socket)

          elif (time.time() - start_time) <= stop_time:
            #time.sleep(0.015)
            string = f"newmsg {message_count}"
            message = set_protocol(username, string)
            client_socket.sendall(message)
            print(username, string + "\n", end = '')
            message_count += 1
          else:
            break

      except KeyboardInterrupt:
        shutdown("\nClosing client connection...", username = username, client_socket = client_socket, default = False)
        
      except Exception as e:
        print("Error:", e)
        shutdown("\nClosing client connection...", username, client_socket)
  
    shutdown("\nClosing client connection...", username = username, client_socket = client_socket)

  except Exception as e:
    print("The login information (host or port) is incorrect. Please try again.")
    client_socket.close()
    sys.exit(0)

  finally:
    print("Messages sent ", message_count)
    print("connection closed.")


if __name__  == "__main__":
  main()
