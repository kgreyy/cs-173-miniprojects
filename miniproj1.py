import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(5),
            admin = sp.test_account("admin").address,
            max_tickets = sp.nat(5),
        )

    @sp.entry_point
    def buy_ticket(self, no_tickets):
        sp.set_type(no_tickets, sp.TNat)

        # Sanity checks
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.split_tokens(self.data.ticket_cost, no_tickets, 1), "INVALID AMOUNT")

        # Storage updates
        self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - no_tickets)

        # Return extra tez balance to the sender
        extra_balance = sp.amount - sp.split_tokens(self.data.ticket_cost, no_tickets, 1)
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")
        sp.verify(sp.sender == self.data.admin, "NOT AUTHORISED")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_ticket_cost(self, new_cost):
        sp.set_type(new_cost, sp.TMutez)

        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME HAS ALREADY BEGUN")
        sp.verify(sp.sender == self.data.admin, "NOT AUTHORISED")
        self.data.ticket_cost = new_cost
    
    @sp.entry_point
    def change_max_tickets(self, new_max_tickets):
        sp.set_type(new_max_tickets, sp.TNat)

        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME HAS ALREADY BEGUN")
        sp.verify(sp.sender == self.data.admin, "NOT AUTHORISED")
        self.data.max_tickets = new_max_tickets
        self.data.tickets_available = self.data.max_tickets


@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")
    john = sp.test_account("john")

    # Contract instance
    lottery = Lottery()
    scenario += lottery

    # change_ticket_cost
    scenario.h2("change_ticket_cost")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(sender = admin)
    scenario += lottery.change_ticket_cost(sp.tez(0)).run(sender = alice, valid = False)

    # change_max_tickets
    scenario += lottery.change_max_tickets(10).run(sender = admin)
    scenario += lottery.change_max_tickets(10).run(sender = alice, valid = False)

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(5).run(amount = sp.tez(10), sender = alice)
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(sender = admin, valid = False)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(4), sender = bob)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(4), sender = john)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = charles)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = mike)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(10).run(amount = sp.tez(1), sender = alice, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(1021).run(sender = admin)