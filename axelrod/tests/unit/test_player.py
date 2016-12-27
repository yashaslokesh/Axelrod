import random
import unittest

import axelrod
from axelrod import DefaultGame, Player, simulate_play


C, D = axelrod.Actions.C, axelrod.Actions.D


def cooperate(self):
    return C

def defect(self):
    return D

def randomize(self):
    return random.choice([C, D])



class TestPlayerClass(unittest.TestCase):

    name = "Player"
    player = Player
    classifier = {
        'stochastic': False
    }

    def test_add_noise(self):
        random.seed(1)
        noise = 0.2
        s1, s2 = C, C
        noisy_s1, noisy_s2 = self.player()._add_noise(noise, s1, s2)
        self.assertEqual(noisy_s1, D)
        self.assertEqual(noisy_s2, C)

        noise = 0.9
        noisy_s1, noisy_s2 = self.player()._add_noise(noise, s1, s2)
        self.assertEqual(noisy_s1, D)
        self.assertEqual(noisy_s2, D)

    def test_play(self):
        p1, p2 = self.player(), self.player()
        p1.strategy = cooperate
        p2.strategy = defect
        p1.play(p2)
        self.assertEqual(p1.history[0], C)
        self.assertEqual(p2.history[0], D)

        # Test cooperation / defection counts
        self.assertEqual(p1.cooperations, 1)
        self.assertEqual(p1.defections, 0)
        self.assertEqual(p2.cooperations, 0)
        self.assertEqual(p2.defections, 1)
        # Test state distribution
        self.assertEqual(p1.state_distribution, {(C, D): 1})
        self.assertEqual(p2.state_distribution, {(D, C): 1})

        p1.play(p2)
        self.assertEqual(p1.history[-1], C)
        self.assertEqual(p2.history[-1], D)
        # Test cooperation / defection counts
        self.assertEqual(p1.cooperations, 2)
        self.assertEqual(p1.defections, 0)
        self.assertEqual(p2.cooperations, 0)
        self.assertEqual(p2.defections, 2)
        # Test state distribution
        self.assertEqual(p1.state_distribution, {(C, D): 2})
        self.assertEqual(p2.state_distribution, {(D, C): 2})

    def test_state_distribution(self):
        p1, p2 = self.player(), self.player()
        p1.strategy = randomize
        p2.strategy = randomize
        for h1, h2 in zip([C, C, D, D, C], [C, D, C, D, D]):
            simulate_play(p1, p2, h1, h2)
        self.assertEqual(dict(p1.state_distribution),
                         {(C, C): 1, (C, D): 2, (D, C): 1, (D, D): 1})
        self.assertEqual(dict(p2.state_distribution),
                         {(C, C): 1, (C, D): 1, (D, C): 2, (D, D): 1})

    def test_noisy_play(self):
        random.seed(1)
        noise = 0.2
        p1, p2 = self.player(), self.player()
        p1.strategy = cooperate
        p2.strategy = defect
        p1.play(p2, noise)
        self.assertEqual(p1.history[0], D)
        self.assertEqual(p2.history[0], D)

    def test_strategy(self):
        self.assertRaises(
            NotImplementedError, self.player().strategy, self.player())

    def test_clone(self):
        """Tests player cloning."""
        p1 = axelrod.Random(0.75)  # 0.5 is the default
        p2 = p1.clone()
        turns = 50
        for op in [axelrod.Cooperator(), axelrod.Defector(),
                   axelrod.TitForTat()]:
            p1.reset()
            p2.reset()
            seed = random.randint(0, 10 ** 6)
            for p in [p1, p2]:
                axelrod.seed(seed)
                m = axelrod.Match((p, op), turns=turns)
                m.play()
            self.assertEqual(len(p1.history), turns)
            self.assertEqual(p1.history, p2.history)


