import collections


def strip_tags(s):
    return re.sub(r'<[^>]*?>', '', s)


def extract_urls(s):
    return re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%['
                      r'0-9a-fA-F][0-9a-fA-F]))+', s)


def convert_to_byte(data, encoding='utf-8'):
    if isinstance(data, basestring):
        return data.encode(encoding) if isinstance(data, unicode) else \
               data
    elif isinstance(data, collections.Mapping):
        return dict(map(convert_to_byte, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert_to_byte, data))
    else:
        return data


def json_dict_unicode_to_bytes(d, encoding='utf-8'):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, unicode):
        return d.encode(encoding)
    elif isinstance(d, dict):
        return dict(imap(json_dict_unicode_to_bytes, iteritems(d), repeat(encoding)))
    elif isinstance(d, list):
        return list(imap(json_dict_unicode_to_bytes, d, repeat(encoding)))
    elif isinstance(d, tuple):
        return tuple(imap(json_dict_unicode_to_bytes, d, repeat(encoding)))
    else:
        return d

def json_dict_bytes_to_unicode(d, encoding='utf-8'):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, bytes):
        return unicode(d, encoding)
    elif isinstance(d, dict):
        return dict(imap(json_dict_bytes_to_unicode, iteritems(d), repeat(encoding)))
    elif isinstance(d, list):
        return list(imap(json_dict_bytes_to_unicode, d, repeat(encoding)))
    elif isinstance(d, tuple):
        return tuple(imap(json_dict_bytes_to_unicode, d, repeat(encoding)))
    else:
        return d



def truncate(value, size=80):
    return value[:size]


def compact(things):
    if isinstance(things, basestring):
        return _compact(things)
    elif isinstance(things, (tuple, list)):
        return [_compact(thing) for thing in things if _compact(thing)]
    else:
        raise Exception('Unsupported type')


def _compact(thing):
    if isinstance(thing, basestring):
        return re.sub(r'\s+', ' ', thing.strip())
    return thing


def get_utf8_value(value):
    if not six.PY2 and isinstance(value, bytes):
        return value

    if not isinstance(value, six.string_types):
        value = six.text_type(value)

    if isinstance(value, six.text_type):
        value = value.encode('utf-8')

    return value


def dedent_initial(s, n=4):
    return s[n:] if s[:n] == ' ' * n else s


def dedent(s, n=4, sep='\n'):
    return sep.join(dedent_initial(l) for l in s.splitlines())


def fill_paragraphs(s, width, sep='\n'):
    return sep.join(fill(p, width) for p in s.split(sep))


def join(l, sep='\n'):
    return sep.join(v for v in l if v)


def ensure_2lines(s, sep='\n'):
    if len(s.splitlines()) <= 2:
        return s + sep
    return s


def abbr(S, max, ellipsis='...'):
    if S is None:
        return '???'
    if len(S) > max:
        return ellipsis and (S[:max - len(ellipsis)] + ellipsis) or S[:max]
    return S


def abbrtask(S, max):
    if S is None:
        return '???'
    if len(S) > max:
        module, _, cls = S.rpartition('.')
        module = abbr(module, max - len(cls) - 3, False)
        return module + '[.]' + cls
    return S


def indent(t, indent=0, sep='\n'):
    """Indent text."""
    return sep.join(' ' * indent + p for p in t.split(sep))


def truncate(s, maxlen=128, suffix='...'):
    """Truncates text to a maximum number of characters."""
    if maxlen and len(s) >= maxlen:
        return s[:maxlen].rsplit(' ', 1)[0] + suffix
    return s


def truncate_bytes(s, maxlen=128, suffix=b'...'):
    if maxlen and len(s) >= maxlen:
        return s[:maxlen].rsplit(b' ', 1)[0] + suffix
    return s


def pluralize(n, text, suffix='s'):
    if n > 1:
        return text + suffix
    return text


def pretty(value, width=80, nl_width=80, sep='\n', **kw):
    if isinstance(value, dict):
        return '{{{0} {1}'.format(sep, pformat(value, 4, nl_width)[1:])
    elif isinstance(value, tuple):
        return '{0}{1}{2}'.format(
            sep, ' ' * 4, pformat(value, width=nl_width, **kw),
        )
    else:
        return pformat(value, width=width, **kw)


