import socket
import threading
import time,
import queue
import re

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

        # Establishing a player class for the dealer. We don't make any modifications to the class but we pretty much
        # ignore anything to do with credits and what not.


        self.print_lock = threading.Lock()
        self.task_queue = queue.Queue()
        self.dealer = player()

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
                decode_data = data.decode('utf-8')\

                # We now add our decoded data to the queue.
                self.task_queue.put((decode_data, addr))
                threading.Thread(target = parser).start() # This launches a new thread.

            except:
                pass
        self.sock.close()

    def parser(self, message):
        '''This method parses incoming messages and takes the appropriate action.

        For a complete breakdown of the Codec visit CodecDescriptions.txt.'''
        decode_data, addr = self.task_queue.get()

        # This is where we split apart our message into its constituent parts.
        pre, null, message = decode_data.partition('&')

        # TODO Does the thread need to some how signal that it has completed it's task.
        try:
            self.dispatch_prefixes[pre](msg=message, conn=addr)
        except KeyError:  # Some other client is trying to connect to the server. This sends a message informing the
            # user to get the proper client
            self.sock.sendto(str.encode('This server only handles BJNet clients. To get a BJNet client visit: ' +
                                        'website.com'), addr)


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

    def shutdown(self, **kargs):
        pass


    def get_userlist(self, **kwargs):
        '''This method gathers all publicly available information about other players and sends it back to the client
        who requested it. '''
        recipient = kwargs['conn']

    def get_playerinfo(self, **kwargs):
        pass

    def new_game(self):
        """ This method begins a new round by ensuring the player list is up to date AND dealing cards/ dealing
        with black jack."""

        # TODO Ensure that dealer and player black-jacks are correctly handled within this method.

    def end_round(self):
        """This method clears the table, pays out bets and begins a timer where players can opt out of playing the
        new game. All players who are in the clients list but haven't opted out are assumed to be connected and the game
        will begin."""

        # First the dealer's hand is dealt with.
        self.deal_server()
        self.pay_winnings_clear_table()

        # TODO To ensure that chat and other such functionality work as intended during these times. The messaging
        # Interface will have to be redesigned.






    def pay_winnings_clear_table(self):

        # We make the rounds of the table paying out winnings to each player.
        # We make use of the for loop to clear the table.

        for client in self.clients:

            if client[1].stand and self.dealer.bust: # If the dealer goes bust, all players not bust win their bet
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(1.25 * client[1].current_bet))
                # TODO communcate the results of this to the players.
            elif client[1].stand and (client[1].total_value > self.dealer.total_value): # Player wins!
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(1.25 * client[1].current_bet))
                # Relay message

            elif client[1].natural and not self.dealer.natural: # Player has black jack
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(2 * client[1].current_bet))
                # Relay message
            elif client[1].natural and self.dealer.natural: # Both player and dealer have black jack
                client[1].current_bet, client[1].credits = 0, (client[1].credits + int(1 * client[1].current_bet))
                # Relay message

            else: # The player has lost in some fashion. either the dealer had a higher hand OR the player went bust.
                client[1].current_bet = 0
                # The message is relayed to the player

            client[1].cards = [] # Cards are returned to the dealer.
            client[1].total_value = 0 # The total value is now zero.
            client[1].bust, client[1].stand, client[1].natural, client[1].aces = False, False, False, False
            # Values are reset.

        # Now we do the same table clear for the dealer.
        self.dealer.cards = []
        self.dealer.total_value = 0
        self.dealer.bust, self.dealer.stand, self.dealer.natural, self.dealer.aces = False, False, False, False









    def broadcast(self, message):
        '''This method broadcasts a server announcement to all players currently in the game. Relay message would be used
        but it is built in a fashion that is a bit too particular to chat messages.'''

    ##### Separating Server-side functions from dealer functions for readability ######

    def construct_deck(self):
        '''This method handles the construction of a new deck of cards.
        Decks are generated pseudo-randomly and currently there is no means by which someone can count cards.
        In a future build of the programme, one area that will be targeted for improvement is to '''
        for card in range(300):  # Our deck will have 300 cards!
            temp = randint(1, 10)
            if temp == 1:
                self.deck.append('Ace')
            else:
                self.deck.append(temp)

    def deal_card(self, **kwargs):
        '''This method draws a card and deals it to the recipient'''
        connection = kwargs['conn']
        player = self.clients[connection][1] # This cleans up the code in the rest of the function.

        if len(self.deck) < 1: # We want to have cards to deal!:
            self.construct_deck()

        new_card = self.deck.pop(0)
        player.cards.append(new_card) # We add the card to the players hand
        player.total_value += new_card # Updating the total value of the players cards

        self.sock.sendto(str.encode('de&' + new_card), connection) # Send them the card that they've drawn.

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

    def deal_server(self):
        '''Once every player has ether chosen to stand or has gone bust, the dealer then deals cards to himself. This
        handles the game logic on the servers end of things. Game logic forv the server works roughly as follows:
        The server will check the total value of it's cards. Dealer stands on soft seventeen. Dealer will stand if
        the total value of their cards is <= 17. Before each turn; the value of the hands will be evaluated with aces
        both high and low. '''
        # TODO The broadcasted messages could be tweaked to come off as more natural sounding in future builds of the
        # TODO programme.
        # Note for future reference. Handling of a dealer black jack is done in the new game method.
        # A soft seventeen however is not.
        dealer = self.dealer # This just simplifies some of the expressions below

        if dealer.natural: # The dealer has blackjack so we don't need to do any of this nonsense.
            return

        if dealer.aces:
            dealer.aces_logic()

        while dealer.total_value < 17:
            if len(self.deck) <= 1:
                self.construct_deck()
            new_card = self.deck.pop(0)
            if new_card == 1: # If an ace is drawn we now know that the player has an ACE!
                dealer.aces = True # In some cases this will be redundant but better be safe than sorry.
                dealer.cards.append(new_card) # Adds the card to the hand.
                self.broadcast("The dealer has drawn an Ace.")
            else: # The dealer not drawn an ace.
                dealer.cards.append(new_card)
                dealer.total_value += new_card
                self.broadcast("The dealer has drawn a " + str(new_card))

            # Now we do ace_logic and broadcast the result to the players.
            if dealer.aces:
                if dealer.aces_logic():
                    self.broadcast("The dealer has elected to keep his ace high and now has a total value of " +
                                   str(dealer.total_value))
                else:
                    self.broadcast("The dealer has elected to keep his ace low and now has a total value of " +
                                   str(dealer.total_value))
            else: # The dealer does not have an ace.
                self.broadcast("This brings the total value of the dealers hand to: " + str(dealer.total_value))

        # Now we broadcast a message that the dealer has either chosen to stand or has gone bust.

        if dealer.total_value <= 21:
            dealer.stand = True # The dealer stands.
            self.broadcast("Since the dealer has a total above seventeen, the dealer has elected to stand. He stands at"
                            + str(dealer.total_value))
        else: # The dealer has gone bust.
            dealer.bust = True
            self.broadcast("LUCKY! The dealer has drawn over 21 and has gone bust. All those with totals under 21 will"
                            + " recieve payouts.")







            # Dealer first handles logic to figure out whether or not they have a more advantageous position with Aces
            # High or Aces Low and makes the necessary changes.





