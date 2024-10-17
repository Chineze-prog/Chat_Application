from db_sql import * 
import socket
import select
import sys
import time
from datetime import datetime 

# maps the clients username to their socket object
connected_clients = {}

#variables to track perfomance
total_messages_recieved = 0
start_time = time.time()
running_time = 360 # 6mins

# sends a message from the server to all the connected clients
def send_message(messages, include_sender = True, sender = ""):
  global connected_clients

  message = messages + "\n" 
 
  for name, sock in connected_clients.items():
    try:   
      if not include_sender:
        if name != sender:
          sock.sendall(message.encode("UTF-8"))

      else:
        sock.sendall(f"\n{message}".encode("UTF-8"))

    except Exception as e:
      print(f"Error occurred while sending a message to {name}: {e}")
  
  if include_sender:
    print(message, end = '')


# splits un the protocoled message sent by the client
def split_message(unfiltered_message):
  try:
    timestamp, username, message = None, None, None

    # format -> [timestamp] username: message
    if unfiltered_message:
      timestamp_part, rest = unfiltered_message.split("] ", 1)
      username, message = rest.split(": ", 1)
      timestamp = timestamp_part[1:]

  except ValueError as ve:
    print(f"Error occurred while parsing the message recieved: {ve}")

  return timestamp, username, message  


# adds a message to the messages db and updates clients' last seen message and number of messages sent
def add_message(cursor, connection, timestamp, sender, message):
  global connected_clients

  add_new_message(cursor, connection, timestamp, sender, message)
  
  update_messages_sent_number(cursor, connection, sender)
  update_client_last_seen_message(cursor, connection, cursor.lastrowid)

  # send to the other clients
  send_message(format_messages([(timestamp, sender, message)]), include_sender = False, sender = sender) 
     

# deals with the messages that are recieved    
def handle_message(cursor, connection, unfiltered_message, client_socket):   
  timestamp, sender, message = split_message(unfiltered_message)
  try:
    if timestamp and sender and message:
      if message == "quit chat" or message == "exit":
        remove_client(cursor, connection, sender, client_socket)
      else:
        total_messages_recieved += 1
        add_message(cursor, connection, timestamp, sender, message)

    else:
      raise Exception("A client disconnected incorrectly.")
      #remove_client(cursor, connection, sender, client_socket)
  except Exception as e:
    print("Error:", e)
    remove_client(cursor, connection, sender, client_socket)


# recieves all the messages from a client
def receive_message(cursor, connection, username, client_socket):
  try:
    default_size = 1024
    full_message = b''
  
    while True:
      message_chunk = client_socket.recv(default_size)
      full_message += message_chunk

      if len(message_chunk) <= default_size: 
        break
    
    if full_message:
      unfiltered_messages_list = full_message.decode("UTF-8").split("\n")

      for unfiltered_message in unfiltered_messages_list:
        if unfiltered_message:
          handle_message(cursor, connection, unfiltered_message, client_socket)

    else:
      raise Exception("Client disconnected.")

  except Exception as e:
    print("Error:", e)
    remove_client(cursor, connection, username, client_socket)


# removes the client from the connected client list and closes the connection
def remove_client(cursor, connection, username, client_socket):
  global connected_clients

  update_connection_status(cursor, connection, username, 'inactive')

  try:
    client_socket.close()
    del connected_clients[username]
    print(f"{username} has disconnected")  

  except Exception as e:
    print(f"Error occurred while closing socket for {username}: {e}")

  send_message(f"{username} has left the chat.", include_sender = False, sender = username)


# formats the messages before sending them to the client
def format_messages(unformatted_messages_list):
  formatted_messages_list = []

  for timestamp, sender, message in unformatted_messages_list:
    formatted_message = f"[{timestamp}] {sender}: {message}"
    formatted_messages_list.append(formatted_message)
  
  messages_list = "\n".join(formatted_messages_list)

  return messages_list


# gets all the messages that the client has not seen and the last few messages from the chat 
def get_unread_messages(cursor, username):
  result = get_last_seen_msg_id(cursor, username)

  if result is None or result[0] is None:
    last_seen_message_id = 0
    last_few_messages = []
  else:
    last_seen_message_id = result[0]
    last_few_messages = get_last_100_msg_before_cutoff(cursor, last_seen_message_id)

  unread_messages = get_msg_after_cutoff(cursor, last_seen_message_id)

  return format_messages(list(reversed(last_few_messages))), format_messages(unread_messages)