def remove_trailing_string(content, trailing):
    """
    Strip trailing component `trailing` from `content` if it exists.
    Used when generating names from view classes.
    """
    if content.endswith(trailing) and content != trailing:
        return content[:-len(trailing)]
    return content


def pretty_name(name):
    """Converts 'first_name' to 'First name'"""
    if not name:
        return ''
    return name.replace('_', ' ').capitalize()


from __future__ import unicode_literals

import re
import unicodedata
from gzip import GzipFile
from io import BytesIO

from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import SimpleLazyObject, allow_lazy
from django.utils.safestring import SafeText, mark_safe
from django.utils.six.moves import html_entities
from django.utils.translation import pgettext, ugettext as _, ugettext_lazy

if six.PY2:
    # Import force_unicode even though this module doesn't use it, because some
    # people rely on it being here.
    from django.utils.encoding import force_unicode  # NOQA


# Capitalizes the first letter of a string.
capfirst = lambda x: x and force_text(x)[0].upper() + force_text(x)[1:]
capfirst = allow_lazy(capfirst, six.text_type)

# Set up regular expressions
re_words = re.compile(r'<.*?>|((?:\w[-\w]*|&.*?;)+)', re.U | re.S)
re_chars = re.compile(r'<.*?>|(.)', re.U | re.S)
re_tag = re.compile(r'<(/)?([^ ]+?)(?:(\s*/)| .*?)?>', re.S)
re_newlines = re.compile(r'\r\n|\r')  # Used in normalize_newlines
re_camel_case = re.compile(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))')


def wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks. Expects that
    existing line breaks are posix newlines.

    All white space is preserved except added line breaks consume the space on
    which they break the line.

    Long words are not wrapped, so the output text may have lines longer than
    ``width``.
    """
    text = force_text(text)

    def _generator():
        for line in text.splitlines(True):  # True keeps trailing linebreaks
            max_width = min((line.endswith('\n') and width + 1 or width), width)
            while len(line) > max_width:
                space = line[:max_width + 1].rfind(' ') + 1
                if space == 0:
                    space = line.find(' ') + 1
                    if space == 0:
                        yield line
                        line = ''
                        break
                yield '%s\n' % line[:space - 1]
                line = line[space:]
                max_width = min((line.endswith('\n') and width + 1 or width), width)
            if line:
                yield line
    return ''.join(_generator())
wrap = allow_lazy(wrap, six.text_type)


class Truncator(SimpleLazyObject):
    """
    An object used to truncate text, either by characters or words.
    """
    def __init__(self, text):
        super(Truncator, self).__init__(lambda: force_text(text))

    def add_truncation_text(self, text, truncate=None):
        if truncate is None:
            truncate = pgettext(
                'String to return when truncating text',
                '%(truncated_text)s...')
        truncate = force_text(truncate)
        if '%(truncated_text)s' in truncate:
            return truncate % {'truncated_text': text}
        # The truncation text didn't contain the %(truncated_text)s string
        # replacement argument so just append it to the text.
        if text.endswith(truncate):
            # But don't append the truncation text if the current text already
            # ends in this.
            return text
        return '%s%s' % (text, truncate)

    def chars(self, num, truncate=None, html=False):
        """
        Returns the text truncated to be no longer than the specified number
        of characters.

        Takes an optional argument of what should be used to notify that the
        string has been truncated, defaulting to a translatable string of an
        ellipsis (...).
        """
        length = int(num)
        text = unicodedata.normalize('NFC', self._wrapped)

        # Calculate the length to truncate to (max length - end_text length)
        truncate_len = length
        for char in self.add_truncation_text('', truncate):
            if not unicodedata.combining(char):
                truncate_len -= 1
                if truncate_len == 0:
                    break
        if html:
            return self._truncate_html(length, truncate, text, truncate_len, False)
        return self._text_chars(length, truncate, text, truncate_len)
    chars = allow_lazy(chars)

    def _text_chars(self, length, truncate, text, truncate_len):
        """
        Truncates a string after a certain number of chars.
        """
        s_len = 0
        end_index = None
        for i, char in enumerate(text):
            if unicodedata.combining(char):
                # Don't consider combining characters
                # as adding to the string length
                continue
            s_len += 1
            if end_index is None and s_len > truncate_len:
                end_index = i
            if s_len > length:
                # Return the truncated string
                return self.add_truncation_text(text[:end_index or 0],
                                                truncate)

        # Return the original string since no truncation was necessary
        return text

    def words(self, num, truncate=None, html=False):
        """
        Truncates a string after a certain number of words. Takes an optional
        argument of what should be used to notify that the string has been
        truncated, defaulting to ellipsis (...).
        """
        length = int(num)
        if html:
            return self._truncate_html(length, truncate, self._wrapped, length, True)
        return self._text_words(length, truncate)
    words = allow_lazy(words)

    def _text_words(self, length, truncate):
        """
        Truncates a string after a certain number of words.

        Newlines in the string will be stripped.
        """
        words = self._wrapped.split()
        if len(words) > length:
            words = words[:length]
            return self.add_truncation_text(' '.join(words), truncate)
        return ' '.join(words)

    def _truncate_html(self, length, truncate, text, truncate_len, words):
        """
        Truncates HTML to a certain number of chars (not counting tags and
        comments), or, if words is True, then to a certain number of words.
        Closes opened tags if they were correctly closed in the given HTML.

        Newlines in the HTML are preserved.
        """
        if words and length <= 0:
            return ''

        html4_singlets = (
            'br', 'col', 'link', 'base', 'img',
            'param', 'area', 'hr', 'input'
        )

        # Count non-HTML chars/words and keep note of open tags
        pos = 0
        end_text_pos = 0
        current_len = 0
        open_tags = []

        regex = re_words if words else re_chars

        while current_len <= length:
            m = regex.search(text, pos)
            if not m:
                # Checked through whole string
                break
            pos = m.end(0)
            if m.group(1):
                # It's an actual non-HTML word or char
                current_len += 1
                if current_len == truncate_len:
                    end_text_pos = pos
                continue
            # Check for tag
            tag = re_tag.match(m.group(0))
            if not tag or current_len >= truncate_len:
                # Don't worry about non tags or tags after our truncate point
                continue
            closing_tag, tagname, self_closing = tag.groups()
            # Element names are always case-insensitive
            tagname = tagname.lower()
            if self_closing or tagname in html4_singlets:
                pass
            elif closing_tag:
                # Check for match in open tags list
                try:
                    i = open_tags.index(tagname)
                except ValueError:
                    pass
                else:
                    # SGML: An end tag closes, back to the matching start tag,
                    # all unclosed intervening start tags with omitted end tags
                    open_tags = open_tags[i + 1:]
            else:
                # Add it to the start of the open tags list
                open_tags.insert(0, tagname)

        if current_len <= length:
            return text
        out = text[:end_text_pos]
        truncate_text = self.add_truncation_text('', truncate)
        if truncate_text:
            out += truncate_text
        # Close any tags still open
        for tag in open_tags:
            out += '</%s>' % tag
        # Return string
        return out


def get_valid_filename(s):
    """
    Returns the given string converted to a string that can be used for a clean
    filename. Specifically, leading and trailing spaces are removed; other
    spaces are converted to underscores; and anything that is not a unicode
    alphanumeric, dash, underscore, or dot, is removed.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = force_text(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)
get_valid_filename = allow_lazy(get_valid_filename, six.text_type)


def get_text_list(list_, last_word=ugettext_lazy('or')):
    """
    >>> get_text_list(['a', 'b', 'c', 'd'])
    'a, b, c or d'
    >>> get_text_list(['a', 'b', 'c'], 'and')
    'a, b and c'
    >>> get_text_list(['a', 'b'], 'and')
    'a and b'
    >>> get_text_list(['a'])
    'a'
    >>> get_text_list([])
    ''
    """
    if len(list_) == 0:
        return ''
    if len(list_) == 1:
        return force_text(list_[0])
    return '%s %s %s' % (
        # Translators: This string is used as a separator between list elements
        _(', ').join(force_text(i) for i in list_[:-1]),
        force_text(last_word), force_text(list_[-1]))
get_text_list = allow_lazy(get_text_list, six.text_type)


def normalize_newlines(text):
    """Normalizes CRLF and CR newlines to just LF."""
    text = force_text(text)
    return re_newlines.sub('\n', text)
normalize_newlines = allow_lazy(normalize_newlines, six.text_type)


