"""This is a tester script meant to try to reproduce an error in the server code where the new game function exits
prematurely. This programme is not server based, though it is built to interact with the user in a similar manner to the server.
In terms of its data structures, it is designed to be very similar to the main server progrmme but most operations are
dummy operations only meant to simulate the rough programme flow of the main server."""

import threading
import queue
import re

from copy import deepcopy

class Dealer(object):
    """This class is meant to emulate the CardServer class of the server programme. It only has methods
    defined for accepting 'bets' and creating new games... It also has a decoder method defined."""

    def __init__(self):
        "Initialises a Dealer Object!"

        self.clients = {'1': ("User", Player())}  # Structure meant to emulate a one player game.
        self.new_friends = {}  # Incase the user doesn't bet they are placed here.

        # Now we establish our dispatch prefixes
        self.dispatch_prefixes = {'be': self.process_bet, 'ng': self.new_round}

        # Just to be safe I'm going to throw in two of our game states.
        self.new_game = False
        self.game_time = False

        # Now we establish our task queue.v
        self.task_queue = queue.Queue()


    def parser(self, message):
        "This parses out a message and passes it to the appropriate function"
        while True:
            pre, null, message = message.partition('&')  # Splitting out the message from its prefix.

            try:
                self.dispatch_prefixes[pre](msg=message)
            except KeyError: # This should ONLY be raised if... and only if we get a key error from reading dispatch
                # prefixes.
                print("Key Error Exception Raised!")

    def process_bet(self, **kwargs):
        "Basically it stores a number in the player class. That's all."
        bet = kwargs["msg"]
        self.clients['1'][1].bet = True # A flag signalling the player has bet.
        self.clients['1'][1].wager = bet
        print("The bet of" + str(bet) + "has been stored!")

    def new_round(self):
        """A method meant to set up the game table. In this case it handles taking bets and then tries to deal a card to
        those who made a bet otherwise it stores them in new friends."""

        print("Bet Now")
        while not self.clients['1'][1].bet:
            pass
        print("Bets have been collected")

        # Now we get to the problem area
        for player in self.clients.values():
            if player[1].wager == 0:
                self.new_friends[player] = deepcopy(self.clients[player])  # This perhaps is causing a key error?
                del self.clients[player]
                print("No Bet")
            else:
                print("Player would be dealt into the game.")

        return

class Player(object):
    """Thiis class is a simplified version of the server-side player function."""
    def __init__(self):
        self.bet = False
        self.wager = 0


def encoder(message,):

    global dealer
    """This takes a message from the main loop and attatches a prefix on it. It then hands it back to the main loop
    Prefixes are as detailed in the main documentation for BJNet."""
    encodings = [(re.compile('^/bet', re.I),'be&'),(re.compile('^/force', re.I), 'ng&')]

    pre, null, message = message.partition(" ")
    for regex_tuple in encodings:
        if regex_tuple[0].fullmatch(pre):
            pre = regex_tuple[1]
    dealer.parser(pre + message)  # Now we parse that message!


def main_loop():
    # Now we get the message and pass it to the encoder.
    while True:
        message = input('\n> ')
        threading.Thread(target = encoder, args = message).start()
    # Main loop will call the parser method directly based on a given input.


# Globals are bad
dealer = Dealer()
main_loop()