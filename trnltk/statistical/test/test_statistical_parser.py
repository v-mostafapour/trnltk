# coding=utf-8
import os
import unittest
from xml.dom.minidom import parse
from trnltk.parseset.xmlbindings import ParseSetBinding
from trnltk.statistical.parser import StatisticalParser
from trnltk.morphology.lexiconmodel.lexiconloader import LexiconLoader
from trnltk.morphology.lexiconmodel.rootgenerator import RootGenerator, RootMapGenerator
from trnltk.morphology.morphotactics.extendedsuffixgraph import ExtendedSuffixGraph
from trnltk.morphology.contextfree.parser.parser import ContextFreeMorphologicalParser
from trnltk.morphology.contextfree.parser.lexemefinder import WordLexemeFinder, NumeralLexemeFinder, ProperNounFromApostropheLexemeFinder, ProperNounWithoutApostropheLexemeFinder
from trnltk.morphology.morphotactics.predefinedpaths import PredefinedPaths
from trnltk.treebank.explorer import CompleteWordConcordanceIndex

class StatisticalParserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(StatisticalParserTest, cls).setUpClass()
        all_stems = []

        dictionary_items = LexiconLoader.load_from_file(os.path.join(os.path.dirname(__file__), '../../resources/master_dictionary.txt'))
        for di in dictionary_items:
            all_stems.extend(RootGenerator.generate(di))


        stem_root_map_generator = RootMapGenerator()
        cls.stem_root_map = stem_root_map_generator.generate(all_stems)

        suffix_graph = ExtendedSuffixGraph()
        predefined_paths = PredefinedPaths(cls.stem_root_map, suffix_graph)
        predefined_paths.create_predefined_paths()

        word_stem_finder = WordLexemeFinder(cls.stem_root_map)
        numeral_stem_finder = NumeralLexemeFinder()
        proper_noun_from_apostrophe_stem_finder = ProperNounFromApostropheLexemeFinder()
        proper_noun_without_apostrophe_stem_finder = ProperNounWithoutApostropheLexemeFinder()

        context_free_parser = ContextFreeMorphologicalParser(suffix_graph, predefined_paths,
            [word_stem_finder, numeral_stem_finder, proper_noun_from_apostrophe_stem_finder, proper_noun_without_apostrophe_stem_finder])

        parseset_index = "001"
        dom = parse(os.path.join(os.path.dirname(__file__), '../../testresources/parsesets/parseset{}.xml'.format(parseset_index)))
        parseset = ParseSetBinding.build(dom.getElementsByTagName("parseset")[0])
        parse_set_word_list = []
        for sentence in parseset.sentences:
            parse_set_word_list.extend(sentence.words)

        complete_word_concordance_index = CompleteWordConcordanceIndex(parse_set_word_list)

        cls.parser = StatisticalParser(context_free_parser, complete_word_concordance_index)

    def test_should_parse(self):
        result = self.parser.parse(u'verirsiniz')
        print result.get_parse_results_with_ratio()


if __name__ == '__main__':
    unittest.main()