def phone2numeric(phone):
    """Converts a phone number with letters into its numeric equivalent."""
    char2number = {'a': '2', 'b': '2', 'c': '2', 'd': '3', 'e': '3', 'f': '3',
         'g': '4', 'h': '4', 'i': '4', 'j': '5', 'k': '5', 'l': '5', 'm': '6',
         'n': '6', 'o': '6', 'p': '7', 'q': '7', 'r': '7', 's': '7', 't': '8',
         'u': '8', 'v': '8', 'w': '9', 'x': '9', 'y': '9', 'z': '9'}
    return ''.join(char2number.get(c, c) for c in phone.lower())
phone2numeric = allow_lazy(phone2numeric)


# From http://www.xhaus.com/alan/python/httpcomp.html#gzip
# Used with permission.
def compress_string(s):
    zbuf = BytesIO()
    zfile = GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(s)
    zfile.close()
    return zbuf.getvalue()


class StreamingBuffer(object):
    def __init__(self):
        self.vals = []

    def write(self, val):
        self.vals.append(val)

    def read(self):
        if not self.vals:
            return b''
        ret = b''.join(self.vals)
        self.vals = []
        return ret

    def flush(self):
        return

    def close(self):
        return


# Like compress_string, but for iterators of strings.
def compress_sequence(sequence):
    buf = StreamingBuffer()
    zfile = GzipFile(mode='wb', compresslevel=6, fileobj=buf)
    # Output headers...
    yield buf.read()
    for item in sequence:
        zfile.write(item)
        data = buf.read()
        if data:
            yield data
    zfile.close()
    yield buf.read()


# Expression to match some_token and some_token="with spaces" (and similarly
# for single-quoted strings).
smart_split_re = re.compile(r"""
    ((?:
        [^\s'"]*
        (?:
            (?:"(?:[^"\\]|\\.)*" | '(?:[^'\\]|\\.)*')
            [^\s'"]*
        )+
    ) | \S+)
""", re.VERBOSE)


def smart_split(text):
    r"""
    Generator that splits a string by spaces, leaving quoted phrases together.
    Supports both single and double quotes, and supports escaping quotes with
    backslashes. In the output, strings will keep their initial and trailing
    quote marks and escaped quotes will remain escaped (the results can then
    be further processed with unescape_string_literal()).

    >>> list(smart_split(r'This is "a person\'s" test.'))
    ['This', 'is', '"a person\\\'s"', 'test.']
    >>> list(smart_split(r"Another 'person\'s' test."))
    ['Another', "'person\\'s'", 'test.']
    >>> list(smart_split(r'A "\"funky\" style" test.'))
    ['A', '"\\"funky\\" style"', 'test.']
    """
    text = force_text(text)
    for bit in smart_split_re.finditer(text):
        yield bit.group(0)


def _replace_entity(match):
    text = match.group(1)
    if text[0] == '#':
        text = text[1:]
        try:
            if text[0] in 'xX':
                c = int(text[1:], 16)
            else:
                c = int(text)
            return six.unichr(c)
        except ValueError:
            return match.group(0)
    else:
        try:
            return six.unichr(html_entities.name2codepoint[text])
        except (ValueError, KeyError):
            return match.group(0)

_entity_re = re.compile(r"&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));")


def unescape_entities(text):
    return _entity_re.sub(_replace_entity, text)
unescape_entities = allow_lazy(unescape_entities, six.text_type)


def unescape_string_literal(s):
    r"""
    Convert quoted string literals to unquoted strings with escaped quotes and
    backslashes unquoted::

        >>> unescape_string_literal('"abc"')
        'abc'
        >>> unescape_string_literal("'abc'")
        'abc'
        >>> unescape_string_literal('"a \"bc\""')
        'a "bc"'
        >>> unescape_string_literal("'\'ab\' c'")
        "'ab' c"
    """
    if s[0] not in "\"'" or s[-1] != s[0]:
        raise ValueError("Not a string literal: %r" % s)
    quote = s[0]
    return s[1:-1].replace(r'\%s' % quote, quote).replace(r'\\', '\\')
