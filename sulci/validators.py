# -*- coding: utf-8 -*-

"""
Validate algorythm output.
"""
import os

from sulci.base import TextManager
from sulci.utils import load_file
from sulci.textmining import SemanticalTagger
from sulci.log import sulci_logger


class BaseValidator(TextManager):

    VALID_EXT = None
    PATH = None
    SEPARATOR = u"—"

    def do(self):
        files = self.get_files(self.VALID_EXT)
        score = 0
        for f in files:
            sulci_logger.info(" ******* File %s *******" % f, "CYAN", True)
            score += self.validate_file(f)
        sulci_logger.info(" ########## Final score ########## ", "CYAN", True)
        sulci_logger.info(score, "RED", True)

    def validate_file(self, filepath):
        # must return a tuple (true_positives, false_positives, false_negatives)
        raise NotImplementedError()

    def split_file_content(self, filepath):
        raw_content = load_file(os.path.join(self.PATH, filepath))
        raw_output, text_content = raw_content.split(self.SEPARATOR)
        text_content = text_content.strip()
        raw_output = self.split_raw_output(raw_output)
        return raw_output, text_content

    def split_raw_output(self, raw_ouput):
        def is_valid(line):
            return line and not line.startswith("#")
        lines = [line for line in raw_ouput.splitlines() if is_valid(line)]
        return lines

    def compare_lists(self, valids, candidates):
        false_negatives = []
        false_positives = []
        true_positives = []
        sulci_logger.info("Expected", "YELLOW", True)
        sulci_logger.info(valids)
        sulci_logger.info("Output", "YELLOW", True)
        sulci_logger.info(candidates)
        for e in candidates[:]:  # Make a copy, to be able to modify it
            if e in valids:
                true_positives.append(e)
            else:
                false_negatives.append(e)
            candidates.remove(e)
        false_positives = candidates
        sulci_logger.info("True positives", "YELLOW", True)
        sulci_logger.info(true_positives, "BLUE")
        sulci_logger.info("False positives", "YELLOW", True)
        sulci_logger.info(false_positives, "RED")
        sulci_logger.info("False negatives", "YELLOW", True)
        sulci_logger.info(false_negatives, "RED")
        score = 1.0 * (len(false_positives) + len(false_negatives)) / len(valids) * -1
        sulci_logger.info("Score", "YELLOW", True)
        sulci_logger.info(score, "RED", True)
        return score


class KeyEntityValidator(BaseValidator):
    """
    Validate key entities extraction.
    """

    VALID_EXT = ".kev"
    PATH = "corpus"

    def validate_file(self, filepath):
        raw_output, text_content = self.split_file_content(filepath)
        S = SemanticalTagger(text_content)
        flat_output = []
        for ke in S.keyentities:
            flat_output.append(
                " ".join(stemm.main_occurrence.lemme for stemm in ke)
            )
        return self.compare_lists(raw_output, flat_output)