# if the client is recurrng send them their unread messages and some of the last few messages
def send_last_and_unread_messages(cursor, connection, username, client_socket):
  last_few_messages, unread_messages = get_unread_messages(cursor, username)

  if unread_messages is not None and last_few_messages is not None:
    try:
      if last_few_messages:   
        client_socket.sendall(last_few_messages.encode("UTF-8"))

      if unread_messages:
        unread = f"\n\nUnread Messages:\n{unread_messages}\n"
        client_socket.sendall(unread.encode("UTF-8"))

      # update the clients last message seen 
      last_message_id = latest_msg_id(cursor)
      update_client_last_seen_message(cursor, connection, last_message_id[0])

    except Exception as e:
      print("Error occurred when sending unread messages to", username)
      remove_client(cursor, connection, username, client_socket, e)
    

# if the client is new to the db, send them the last 100 messages
def send_last_few_messages(cursor, connection, username, client_socket):
  last_few_messages = get_last_100_msg(cursor)
  
  formatted_messages_list = format_messages(list(reversed(last_few_messages))) + "\n"

  if formatted_messages_list:
    try:
      # send the previous 100 messages to the client
      client_socket.sendall(formatted_messages_list.encode("UTF-8"))

      # update the clients last message seen id
      last_message_id = latest_msg_id(cursor)
      update_client_last_seen_message(cursor, connection, last_message_id[0])

    except Exception as e:
      print("Error occurred when sending messages-log to", username)
      remove_client(cursor, connection, username, client_socket)    
 
      
# deals with the client when they connect to the server
def client_login(cursor, connection, username, client_socket):
  global connected_clients

  # if the username is unique add to the list of connected clients and clients db
  if username and username not in connected_clients:
    connected_clients[username] = client_socket

    if find_client(cursor, username):
      update_connection_status(cursor, connection, username, 'active')
      send_last_and_unread_messages(cursor, connection, username, client_socket)
    else:
      add_client(cursor, connection, username)
      send_last_few_messages(cursor, connection, username, client_socket)  
    
    # announce to all connected clients about the new client
    send_message(f"{username} has joined the chat.")

  else:
    try:
      client_socket.sendall(b"Username is already in use or is invalid. Please try again later.")
    except Exception as e:
      print(f"Error occured while sending a message to {username}: {e}")

    client_socket.close()


# deals with the server's shutdown
def shutdown(cursor, connection, server_socket):
  global connected_clients

  print("\nShutting down server...")

  for username, client_socket in connected_clients.items():
    try:
      client_socket.sendall(b"The server is shutting down. This connection is closing...\n")
    except Exception as e:
      print(f"Error occured while sending shutdown message to {username}: {e}")
    finally:
      try:
        update_connection_status(cursor, connection, username, 'inactive')
        client_socket.close()
      except Exception as e:
        print(f"Error occured while closing socket for {username}: {e}")

  connection.close()
  connected_clients.clear()
  server_socket.close()
  sys.exit(0)


def get_performance_stats():
  elapsed_time = time.time() - start_time

  if elapsed_time >= running_time:
    messages_per_sec = total_messages_recieved / elapsed_time
    print(f"Total messages recieved: {total_messages_recieved}")
    print(f"Messages per second: {messages_per_sec:.2f}")
    print(f"Ran for 6 mins.")
    return True

  else:
    return False


def main():
  global connected_clients
  global total_messages_recieved
  global start_time
  
  connection, cursor = initialize_db()
  server_host = ""
  server_port = 8576
  
  print(f"Listening on interface {socket.gethostname()} on port {server_port}")
    
  # binging and listening to a host and port
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.setblocking(False) # non-blocking
  server_socket.bind((server_host, server_port))
  server_socket.listen()

  print("To close the server press 'Ctrl + C'\nWaiting for input...")

  while True:
    try:
      inputs = [server_socket] + list(connected_clients.values())
      readable, writable, exceptional = select.select(inputs, [], inputs)

      for source in readable:
        if source is server_socket:
          # then we have a new client, accept new connection
          client_socket, client_address = server_socket.accept()
          print("Accepting connection from:", client_address)

          # get client's username
          username = client_socket.recv(1024).decode("UTF-8") 
          client_login(cursor, connection, username, client_socket)        
        else:
          receive_message(cursor, connection, username, source)

      #printing out performance statistics every minuite 
      if get_performance_stats():
        shutdown(cursor, connection, server_socket)
        break      
    except KeyboardInterrupt:
      shutdown(cursor, connection, server_socket)
    except Exception as e: 
      print("Error:", e)
      shutdown(cursor, connection, server_socket)
    finally:
      print("msg recieved", total_messages_recieved)
      print("msg/ser ", total_messages_recieved/(time.time()-start_time))

if __name__ == "__main__":
  main()