unescape_string_literal = allow_lazy(unescape_string_literal)


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = force_text(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
        value = re.sub('[^\w\s-]', '', value, flags=re.U).strip().lower()
        return mark_safe(re.sub('[-\s]+', '-', value, flags=re.U))
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return mark_safe(re.sub('[-\s]+', '-', value))
slugify = allow_lazy(slugify, six.text_type, SafeText)


def camel_case_to_spaces(value):
    """
    Splits CamelCase and converts to lower case. Also strips leading and
    trailing whitespace.
    """
    return re_camel_case.sub(r' \1', value).strip().lower()


def marquee(txt='',width=78,mark='*'):
    """Return the input string centered in a 'marquee'.

    Examples
    --------
    ::

        In [16]: marquee('A test',40)
        Out[16]: '**************** A test ****************'

        In [17]: marquee('A test',40,'-')
        Out[17]: '---------------- A test ----------------'

        In [18]: marquee('A test',40,' ')
        Out[18]: '                 A test                 '

    """
    if not txt:
        return (mark*width)[:width]
    nmark = (width-len(txt)-2)//len(mark)//2
    if nmark < 0: nmark =0
    marks = mark*nmark
    return '%s %s %s' % (marks,txt,marks)


def strip_email_quotes(text):
    """Strip leading email quotation characters ('>').

    Removes any combination of leading '>' interspersed with whitespace that
    appears *identically* in all lines of the input text.

    Parameters
    ----------
    text : str

    Examples
    --------

    Simple uses::

        In [2]: strip_email_quotes('> > text')
        Out[2]: 'text'

        In [3]: strip_email_quotes('> > text\\n> > more')
        Out[3]: 'text\\nmore'

    Note how only the common prefix that appears in all lines is stripped::

        In [4]: strip_email_quotes('> > text\\n> > more\\n> more...')
        Out[4]: '> text\\n> more\\nmore...'

    So if any line has no quote marks ('>') , then none are stripped from any
    of them ::

        In [5]: strip_email_quotes('> > text\\n> > more\\nlast different')
        Out[5]: '> > text\\n> > more\\nlast different'
    """
    lines = text.splitlines()
    matches = set()
    for line in lines:
        prefix = re.match(r'^(\s*>[ >]*)', line)
        if prefix:
            matches.add(prefix.group(1))
        else:
            break
    else:
        prefix = long_substr(list(matches))
        if prefix:
            strip = len(prefix)
            text = '\n'.join([ ln[strip:] for ln in lines])
    return text


def get_text_list(list_, last_sep=' and ', sep=", ", wrap_item_with=""):
    """
    Return a string with a natural enumeration of items

    >>> get_text_list(['a', 'b', 'c', 'd'])
    'a, b, c and d'
    >>> get_text_list(['a', 'b', 'c'], ' or ')
    'a, b or c'
    >>> get_text_list(['a', 'b', 'c'], ', ')
    'a, b, c'
    >>> get_text_list(['a', 'b'], ' or ')
    'a or b'
    >>> get_text_list(['a'])
    'a'
    >>> get_text_list([])
    ''
    >>> get_text_list(['a', 'b'], wrap_item_with="`")
    '`a` and `b`'
    >>> get_text_list(['a', 'b', 'c', 'd'], " = ", sep=" + ")
    'a + b + c = d'
    """
    if len(list_) == 0:
        return ''
    if wrap_item_with:
        list_ = ['%s%s%s' % (wrap_item_with, item, wrap_item_with) for
                 item in list_]
    if len(list_) == 1:
        return list_[0]
    return '%s%s%s' % (
        sep.join(i for i in list_[:-1]),
        last_sep, list_[-1])


def ln(label):
    """Draw a 70-char-wide divider, with label in the middle.

    >>> ln('hello there')
    '---------------------------- hello there -----------------------------'
    """
    label_len = len(label) + 2
    chunk = (70 - label_len) // 2
    out = '%s %s %s' % ('-' * chunk, label, '-' * chunk)
    pad = 70 - len(out)
    if pad > 0:
        out = out + ('-' * pad)
    return out


def safe_str(val, encoding='utf-8'):
    try:
        return str(val)
    except UnicodeEncodeError:
        if isinstance(val, Exception):
            return ' '.join([safe_str(arg, encoding)
                             for arg in val])
        return unicode(val).encode(encoding)


def get_encodings_from_content(content):
    """Returns encodings from given content string.

    :param content: bytestring to extract encodings from.
    """
    warnings.warn((
        'In requests 3.0, get_encodings_from_content will be removed. For '
        'more information, please see the discussion on issue #2266. (This'
        ' warning should only appear once.)'),
        DeprecationWarning)

    charset_re = re.compile(r'<meta.*?charset=["\']*(.+?)["\'>]', flags=re.I)
    pragma_re = re.compile(r'<meta.*?content=["\']*;?charset=(.+?)["\'>]', flags=re.I)
    xml_re = re.compile(r'^<\?xml.*?encoding=["\']*(.+?)["\'>]')

    return (charset_re.findall(content) +
            pragma_re.findall(content) +
            xml_re.findall(content))


def force_decode(string, encoding):
    """Forcibly get a unicode string out of a bytestring."""
    if isinstance(string, binary_type):
        try:
            if encoding:
                string = string.decode(encoding)
            else:
                # try decoding with utf-8, should only work for real UTF-8
                string = string.decode('utf-8')
        except UnicodeError:
            # last resort -- can't fail
            string = string.decode('latin1')
    return string


##


# (c) 2012-2014, Toshio Kuraotmi <a.badger@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.six import string_types, text_type, binary_type, PY3

# to_bytes and to_unicode were written by Toshio Kuratomi for the
# python-kitchen library https://pypi.python.org/pypi/kitchen
# They are licensed in kitchen under the terms of the GPLv2+
# They were copied and modified for use in ansible by Toshio in Jan 2015
# (simply removing the deprecated features)

#: Aliases for the utf-8 codec
_UTF8_ALIASES = frozenset(('utf-8', 'UTF-8', 'utf8', 'UTF8', 'utf_8', 'UTF_8',
    'utf', 'UTF', 'u8', 'U8'))
#: Aliases for the latin-1 codec
_LATIN1_ALIASES = frozenset(('latin-1', 'LATIN-1', 'latin1', 'LATIN1',
    'latin', 'LATIN', 'l1', 'L1', 'cp819', 'CP819', '8859', 'iso8859-1',
    'ISO8859-1', 'iso-8859-1', 'ISO-8859-1'))

# EXCEPTION_CONVERTERS is defined below due to using to_unicode

if PY3:
    basestring = (str, bytes)

def to_unicode(obj, encoding='utf-8', errors='replace', nonstring=None):
    '''Convert an object into a :class:`unicode` string

    :arg obj: Object to convert to a :class:`unicode` string.  This should
        normally be a byte :class:`str`
    :kwarg encoding: What encoding to try converting the byte :class:`str` as.
        Defaults to :term:`utf-8`
    :kwarg errors: If errors are found while decoding, perform this action.
        Defaults to ``replace`` which replaces the invalid bytes with
        a character that means the bytes were unable to be decoded.  Other
        values are the same as the error handling schemes in the `codec base
        classes
        <http://docs.python.org/library/codecs.html#codec-base-classes>`_.
        For instance ``strict`` which raises an exception and ``ignore`` which
        simply omits the non-decodable characters.
    :kwarg nonstring: How to treat nonstring values.  Possible values are:

        :simplerepr: Attempt to call the object's "simple representation"
            method and return that value.  Python-2.3+ has two methods that
            try to return a simple representation: :meth:`object.__unicode__`
            and :meth:`object.__str__`.  We first try to get a usable value
            from :meth:`object.__unicode__`.  If that fails we try the same
            with :meth:`object.__str__`.
        :empty: Return an empty :class:`unicode` string
        :strict: Raise a :exc:`TypeError`
        :passthru: Return the object unchanged
        :repr: Attempt to return a :class:`unicode` string of the repr of the
            object

        Default is ``simplerepr``

    :raises TypeError: if :attr:`nonstring` is ``strict`` and
        a non-:class:`basestring` object is passed in or if :attr:`nonstring`
        is set to an unknown value
    :raises UnicodeDecodeError: if :attr:`errors` is ``strict`` and
        :attr:`obj` is not decodable using the given encoding
    :returns: :class:`unicode` string or the original object depending on the
        value of :attr:`nonstring`.

    Usually this should be used on a byte :class:`str` but it can take both
    byte :class:`str` and :class:`unicode` strings intelligently.  Nonstring
    objects are handled in different ways depending on the setting of the
    :attr:`nonstring` parameter.

    The default values of this function are set so as to always return
    a :class:`unicode` string and never raise an error when converting from
    a byte :class:`str` to a :class:`unicode` string.  However, when you do
    not pass validly encoded text (or a nonstring object), you may end up with
    output that you don't expect.  Be sure you understand the requirements of
    your data, not just ignore errors by passing it through this function.
    '''
    # Could use isbasestring/isunicode here but we want this code to be as
    # fast as possible
    if isinstance(obj, basestring):
        if isinstance(obj, text_type):
            return obj
        if encoding in _UTF8_ALIASES:
            return text_type(obj, 'utf-8', errors)
        if encoding in _LATIN1_ALIASES:
            return text_type(obj, 'latin-1', errors)
        return obj.decode(encoding, errors)

    if not nonstring:
        nonstring = 'simplerepr'
    if nonstring == 'empty':
        return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        try:
            simple = obj.__unicode__()
        except (AttributeError, UnicodeError):
            simple = None
        if not simple:
            try:
                simple = text_type(obj)
            except UnicodeError:
                try:
                    simple = obj.__str__()
                except (UnicodeError, AttributeError):
                    simple = u''
        if isinstance(simple, binary_type):
            return text_type(simple, encoding, errors)
        return simple
    elif nonstring in ('repr', 'strict'):
        obj_repr = repr(obj)
        if isinstance(obj_repr, binary_type):
            obj_repr = text_type(obj_repr, encoding, errors)
        if nonstring == 'repr':
            return obj_repr
        raise TypeError('to_unicode was given "%(obj)s" which is neither'
            ' a byte string (str) or a unicode string' %
            {'obj': obj_repr.encode(encoding, 'replace')})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})

