# coding: utf-8
"""

    Use Markov chains to generate random text that sounds Japanese.
    This makes random pronounceable passwords that are both strong and easy
    to memorize.
    
    Of course English or any other language could be used in the sample text.
    
    See more details at http://exyr.org/2011/random-pronounceable-passwords/
    
    Author: Simon Sapin
    License: BSD

"""

from __future__ import division
import string
import itertools
import random
from collections import defaultdict


# This is a romanization of the opening of "Genji Monogatari"
# by Murasaki Shikibu.
# Source: http://etext.lib.virginia.edu/japanese/genji/roman.html
finnish = '''
 Jukolan talo, eteläisessä Hämeessä, seisoo erään mäen pohjoisella rinteellä, liki Toukolan kylää. Sen läheisin ympäristö on kivinen tanner, mutta alempana alkaa pellot, joissa, ennenkuin talo oli häviöön mennyt, aaltoili teräinen vilja. Peltojen alla on niittu, apilaäyräinen, halki-leikkaama monipolvisen ojan; ja runsaasti antoi se heiniä, ennenkuin joutui laitumeksi kylän karjalle. Muutoin on talolla avaria metsiä, soita ja erämaita, jotka, tämän tilustan ensimmäisen perustajan oivallisen toiminnan kautta, olivat langenneet sille osaksi jo ison jaon käydessä entisinä aikoina. Silloinpa Jukolan isäntä, pitäen enemmän huolta jälkeentulevainsa edusta kuin omasta parhaastansa, otti vastaan osaksensa kulon polttaman metsän ja sai sillä keinolla seitsemän vertaa enemmän kuin toiset naapurinsa. Mutta kaikki kulovalkean jäljet olivat jo kadonneet hänen piiristänsä ja tuuhea metsä kasvanut sijaan. - Ja tämä on niiden seitsemän veljen koto, joiden elämänvaiheita tässä nyt käyn kertoilemaan.
Veljesten nimet vanhimmasta nuorimpaan ovat: Juhani, Tuomas, Aapo, Simeoni, Timo, Lauri ja Eero. Ovat heistä Tuomas ja Aapo kaksoispari ja samoin Timo ja Lauri. Juhanin, vanhimman veljen, ikä on kaksikymmentä ja viisi vuotta, mutta Eero, nuorin heistä, on tuskin nähnyt kahdeksantoista auringon kierrosta. Ruumiin vartalo heillä on tukeva ja harteva, pituus kohtalainen, paitsi Eeron, joka vielä on kovin lyhyt. Pisin heistä kaikista on Aapo, ehkä ei suinkaan hartevin. Tämä jälkimmäinen etu ja kunnia on Tuomaan, joka oikein on kuuluisa hartioittensa levyyden tähden. Omituisuus, joka heitä kaikkia yhteisesti merkitsee, on heidän ruskea ihonsa ja kankea, hampunkarvainen tukkansa, jonka karheus etenkin Juhanilla on silmään pistävä.
Heidän isäänsä, joka oli ankaran innokas metsämies, kohtasi hänen parhaassa iässään äkisti surma, kun hän tappeli äkeän karhun kanssa. Molemmat silloin, niin metsän kontio kuin mies, löyttiin kuolleina, toinen toisensa rinnalla maaten verisellä tanterella. Pahoin oli mies haavoitettu, mutta pedonkin sekä kurkku että kylki nähtiin puukon viiltämänä ja hänen rintansa kiväärin tuiman luodin lävistämänä. Niin lopetti päivänsä roteva mies, joka oli kaatanut enemmän kuin viisikymmentä karhua. Mutta näiden metsäretkiensä kautta löi hän laimin työn ja toimen talossansa, joka vähitellen, ilman esimiehen johtoa, joutui rappiolle. Eivät kyenneet hänen poikansakaan kyntöön ja kylvöön; sillä olivatpa he perineet isältänsä saman voimallisen innon metsäotusten pyyntöön. He rakentelivat satimia, loukkuja, ansaita ja teerentarhoja surmaksi linnuille ja jäniksille. Niin viettivät he poikuutensa ajat, kunnes rupesivat käsittelemään tuliluikkua ja rohkenivat lähestyä otsoa korvessa.
'''


def pairwise(iterable):
    """
    Yield pairs of consecutive elements in iterable.
    
    >>> list(pairwise('abcd'))
    [('a', 'b'), ('b', 'c'), ('c', 'd')]
    """
    iterator = iter(iterable)
    try:
        a = iterator.next()
    except StopIteration:
        return
    for b in iterator:
        yield a, b
        a = b


class MarkovChain(object):
    """
    If a system transits from a state to another and the next state depends
    only on the current state and not the past, it is said to be a Markov chain.
    
    It is determined by the probability of each next state from any current
    state.
    
    See http://en.wikipedia.org/wiki/Markov_chain
    
    The probabilities are built from the frequencies in the `sample` chain.
    Elements of the sample that are not a valid state are ignored.
    """
    def __init__(self, sample):
        self.counts = counts = defaultdict(lambda: defaultdict(int))
        for current, next in pairwise(sample):
            counts[current][next] += 1
        
        self.totals = dict(
            (current, sum(next_counts.itervalues()))
            for current, next_counts in counts.iteritems()
        )
        

    def next(self, state):
        """
        Choose at random and return a next state from a current state,
        according to the probabilities for this chain
        """
        nexts = self.counts[state].iteritems()
        # Like random.choice() but with a different weight for each element
        rand = random.randrange(0, self.totals[state])
        # Using bisection here could be faster, but simplicity prevailed.
        # (Also it’s not that slow with 26 states or so.)
        for next_state, weight in nexts:
            if rand < weight:
                return next_state
            rand -= weight
    
    def __iter__(self):
        """
        Return an infinite iterator of states.
        """
        state = random.choice(self.counts.keys())
        while True:
            state = self.next(state)
            yield state

def main():
    chain = MarkovChain(
        c for c in japanese.lower() if c in string.ascii_lowercase
    )
    print ''.join(itertools.islice(chain, 14))

if __name__ == '__main__':
    main()

