import string
import sys
import unicodedata
from fast_autocomplete.lfucache import LFUCache

NORMALIZED_CACHE_SIZE = 2048
MAX_WORD_LENGTH = 40

_normalized_lfu_cache = LFUCache(NORMALIZED_CACHE_SIZE)


class Normalizer:

    def __init__(
        self,
        valid_chars_for_string=None,
        valid_chars_for_integer=None,
        valid_chars_for_node_name=None
    ):
        if valid_chars_for_string:
            self.valid_chars_for_string = frozenset(valid_chars_for_string)
        else:
            self.valid_chars_for_string = frozenset(c for c in map(chr, range(sys.maxunicode + 1))
                                                    if unicodedata.category(c).startswith('L'))
        if valid_chars_for_integer:
            self.valid_chars_for_integer = frozenset(valid_chars_for_integer)
        else:
            self.valid_chars_for_integer = frozenset(c for c in map(chr, range(sys.maxunicode + 1))
                                                     if unicodedata.category(c).startswith('N'))
        if valid_chars_for_node_name:
            self.valid_chars_for_node_name = valid_chars_for_node_name
        else:
            self.valid_chars_for_node_name = self._get_valid_chars_for_node_name()

    def _get_valid_chars_for_node_name(self):
        return {' ', '-', ':', '_'} | self.valid_chars_for_string | self.valid_chars_for_integer

    def normalize_node_name(self, name, extra_chars=None):
        if name is None:
            return ''
        name = Normalizer.normalize_unicode(name)[:MAX_WORD_LENGTH]
        key = name if extra_chars is None else f"{name}{extra_chars}"
        result = _normalized_lfu_cache.get(key)
        if result == -1:
            result = self._get_normalized_node_name(name, extra_chars=extra_chars)
            _normalized_lfu_cache.set(key, result)
        return result

    def _remove_invalid_chars(self, x):
        result = x in self.valid_chars_for_node_name
        if x == '-' == self.prev_x:
            result = False
        self.prev_x = x
        return result

    def remove_any_special_character(self, name):
        """
        Only remove invalid characters from a name. Useful for cleaning the user's original word.
        """
        if name is None:
            return ''
        name = Normalizer.normalize_unicode(name)[:MAX_WORD_LENGTH]
        self.prev_x = ''

        return ''.join(filter(self._remove_invalid_chars, name)).strip()

    def _get_normalized_node_name(self, name, extra_chars=None):
        name = name.casefold()
        result = []
        last_i = None
        for i in name:
            if i in self.valid_chars_for_node_name or (extra_chars and i in extra_chars):
                if i == '-':
                    i = ' '
                elif last_i is not None:
                    i_cat = unicodedata.category(i)
                    last_i_cat = unicodedata.category(last_i)
                    if ((i_cat.startswith('N') and last_i_cat.startswith('L')) or
                        (i_cat.startswith('L') and last_i_cat.startswith('N'))):
                        result.append(' ')
                if not(i == last_i == ' '):
                    result.append(i)
                    last_i = i
        return ''.join(result).strip()

    @staticmethod
    def normalize_unicode(text):
        return unicodedata.normalize('NFKC', text)
