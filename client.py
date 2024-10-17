import termios
import socket
import select
import sys
from datetime import datetime


def customize_terminal():
  # so that the user's message is not echoed in the terminal
  fd = sys.stdin.fileno()
  newattr = termios.tcgetattr(fd)
  newattr[3] = newattr[3] & ~termios.ICANON
  #newattr[3] = newattr[3] & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr) 


def restore_terminal():
  # so that the terminal is returned to its original state
  fd = sys.stdin.fileno()
  newattr = termios.tcgetattr(fd)
  newattr[3] = newattr[3] |  ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)


def shutdown(message, username, client_socket, default = True):
  print(message)

  if not default:
    exit_message = set_protocol(username, "exit")
    client_socket.sendall(exit_message)

  client_socket.close()
  sys.exit(0)


def get_login_details():
  host = input("Enter server host name: ")
  port = int(input("Enter server port: "))
  username = input("Enter unique username: ")

  while username == "" or username == " ":
    username = input("Please enter a username: ")

  return host, port, username


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
  try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
    client_host, client_port, username = get_login_details()
  
    client_socket.connect((client_host, client_port))

    client_socket.sendall(username.encode("UTF-8"))
    print("To exit the chat enter 'quit chat' or 'exit'")
 
    customize_terminal()
    
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

          elif source is sys.stdin:
            user_input = sys.stdin.readline().strip()

            if(user_input != "" and user_input != "\n" and user_input != " "):
              message = set_protocol(username, user_input)
              client_socket.sendall(message)

      except KeyboardInterrupt:
        shutdown("\nClosing client connection...", username = username, client_socket = client_socket, default = False)
        
      except Exception as e:
        print("Error:", e)
        shutdown("\nClosing client connection...", username, client_socket)
  
  except Exception as e:
    print("The login information (host or port) is incorrect. Please try again.")
    client_socket.close()
    sys.exit(0)

  finally:
    restore_terminal()
    print("connection closed.") 


if __name__  == "__main__":
  main()