def test_responses(test_class, P1, P2, history_1, history_2, responses,
                   random_seed=None, attrs=None):
    """
    Test responses to arbitrary histories. Used for the following tests
    in TestPlayer: first_play_test, markov_test, and responses_test.
    Works for arbitrary players as well. Input response_lists is a list of
    lists, each of which consists of a list for the history of player 1, a
    list for the history of player 2, and a list for the subsequent moves
    by player one to test.
    """

    if random_seed:
        axelrod.seed(random_seed)
    # Force the histories, In case either history is impossible or if some
    # internal state needs to be set, actually submit to moves to the strategy
    # method. Still need to append history manually.
    for h1, h2 in zip(history_1, history_2):
        simulate_play(P1, P2, h1, h2)
    # Run the tests
    for response in responses:
        s1, s2 = simulate_play(P1, P2)
        test_class.assertEqual(s1, response)
    if attrs:
        for attr, value in attrs.items():
            test_class.assertEqual(getattr(P1, attr), value)


class TestOpponent(Player):
    """A player who only exists so we have something to test against"""

    name = 'TestPlayer'
    classifier = {
        'memory_depth': 0,
        'stochastic': False,
        'makes_use_of': None,
        'inspects_source': False,
        'manipulates_source': False,
        'manipulates_state': False
    }

    @staticmethod
    def strategy(opponent):
        return 'C'