def to_bytes(obj, encoding='utf-8', errors='replace', nonstring=None):
    '''Convert an object into a byte :class:`str`

    :arg obj: Object to convert to a byte :class:`str`.  This should normally
        be a :class:`unicode` string.
    :kwarg encoding: Encoding to use to convert the :class:`unicode` string
        into a byte :class:`str`.  Defaults to :term:`utf-8`.
    :kwarg errors: If errors are found while encoding, perform this action.
        Defaults to ``replace`` which replaces the invalid bytes with
        a character that means the bytes were unable to be encoded.  Other
        values are the same as the error handling schemes in the `codec base
        classes
        <http://docs.python.org/library/codecs.html#codec-base-classes>`_.
        For instance ``strict`` which raises an exception and ``ignore`` which
        simply omits the non-encodable characters.
    :kwarg nonstring: How to treat nonstring values.  Possible values are:

        :simplerepr: Attempt to call the object's "simple representation"
            method and return that value.  Python-2.3+ has two methods that
            try to return a simple representation: :meth:`object.__unicode__`
            and :meth:`object.__str__`.  We first try to get a usable value
            from :meth:`object.__str__`.  If that fails we try the same
            with :meth:`object.__unicode__`.
        :empty: Return an empty byte :class:`str`
        :strict: Raise a :exc:`TypeError`
        :passthru: Return the object unchanged
        :repr: Attempt to return a byte :class:`str` of the :func:`repr` of the
            object

        Default is ``simplerepr``.

    :raises TypeError: if :attr:`nonstring` is ``strict`` and
        a non-:class:`basestring` object is passed in or if :attr:`nonstring`
        is set to an unknown value.
    :raises UnicodeEncodeError: if :attr:`errors` is ``strict`` and all of the
        bytes of :attr:`obj` are unable to be encoded using :attr:`encoding`.
    :returns: byte :class:`str` or the original object depending on the value
        of :attr:`nonstring`.

    .. warning::

        If you pass a byte :class:`str` into this function the byte
        :class:`str` is returned unmodified.  It is **not** re-encoded with
        the specified :attr:`encoding`.  The easiest way to achieve that is::

            to_bytes(to_unicode(text), encoding='utf-8')

        The initial :func:`to_unicode` call will ensure text is
        a :class:`unicode` string.  Then, :func:`to_bytes` will turn that into
        a byte :class:`str` with the specified encoding.

    Usually, this should be used on a :class:`unicode` string but it can take
    either a byte :class:`str` or a :class:`unicode` string intelligently.
    Nonstring objects are handled in different ways depending on the setting
    of the :attr:`nonstring` parameter.

    The default values of this function are set so as to always return a byte
    :class:`str` and never raise an error when converting from unicode to
    bytes.  However, when you do not pass an encoding that can validly encode
    the object (or a non-string object), you may end up with output that you
    don't expect.  Be sure you understand the requirements of your data, not
    just ignore errors by passing it through this function.
    '''
    # Could use isbasestring, isbytestring here but we want this to be as fast
    # as possible
    if isinstance(obj, basestring):
        if isinstance(obj, binary_type):
            return obj
        return obj.encode(encoding, errors)
    if not nonstring:
        nonstring = 'simplerepr'

    if nonstring == 'empty':
        return b''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        try:
            simple = str(obj)
        except UnicodeError:
            try:
                simple = obj.__str__()
            except (AttributeError, UnicodeError):
                simple = None
        if not simple:
            try:
                simple = obj.__unicode__()
            except (AttributeError, UnicodeError):
                simple = b''
        if isinstance(simple, text_type):
            simple = simple.encode(encoding, 'replace')
        return simple
    elif nonstring in ('repr', 'strict'):
        try:
            obj_repr = obj.__repr__()
        except (AttributeError, UnicodeError):
            obj_repr = b''
        if isinstance(obj_repr, text_type):
            obj_repr =  obj_repr.encode(encoding, errors)
        else:
            obj_repr = binary_type(obj_repr)
        if nonstring == 'repr':
            return obj_repr
        raise TypeError('to_bytes was given "%(obj)s" which is neither'
            ' a unicode string or a byte string (str)' % {'obj': obj_repr})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})


