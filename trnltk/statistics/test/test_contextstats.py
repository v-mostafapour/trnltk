# coding=utf-8
"""
There is no verification -yet- in test of this class.
The tests are there for making sure there is no run time exceptions
"""
import logging
import os
import unittest
from xml.dom.minidom import parse
import pymongo
from trnltk.morphology.contextfree.parser.parser import ContextFreeMorphologicalParser
from trnltk.morphology.contextfree.parser.rootfinder import WordRootFinder, NumeralRootFinder, ProperNounFromApostropheRootFinder, ProperNounWithoutApostropheRootFinder
from trnltk.morphology.model import formatter
from trnltk.morphology.morphotactics.extendedsuffixgraph import ExtendedSuffixGraph
from trnltk.morphology.morphotactics.predefinedpaths import PredefinedPaths
from trnltk.morphology.lexicon.lexiconloader import LexiconLoader
from trnltk.morphology.lexicon.rootgenerator import RootGenerator, RootMapGenerator
from trnltk.parseset.xmlbindings import ParseSetBinding
from trnltk.statistics.contextstats import NonContextParsingLikelihoodCalculator, ContextParsingLikelihoodCalculator
from trnltk.statistics.contextstats import logger as context_stats_logger
from trnltk.statistics.query import logger as query_logger

dom = parse(os.path.join(os.path.dirname(__file__), 'morphology_contextfree_statistics_sample_parseset.xml'))
parseset = ParseSetBinding.build(dom.getElementsByTagName("parseset")[0])
parse_set_word_list = []
for sentence in parseset.sentences:
    parse_set_word_list.extend(sentence.words)

class LikelihoodCalculatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(LikelihoodCalculatorTest, cls).setUpClass()
        all_roots = []

        lexemes = LexiconLoader.load_from_file(os.path.join(os.path.dirname(__file__), '../../resources/master_dictionary.txt'))
        for di in lexemes:
            all_roots.extend(RootGenerator.generate(di))

        root_map_generator = RootMapGenerator()
        cls.root_map = root_map_generator.generate(all_roots)

        suffix_graph = ExtendedSuffixGraph()
        predefined_paths = PredefinedPaths(cls.root_map, suffix_graph)
        predefined_paths.create_predefined_paths()

        word_root_finder = WordRootFinder(cls.root_map)
        numeral_root_finder = NumeralRootFinder()
        proper_noun_from_apostrophe_root_finder = ProperNounFromApostropheRootFinder()
        proper_noun_without_apostrophe_root_finder = ProperNounWithoutApostropheRootFinder()

        cls.context_free_parser = ContextFreeMorphologicalParser(suffix_graph, predefined_paths,
            [word_root_finder, numeral_root_finder, proper_noun_from_apostrophe_root_finder, proper_noun_without_apostrophe_root_finder])

        mongodb_connection = pymongo.Connection()
        cls.collection_map = {
            1: mongodb_connection['trnltk']['wordUnigrams999'],
            2: mongodb_connection['trnltk']['wordBigrams999'],
            3: mongodb_connection['trnltk']['wordTrigrams999']
        }

        cls.generator = None

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        query_logger.setLevel(logging.INFO)
        context_stats_logger.setLevel(logging.INFO)

    def _test_generate_likelihood(self, surface, leading_context=None, following_context=None):
        assert leading_context or following_context

        leading_context_with_parse_results = [(cw, self.context_free_parser.parse(cw)) for cw in leading_context] if leading_context else []
        following_context_with_parse_results = [(cw, self.context_free_parser.parse(cw)) for cw in following_context] if following_context else []

        likelihoods = []
        results = self.context_free_parser.parse(surface)
        for result in results:
            formatted_parse_result = formatter.format_morpheme_container_for_parseset(result)
            likelihood = 0.0
            if leading_context and following_context:
                likelihood = self.generator.calculate_likelihood(result, leading_context_with_parse_results, following_context_with_parse_results)
            elif leading_context:
                likelihood = self.generator.calculate_oneway_likelihood(result, leading_context_with_parse_results, True)
            elif following_context:
                likelihood = self.generator.calculate_oneway_likelihood(result, following_context_with_parse_results, False)

            likelihoods.append((formatted_parse_result, likelihood))

        for item in likelihoods:
            print item

    def test_generate_likelihood_of_one_word_given_one_leading_context_word(self):
    #        query_logger.setLevel(logging.DEBUG)
    #        context_stats_logger.setLevel(logging.DEBUG)

        context = [u'bir']
        surface = u'erkek'

        self._test_generate_likelihood(surface=surface, leading_context=context, following_context=None)

    def test_generate_likelihood_of_one_word_given_two_leading_context_words(self):
    #        query_logger.setLevel(logging.DEBUG)
    #        context_stats_logger.setLevel(logging.DEBUG)

        context = [u'gençten', u'bir']
        surface = u'erkek'

        self._test_generate_likelihood(surface=surface, leading_context=context, following_context=None)

    def test_generate_likelihood_of_one_word_given_one_following_context_word(self):
    #        query_logger.setLevel(logging.DEBUG)
    #        context_stats_logger.setLevel(logging.DEBUG)

        context = [u'girdi']
        surface = u'erkek'

        self._test_generate_likelihood(surface=surface, leading_context=None, following_context=context)

    def test_generate_likelihood_of_one_word_given_one_context_word(self):
    #        query_logger.setLevel(logging.DEBUG)
    #        context_stats_logger.setLevel(logging.DEBUG)

        leading_context = [u'bir']
        surface = u'erkek'
        following_context = [u'girdi']

        self._test_generate_likelihood(surface=surface, leading_context=leading_context, following_context=following_context)

    def test_generate_likelihood_of_one_word_given_two_context_words(self):
    #        query_logger.setLevel(logging.DEBUG)
    #        context_stats_logger.setLevel(logging.DEBUG)

        leading_context = [u'gençten', u'bir']
        surface = u'erkek'
        following_context = [u'girdi', u'.']

        self._test_generate_likelihood(surface=surface, leading_context=leading_context, following_context=following_context)

class NonContextParsingLikelihoodCalculatorTest(LikelihoodCalculatorTest):
    @classmethod
    def setUpClass(cls):
        super(NonContextParsingLikelihoodCalculatorTest, cls).setUpClass()

        cls.generator = NonContextParsingLikelihoodCalculator(cls.collection_map)

class ContextParsingLikelihoodCalculatorTest(LikelihoodCalculatorTest):
    @classmethod
    def setUpClass(cls):
        super(ContextParsingLikelihoodCalculatorTest, cls).setUpClass()

        cls.generator = ContextParsingLikelihoodCalculator(cls.collection_map)


if __name__ == '__main__':
    unittest.main()
