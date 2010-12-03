'''Parses IMAP fetch BODYSTRUCTURE results and displays messagae partnumbers
Reference RFC3501
'''
__version__ = '''IMAP BODYSTRUCTURE parser v 0.2

Copyright (C) 2010 Brian Peterson
This is free software; see LICENSE file for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
'''
import re, sys
DBUG = False
if DBUG: from pprint import pprint, pformat
SUBTYPES = ['MIXED', 'MESSAGE', 'DIGEST', 'ALTERNATIVE', 'RELATED',
    'REPORT','SIGNED','ENCRYPTED','FORM DATA']
BODYSTRUCTURE_RE = re.compile('.*\(BODY\w{0,9} (.*)\)')
CONTENT_TYPE_RE = re.compile(r'\s*"(TEXT|APPLICATION|IMAGE|VIDEO|AUDIO)"', re.I)
MULTIPART_SUBTYPE_RE = re.compile('\s*"({0})"'.format('|'.join(SUBTYPES)), re.I)

def parse_bodystructure(string):
    '''Parses IMAP fetch "BODY" or "BODYSTRUCTURE" results
    returns a list of tuples in the format (multipart subtype, depth, text)'''
    match = BODYSTRUCTURE_RE.search(string)
    if not match: 
        mesg = 'WARNING: BODYSTRUCTURE text does not match expected pattern.'
        sys.stderr.write(mesg + '\n')
        return
    body, parts = (match.group(1), [])
    if DBUG: print '\nBODY:\n', body
    for multipart_subtype, depth, text in parse_parts(string):
        if DBUG: print '{0}\n'.format(pformat((multipart_subtype, depth, text)))
        if multipart_subtype:
            i = len(parts) - 1
            while (i >= 0) and (depth < parts[i]): i -= 1
            parts.insert(i + 1, (depth - 1, multipart_subtype))
        if CONTENT_TYPE_RE.match(text):
            parts.append((depth, text))
    return add_part_nums(parts)

def parse_parts(string):
    '''Nested parenthese text generator, yields (depth, text)'''
    open_paren_pos = []
    for ch_pos, char in enumerate(string):
        if char == '(':
            open_paren_pos.append(ch_pos)
        elif char == ')':
            start_pos = open_paren_pos.pop()
            text = string[ start_pos + 1: ch_pos]
            depth = len(open_paren_pos)
            match = MULTIPART_SUBTYPE_RE.match(string[ch_pos + 1:])
            multipart_subtype = match.group(1) if match else ''
            yield (multipart_subtype, depth, text)

def add_part_nums(parts):
    if DBUG: print '\nPARTS:\n{0}\n'.format(pformat(parts))
    result = []
    partnums = [0] * max(parts)[0]
    get_part_str = lambda x, y, z: '{0}{1}{2}{3}'.format(
        '\t'*(x - 1), y, ' '*(y!=''), z)
    for depth, text in parts:
        partnum, is_multipart = ('', (text.upper() in SUBTYPES))
        if depth > 1:
            partnums[depth - 2] += 1
            partnum = '.'.join([ str(i) for i in partnums[:depth - 1] ])
        if is_multipart: text = 'MULTIPART/' + text.upper()
        result.append(get_part_str(depth, partnum, text))
    return result

if __name__ == '__main__':
    # Sample Usage
    body = '3 (BODY (((("TEXT" "PLAIN"  ("charset" "US-ASCII") NIL NIL "QUOTED-PRINTABLE" 2210 76)("TEXT" "HTML"  ("charset" "US-ASCII") NIL NIL "QUOTED-PRINTABLE"3732 99) "ALTERNATIVE")("IMAGE" "GIF"  ("name" "pic00041.gif") "<2__=07BBFD03DDC66BF58f9e8a93@domain.org>" NIL "BASE64" 1722)("IMAGE" "GIF"  ("name" "ecblank.gif") "<3__=07BBFD43DFC66BF58f9e8a93@domain.org>" NIL "BASE64" 64) "RELATED")("APPLICATION" "PDF"  ("name" "Quote_VLQ5069.pdf") "<1__=07BBED03DFC66BF58f9e8a93@domain.org>" NIL "BASE64" 59802) "MIXED"))'
    parts = parse_bodystructure(body)
    if parts:
        for i in parts:
            print i

"""Sample Output:
MULTIPART/MIXED
        1 MULTIPART/RELATED
                1.1 MULTIPART/ALTERNATIVE
                        1.1.1 "TEXT" "PLAIN"  ("charset" "US-ASCII") NIL NIL "QUOTED-PRINTABLE" 2210 76
                        1.1.2 "TEXT" "HTML"  ("charset" "US-ASCII") NIL NIL "QUOTED-PRINTABLE"3732 99
                1.2 "IMAGE" "GIF"  ("name" "pic00041.gif") "<2__=07BBFD03DDC66BF58f9e8a93@domain.org>" NIL "BASE64" 1722
                1.3 "IMAGE" "GIF"  ("name" "ecblank.gif") "<3__=07BBFD43DFC66BF58f9e8a93@domain.org>" NIL "BASE64" 64
        2 "APPLICATION" "PDF"  ("name" "Quote_VLQ5069.pdf") "<1__=07BBED03DFC66BF58f9e8a93@domain.org>" NIL "BASE64" 59802
"""