# force the return value of a function to be unicode.  Use with partial to
# ensure that a filter will return unicode values.
def unicode_wrap(func, *args, **kwargs):
    return to_unicode(func(*args, **kwargs), nonstring='passthru')


# Alias for converting to native strings.
# Native strings are the default string type for the particular version of
# python.  The objects are called "str" in both py2 and py3 but they mean
# different things.  In py2, it's a byte string like in C.  In py3 it's an
# abstract text type (like py2's unicode type).
#
# Use this when raising exceptions and wanting to get the string
# representation of an object for the exception message.  For example:
#
# try:
#    do_something()
# except Exception as e:
#    raise AnsibleError(to_str(e))
#
# Note that this is because python's exception handling expects native strings
# and doe the wrong thing if given the other sort of string (in py2, if given
# unicode strings, it could traceback or omit the message.  in py3, if given
# byte strings it prints their repr (so the message ends up as b'message').
#
# If you use ansible's API instead of re-raising an exception, use to_unicode
# instead:
#
# try:
#     do_something()
# except Exception as e:
#     display.warn(to_unicode(e))
if PY3:
    to_str = to_unicode
else:
    to_str = to_bytes


def do_title(s):
    """Return a titlecased version of the value. I.e. words will start with
    uppercase letters, all remaining characters are lowercase.
    """
    rv = []
    for item in re.compile(r'([-\s]+)(?u)').split(soft_unicode(s)):
        if not item:
            continue
        rv.append(item[0].upper() + item[1:].lower())
    return ''.join(rv)