class TestPlayer(unittest.TestCase):
    "A Test class from which other player test classes are inherited"
    player = TestOpponent
    expected_class_classifier = None

    def test_initialisation(self):
        """Test that the player initiates correctly."""
        if self.__class__ != TestPlayer:
            player = self.player()
            self.assertEqual(player.history, [])
            self.assertEqual(
                player.match_attributes,
                {'length': -1, 'game': DefaultGame, 'noise': 0})
            self.assertEqual(player.cooperations, 0)
            self.assertEqual(player.defections, 0)
            self.classifier_test(self.expected_class_classifier)

    def test_repr(self):
        """Test that the representation is correct."""
        if self.__class__ != TestPlayer:
            self.assertEqual(str(self.player()), self.name)

    def test_match_attributes(self):
        player = self.player()
        # Default
        player.set_match_attributes()
        t_attrs = player.match_attributes
        self.assertEqual(t_attrs['length'], -1)
        self.assertEqual(t_attrs['noise'], 0)
        self.assertEqual(t_attrs['game'].RPST(), (3, 1, 0, 5))

        # Common
        player.set_match_attributes(length=200)
        t_attrs = player.match_attributes
        self.assertEqual(t_attrs['length'], 200)
        self.assertEqual(t_attrs['noise'], 0)
        self.assertEqual(t_attrs['game'].RPST(), (3, 1, 0, 5))

        # Noisy
        player.set_match_attributes(length=200, noise=.5)
        t_attrs = player.match_attributes
        self.assertEqual(t_attrs['noise'], .5)

    def test_reset(self):
        """Make sure resetting works correctly."""
        p = self.player()
        p_clone = p.clone()
        p2 = axelrod.Random()
        for _ in range(10):
            p.play(p2)
        p.reset()
        self.assertEqual(p.history, [])
        self.assertEqual(self.player().cooperations, 0)
        self.assertEqual(self.player().defections, 0)
        self.assertEqual(self.player().state_distribution, {})

        for k, v in p_clone.__dict__.items():
            self.assertEqual(v, getattr(p_clone, k))

    def test_clone(self):
        # Test that the cloned player produces identical play
        p1 = self.player()
        if str(p1) in ["Darwin", "Human"]:
            # Known exceptions
            return
        p2 = p1.clone()
        self.assertEqual(len(p2.history), 0)
        self.assertEqual(p2.cooperations, 0)
        self.assertEqual(p2.defections, 0)
        self.assertEqual(p2.state_distribution, {})
        self.assertEqual(p2.classifier, p1.classifier)
        self.assertEqual(p2.match_attributes, p1.match_attributes)

        turns = 50
        r = random.random()
        for op in [axelrod.Cooperator(), axelrod.Defector(),
                   axelrod.TitForTat(), axelrod.Random(r)]:
            p1.reset()
            p2.reset()
            seed = random.randint(0, 10 ** 6)
            for p in [p1, p2]:
                axelrod.seed(seed)
                m = axelrod.Match((p, op), turns=turns)
                m.play()
            self.assertEqual(len(p1.history), turns)
            self.assertEqual(p1.history, p2.history)

    def first_play_test(self, play, random_seed=None):
        """Tests first move of a strategy."""
        P1 = self.player()
        P2 = TestOpponent()
        test_responses(
            self, P1, P2, [], [], [play],
            random_seed=random_seed)

    def markov_test(self, responses, random_seed=None):
        """Test responses to the four possible one round histories. Input
        responses is simply the four responses to CC, CD, DC, and DD."""
        # Construct the test lists
        histories = [
            [[C], [C]], [[C], [D]], [[D], [C]],
            [[D], [D]]]
        for i, history in enumerate(histories):
            # Needs to be in the inner loop in case player retains some state
            P1 = self.player()
            P2 = TestOpponent()
            test_responses(self, P1, P2, history[0], history[1], responses[i],
                           random_seed=random_seed)

    def responses_test(self, history_1, history_2, responses, random_seed=None,
                       tournament_length=200, attrs=None):
        """Test responses to arbitrary histories. Input response_list is a
        list of lists, each of which consists of a list for the history of
        player 1, a list for the history of player 2, and a list for the
        subsequent moves by player one to test.
        """
        P1 = self.player()
        P1.match_attributes['length'] = tournament_length
        P2 = TestOpponent()
        P2.match_attributes['length'] = tournament_length
        test_responses(
            self, P1, P2, history_1, history_2, responses,
            random_seed=random_seed, attrs=attrs)

        # Test that we get the same sequence after a reset
        P1.reset()
        P2 = TestOpponent()
        P2.match_attributes['length'] = tournament_length
        test_responses(
            self, P1, P2, history_1, history_2, responses,
            random_seed=random_seed, attrs=attrs)

        # Test that we get the same sequence after a clone
        P1 = P1.clone()
        P2 = TestOpponent()
        P2.match_attributes['length'] = tournament_length
        test_responses(
            self, P1, P2, history_1, history_2, responses,
            random_seed=random_seed, attrs=attrs)

    def classifier_test(self, expected_class_classifier=None):
        """Test that the keys in the expected_classifier dictionary give the
        expected values in the player classifier dictionary. Also checks that
        two particular keys (memory_depth and stochastic) are in the
        dictionary."""
        player = self.player()

        # Test that player has same classifier as it's class unless otherwise
        # specified
        if expected_class_classifier is None:
            expected_class_classifier = player.classifier
        self.assertEqual(expected_class_classifier, self.player.classifier)

        self.assertTrue('memory_depth' in player.classifier,
                        msg="memory_depth not in classifier")
        self.assertTrue('stochastic' in player.classifier,
                        msg="stochastic not in classifier")
        for key in TestOpponent.classifier:
            self.assertEqual(
                player.classifier[key],
                self.expected_classifier[key],
                msg="%s - Behaviour: %s != Expected Behaviour: %s" %
                (key, player.classifier[key], self.expected_classifier[key]))


class TestHeadsUp(unittest.TestCase):
    """Test class for heads up play between two given players."""

    def versus_test(self, player_1, player_2, expected_actions1,
                    expected_actions2, random_seed=None):
        """Tests a sequence of outcomes for two given players."""
        if random_seed:
            random.seed(random_seed)
        # Test sequence of play
        for outcome_1, outcome_2 in zip(expected_actions1, expected_actions2):
            player_1.play(player_2)
            self.assertEqual(player_1.history[-1], outcome_1)
            self.assertEqual(player_2.history[-1], outcome_2)


def test_four_vector(test_class, expected_dictionary):
    """
    Checks that two dictionaries match -- the four-vector defining
    a memory-one strategy and the given expected dictionary.
    """
    P1 = test_class.player()
    for key in sorted(expected_dictionary.keys()):
        test_class.assertAlmostEqual(
            P1._four_vector[key], expected_dictionary[key])
