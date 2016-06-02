import socket, threading, time, re


class cardserver(object):

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 5000
        self.clients = {} # I'm using a dict because it gives me better ability to keep track of user names.

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.HOST, self.PORT))
        self.sock.setblocking(True)
        self.quitting = False
        self.dispatch_prefixes = {'ch': self.relay_message, 'jo': self.new_connection,
                                  'ul': self.get_userlist}  # Currently this is only a partial list.

        print("The server has started")

    def listen_loop(self):
        '''This is the main loop which listens for in coming connections and when messages are received it handles
        the messages accordingly. The only problem with it currently that it is not threaded and were it to be threaded:
        new connections would have to be handled outside of this method. This is something that will be worked on
        once core functionality is built and confirmed to work'''

        while not self.quitting:
            try:
                data, addr = self.sock.recvfrom(2048)
                decode_data = data.decode('utf-8')

                # At this point we parse out the prefix and based upon that we call a certain slew of functions
                pre, null, message = decode_data.partition('&')

                # Here we may implement a check to ensure the user first joins the chat room but I may simply handle that
                # client side.
                try:
                    self.dispatch_prefixes[pre](msg = message, conn = addr)
                except KeyError: # Some other client is trying to connect to the server. This sends a message informing the
                    # user to get the proper client
                    self.sock.sendto(str.encode('This server only handles BJNet clients. To get a BJNet client visit: ' +
                                            'website.com'), addr)
            except:
                pass
        self.sock.close()

    def new_connection(self, **kwargs):
        handle = kwargs['msg']
        connection = kwargs['conn']
        # Here we check if the username is already being used. Multiple connections by the same client is handled server
        #side
        if handle in self.clients:
            self.sock.sendto(str.encode("409"), connection) # nh is prefix for new handle
        else:
            self.clients[handle] = (player(), connection) # Adds the client to the list of connected clients
            self.sock.sendto(str.encode('300'), connection)

    def relay_message(self, **kwargs):
        message = kwargs['msg']
        sender = kwargs['conn']
        print(time.ctime(time.time()) + str(sender) + ': :' + message)

        # Unfortunately one of the pitfalls of my design is that messages will have to be re-encoded and have the 'ch'
        # prefix re-attached. Unlike how this will be approached client-side we can simply append the prefix.

        message = str.encode('ch%' + message)
        for user, info in self.clients.items():
            client = info[1]
            self.sock.sendto(message, client)

    def send_message(self, **kwargs):
        '''The differene between this and relay message is that send message goes to one, and only one,
        recipient. Otherwise it does the exact same.'''
        pass

    def parser(self, message):
        '''A message is to consist of two parts a prefix and then a message body. Some messages that are simple commands
        will only have a prefix as there is no need to have a lengthy message. The prefix is seperated from the main
        body with an '&' symbol.


        A guide to what prefixes are used in this protocol is below.

        ch - Chat Message. Server simply logs this and relays message to all connected clients
            Format of a ch message is ch MESSAGE. Only MESSAGE is relayed to all clients.

        jo - Join Request. This starts a new session for the player. It will also prompt the server to check against existing
        connections and usernames to check for a mismatch. If records already exist they are told to either first quit
        and start anew... OR they are instructed to change username (should said username already exist.

            jo USER

            NOTE: Any server instructions are sent as chat protocol messages.

        co - Cashout. User leaves table. Connection is closed.

        ht - Hit Me. User is requesting a card. Changes to game-state are first applied server side and then are communicated
        to the player

        sd - Player stands locking in their current score

        bet - This prefix handles betting

            bet AMOUNT

        ul - A server side query to send all public information about the table to the requesting player

        pl - Similar to the previous command except it returns all private information about the requesting player to
        the player

        Note: These message encodings are handled by the client, the parser only strips/reads the prefix and based upon
        the prefix it handles the message in the proper fashion.
        '''

        # First we establish each of our regular expressions. For ease of use, I think it would be best if we put them
        # in a dictionary where the regular expression matches the prefix.
        pass


    def shutdown(self, **kargs):
        pass

    def get_userlist(self, **kwargs):
        '''This method gathers all publicly available information about other players and sends it back to the client
        who requested it. '''
        recipient = kwargs['conn']

    def get_playerinfo(self, **kwargs):
        pass

    def new_round(self):
        "Initialises a new round of gameplay."
        pass


class player(object):
    '''This is a class to handle gamestate/player management from the server server side.'''

    def __init__ (self):
        '''Currently all players will start with the same "slate".'''
        self.cards = () # The card in position 0 is the face down card.
        self.credits = 100
        self.currentbet = 0 # This is a sort of holding pool for the players current bet. The money is taken out of
        # credits.
        self.bust = False # This will change to true if the player has value over 21

def main():
    dealer = cardserver()
    dealer.listen_loop()

main()