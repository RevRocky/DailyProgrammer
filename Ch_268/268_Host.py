import socket, threading, time, re
from random import randint

class CardServer(object):

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

        # Now we generate ourselves a deck of cards!
        self.deck = []
        self.deck = self.construct_deck()

        # Finally we make a counter keeping track of how many players have stood or gone bust. When it reaches four:
        # we trigger a new game.
        # TODO Ensure this variable is properly updated once threading is implemented.
        self.stand_bust_count = 0





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
        for client in self.clients:
            if handle in client[0]:
                self.sock.sendto(str.encode("409"), connection)  # nh is prefix for new handle
                return # Now we cut out of the function

        self.clients[connection] = (handle, player())  # Adds the client to the list of connected clients
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

    ##### Separating Server-side functions from dealer functions for readability ######

    def construct_deck(self):
        '''This method handles the construction of a new deck of cards.
        Decks are generated pseudo-randomly and currently there is no means by which someone can count cards. In a future
        build of the programme, one area that will be targeted for improvement is to '''
        for card in range(300):  # Our deck will have 300 cards!
            temp = randint(1, 10)
            if temp == 1:
                self.deck.append(card('Ace'))
            else:
                self.deck.append(card(temp))

    def deal_card(self, **kwargs):
        '''This method draws a card and deals it to the recipient'''
        connection = kwargs['conn']
        player = self.clients[connection][1] # This cleans up the code in the rest of the function.

        if len(self.deck) < 1: # We want to have cards to deal!:
            self.construct_deck()

        card = self.deck.pop(0)
        player.cards.append(card) # We add the card to the players hand
        player.total_value += card.value # Updating the total value of the players cards

        self.sock.sendto(str.encode('de&' + card.value), connection) # Send them the card that they've drawn.

        if player.total_value == 21: # The player will automatically stand if the total value is 21...
            self.confirm_stand(21, conn = connection) # This confirms
        elif player.total_value > 21:
            player.bust = True
            self.stand_bust_count += 1


    def store_bet(self, **kwargs):
        '''Accepts the bet from the player and stores the information serverside.'''
        conn = kwargs['conn']
        bet = kwargs['message']
        player = self.clients[conn][1] # Cleans u[ the code.

        player.credits, player.current_bet = player.credits - bet, bet

    def confirm_stand(self, flag = 0, **kwargs):
        '''Confirm that the player has chosen to stand and lck in their current value.'''
        conn = kwargs['conn']

        self.stand_bust_count += 1 # Incrementing our stand and bust tracker by one.
        if flag == 21:
            self.sock.sendto(str.encode('sd&You have a total of 21, as a result you decide to stand. Winnings will be '
                                        + 'paid once a new round starts'))

        elif flag == 'bj':
            self.sock.sendto(str.encode('sd&Joy fills the air. Everything in the casino seems a bit brighter as you realise' +
                                        'that you have hit the big jackpot. BLACKJACK.' +
                                        'The moment passes and you soon realise that... there is no casino. This is an' +
                                        'online game... and the money isn\'t real. Still feels good though doesn\'t it')
                             , conn)

        else: # The player has chosen to stand
            self.sock.sendto(str.encode('sd&The dealer nods, acknowledging your request to stand. Winnings will be payed'
                           + ' out once the round is finished'), conn)











class card(object):
    '''Currently the card object only keeps track of value and cares not about suit but this could easily be written
    into the programme and will be once core functionality is drawn up.'''

    def __init__(self, value):
        if value != 'Ace':
            self.value = value
        else:
            self.value = 1

    def change_ace(self):
        'This changes an ace from high to low or vice versa.'
        if self.value == 1:
            self.value = 11

        elif self.value == 11:
            self.value = 1

        else: # The card is not an ace.
            raise ValueError('The card is not an ace, therefore it\'s value can\'t be changed')





class player(object):
    '''This is a class to handle gamestate/player management from the server server side.'''

    def __init__ (self):
        '''Currently all players will start with the same "slate".'''
        self.cards = () # The card in position 0 is the face down card.
        self.credits = 100
        self.current_bet = 0 # This is a sort of holding pool for the players current bet. The money is taken out of
        # credits.
        self.bust = False # This will change to true if the player has value over 21
        self.stand = False
        self.total_value = 0 # This is the total value of the players cards


def main():
    dealer = CardServer()
    dealer.listen_loop()

main()