def do_truncate(s, length=255, killwords=False, end='...'):
    """Return a truncated copy of the string. The length is specified
    with the first parameter which defaults to ``255``. If the second
    parameter is ``true`` the filter will cut the text at length. Otherwise
    it will discard the last word. If the text was in fact
    truncated it will append an ellipsis sign (``"..."``). If you want a
    different ellipsis sign than ``"..."`` you can specify it using the
    third parameter.

    .. sourcecode:: jinja

        {{ "foo bar baz"|truncate(9) }}
            -> "foo ..."
        {{ "foo bar baz"|truncate(9, True) }}
            -> "foo ba..."

    """
    if len(s) <= length:
        return s
    elif killwords:
        return s[:length - len(end)] + end

    result = s[:length - len(end)].rsplit(' ', 1)[0]
    if len(result) < length:
        result += ' '
    return result + end


def do_wordwrap(environment, s, width=79, break_long_words=True,
                wrapstring=None):
    """
    Return a copy of the string passed to the filter wrapped after
    ``79`` characters.  You can override this default using the first
    parameter.  If you set the second parameter to `false` Jinja will not
    split words apart if they are longer than `width`. By default, the newlines
    will be the default newlines for the environment, but this can be changed
    using the wrapstring keyword argument.

    .. versionadded:: 2.7
       Added support for the `wrapstring` parameter.
    """
    if not wrapstring:
        wrapstring = environment.newline_sequence
    import textwrap
    return wrapstring.join(textwrap.wrap(s, width=width, expand_tabs=False,
                                   replace_whitespace=False,
                                   break_long_words=break_long_words))