class player(object):
    '''This is a class to handle gamestate/player management from the server server side.'''

    def __init__ (self):
        '''Currently all players will start with the same "slate".'''
        self.cards = [] # The card in position 0 is the face down card.
        self.credits = 100
        self.current_bet = 0 # This is a sort of holding pool for the players current bet. The money is taken out of
        # credits.
        self.bust = False # This will change to true if the player has value over 21
        self.stand = False
        self.natural = False # Boolean tracks whether or not someone has a black jack. Considered in the same way that
        self.aces = False # This is a boolean flag that tracks whether or not there is an ace in the player's hand.
        # stand and bust are used by the programme.
        self.total_value = 0 # This is the total value of the players cards

    def aces_logic(self):
        '''This method handles dealer side logic of whether each individual ace should be high or low. Since no more than
        one ace can be 11 (11+11 equals 22) it basically will determine for the player what the optimal treatment of an
        ace is. And change the values accordingly.

        In addition to modifying the self.cards and self.total_value parameters it will return True if the ace is
        determined to be high and False if it is determined to be low. This is so that certain checks can be done when
        checking for black jack.'''

        # TODO Implement a flagging system for this function call.
        # TODO think about how to return this and integrate it with the possible calling environements.

        # We loop through the cards looking for the first ace. If it's ace high we set it to ace low. This is for
        # simplicity in our code.
        for card, position in enumerate(self.cards):
            if card == 1:
                break  # We only need one ace to flip.
            elif card == 11:
                card = 1
                self.total_value -= 10
                break

        if self.total_value + 10 in range(17, 22):  # Check if ace high is in our optimal range
            self.total_value += 10
            card = 11
            return True  # True refers to the ace being considered high.

        elif self.total_value + 10 <= 16:  # Ace high and low give values within our range. Challenge here is how to
            # handle in the calling environment.
            self.total_value += 10
            card = 11
            return "both"  # This will have to be further evaluated once the calling environment is better defined.
            # The idea here is that we return set ace high but want to return a super position so that the player is
            # informed of both possibilities

        else:
            # we have accounted for all of the situations with ace high. If none of these worked out then we know we
            # want our ace to be low.
            return False  # False refers to the ace NOT being considered high



def main():
    dealer = CardServer()
    dealer.listen_loop()

main()