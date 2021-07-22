from sgmllib import SGMLParser, SGMLParseError
import re
from cgi import escape

from .utils import safeToInt
from .safe_html_utils import *

class IllegalHTML(Exception):
    """ Illegal HTML error.
    """

def bodyfinder(text):
    """ Return body or unchanged text if no body tags found.

    Always use html_headcheck() first.
    """
    lowertext = text.lower()
    bodystart = lowertext.find('<body')
    if bodystart == -1:
        return text
    bodystart = lowertext.find('>', bodystart) + 1
    if bodystart == 0:
        return text
    bodyend = lowertext.rfind('</body>', bodystart)
    if bodyend == -1:
        return text
    return text[bodystart:bodyend]


CSS_COMMENT = re.compile(r'/\*.*\*/')
def hasScript(s):
    """Dig out evil Java/VB script inside an HTML attribute.

    >>> hasScript('data:text/html;base64,PHNjcmlwdD5hbGVydCgidGVzdCIpOzwvc2NyaXB0Pg==')
    True
    >>> hasScript('script:evil(1);')
    True
    >>> hasScript('expression:evil(1);')
    True
    >>> hasScript('expression/**/:evil(1);')
    True
    >>> hasScript('http://foo.com/ExpressionOfInterest.doc')
    False
    """
    s = decode_htmlentities(s)
    s = s.replace('\x00', '')
    s = CSS_COMMENT.sub('', s)
    s = ''.join(s.split()).lower()
    for t in ('script:', 'expression:', 'expression(', 'data:'):
        if t in s:
            return True
    return False


CHR_RE = re.compile(r'\\(\d+)')
def unescape_chr(matchobj):
    try:
        return chr(int(matchobj.group(1), 16))
    except ValueError:
        return matchobj.group(0)


def decode_charref(s):
    s = s.group(1)
    try:
        if s[0] in ['x', 'X']:
            c = int(s[1:], 16)
        else:
            c = int(s)
        c = unichr(c)
        if isinstance(s, str):
            c = c.encode('utf8')
        return c
    except ValueError:
        return '&#'+s+';'


def decode_entityref(s):
    s = s.group(1)
    try:
        c = html5entities[s + ';']
    except KeyError:
        try:
            c = html5entities[s]
        except KeyError:
            # strip unrecognized entities
            c = u''
    if isinstance(s, str):
        c = c.encode('utf8')
    return c


CHARREF_RE = re.compile(r"&(?:amp;)?#([xX]?[0-9a-fA-F]+);?")
ENTITYREF_RE = re.compile(r"&(\w{1,32});?")

def decode_htmlentities(s):
    # Decode HTML5 entities (numeric or named).
    s = CHR_RE.sub(unescape_chr, s)
    if '&' not in s:
        return s
    s = CHARREF_RE.sub(decode_charref, s)
    return ENTITYREF_RE.sub(decode_entityref, s)


class StrippingParser(SGMLParser):
    """Pass only allowed tags;  raise exception for known-bad.

    Copied from Products.CMFDefault.utils
    Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
    """

    # This replaces SGMLParser.entitydefs
    entitydefs = html5entities

    def __init__(self, valid, nasty, remove_javascript, raise_error):
        SGMLParser.__init__(self)
        self.result = []
        self.valid = valid
        self.nasty = nasty
        self.remove_javascript = remove_javascript
        self.raise_error = raise_error
        self.suppress = False

    def handle_data(self, data):
        if self.suppress:
            return
        if data:
            self.result.append(escape(data))

    def handle_charref(self, name):
        if self.suppress:
            return
        self.result.append(self.convert_charref(name))

    def handle_comment(self, comment):
        pass

    def handle_decl(self, data):
        pass

    def handle_entityref(self, name):
        if self.suppress:
            return
        self.result.append(self.convert_entityref(name))

    def convert_entityref(self, name):
        if name + ';' in self.entitydefs:
            x = ';'
        elif name in self.entitydefs:
            x = ''
        else:
            x = ';'
        return '&%s%s' % (name, x)

    def convert_charref(self, name):
        return '&#%s;' % name

    def unknown_starttag(self, tag, attrs):
        """ Delete all tags except for legal ones.
        """
        if self.suppress:
            return

        if tag in self.valid:
            self.result.append('<' + tag)

            remove_script = getattr(self, 'remove_javascript', True)

            for k, v in attrs:
                if remove_script and k.strip().lower().startswith('on'):
                    if not self.raise_error:
                        continue
                    else:
                        raise IllegalHTML('Script event "%s" not allowed.' % k)
                elif remove_script and hasScript(v):
                    if not self.raise_error:
                        continue
                    else:
                        raise IllegalHTML('Script URI "%s" not allowed.' % v)
                else:
                    self.result.append(' %s="%s"' % (k, v))

            #UNUSED endTag = '</%s>' % tag
            if safeToInt(self.valid.get(tag)):
                self.result.append('>')
            else:
                self.result.append(' />')
        elif tag in self.nasty:
            self.suppress = True
            if self.raise_error:
                raise IllegalHTML('Dynamic tag "%s" not allowed.' % tag)
        else:
            # omit tag
            pass

    def unknown_endtag(self, tag):
        if tag in self.nasty and not tag in self.valid:
            self.suppress = False
        if self.suppress:
            return
        if safeToInt(self.valid.get(tag)):
            self.result.append('</%s>' % tag)

    def parse_declaration(self, i):
        """Fix handling of CDATA sections. Code borrowed from BeautifulSoup.
        """
        j = None
        if self.rawdata[i:i+9] == '<![CDATA[':
            k = self.rawdata.find(']]>', i)
            if k == -1:
                k = len(self.rawdata)
            j = k+3
        else:
            try:
                j = SGMLParser.parse_declaration(self, i)
            except SGMLParseError:
                j = len(self.rawdata)
        return j

    def getResult(self):
        return ''.join(self.result)


def safe_html(html, valid=VALID_TAGS, nasty=NASTY_TAGS,
              remove_javascript=True, raise_error=True):

    """ Strip illegal HTML tags from string text.
    """
    parser = StrippingParser(valid=valid, nasty=nasty,
                             remove_javascript=remove_javascript,
                             raise_error=raise_error)
    parser.feed(html)
    parser.close()
    return parser.getResult()

