# Part 2: Analysis

# Analysis

I had 8 data points: [1, 2, 5, 10, 20, 50, 100, 200] and each of my experiments runs for 6 minutes.

My server was on the "owl.cs.umanitoba.ca" host with port number 8576.

I modified my server - test_server.py - to run for 6 mins and recieve as many messages it can and send them back to clients. I also modified my client - test_client.py - to send as many messages it can in 6 mins while recieving messages as well.

I used bash scripting -run_clients.sh- to run as many clients as in need for each data point.

The table below shows:

- the messages sent by each client

- the total messages the clients were able to recieve

- the avarage, which is based on the number of messages sent/ time running.

The result looks like this:

    clients #| Experiment 1                      | Experiment 2                      | Experiment 3

             | msg sent | msg recieved | Average | msg sent | msg recieved | Average | msg sent | msg recieved | Average 

            1|   43168  |    33763     | 7194.67 |   43114  |    34015     | 7185.67 |   43146  |     33801    | 7191   
        
            2|   34623  |    30959     | 5770.5  |   34594  |    31186     | 5765.67 |   34623  |     31070    | 5770.5

            5|   34326  |    31960     | 5721    |   34371  |    29367     | 5728.5  |   34389  |     27902    | 5731.5

           10|   34248  |    32555     | 5708    |   34293  |    30644     | 5715.5  |   34203  |     31583    | 5700.5

           20|   23022  |    28792     | 3837    |   23024  |    29646     | 3837.33 |   22998  |     29650    | 3833

           50|   17556  |    27005     | 2926    |   17582  |    29305     | 2930.33 |   17553  |     25534    | 2925.5

          100|   8951   |    1491.833  | 1491.83 |   9022   |    5664      | 1503.67 |   9545   |     5709     | 1590.833

          200|   3869   |    644.83333 | 644.833 |   3948   |    5516      | 658     |   3864   |     5877     | 644

Boxplot Data - messages per minute

    1  Client  | 2 Clients | 5 Clients | 10 Clients | 20 Clients | 50 Clients | 100 Clients | 200 Clients

    7194.667   | 5770.5    | 5721      | 5708       | 3837       | 2926       | 1491.833    | 644.83333

    7185.667   | 5765.667  | 5728.5    | 5715.5     | 3837.333   | 2930.333   | 1503.667    | 658

    7191       | 5770.5    | 5731.5    | 5700.5     | 3833       | 2925.5     | 1590.833    | 644


Did running more clients affect the performance of your server?

- Yes, running more clients slowed down the server

- In the beginning, 1 to 10 clients, the performance degrades linearly because the number of messages per minute decreases steadily but not drastically. But beyond the 20 clients mark, the performance degrades in a more quadratic manner since there are significant drops in the number of messages per minute.
  
- The server is not able to process alot of data comming from alot of clients at once so it results in loss of data.

