import bodystructure
import email.utils, imaplib, re

SIZE_RE = re.compile('RFC822.SIZE (\d+)')
ATTACHMENTS_RE = re.compile(r'(?<="name"\s").+?(?=")')

def parse_bodystructure(data):
    '''parses data from any of the following:
      FETCH BODY
      FETCH BODYSTRUCTURE
      return a list tuples (partnumber, description)
    '''
    return bodystructure.parse_bodystructure(data)

def parse_message(data):
    '''parses data from any of the following:
      FETCH RFC822
      FETCH RFC822.HEADER
      FETCH (BODY[HEADER])
    '''
    return email.message_from_string(data)

def parse_flags(data):
    '''parses FETCH FLAGS'''
    return imaplib.ParseFlags(data)
  
def parse_internaltime(data):
    '''parses FETCH INTERNALTIME
    returns a time tuple'''
    return imaplib.Internaldate2tuple(data)

def parse_fields(data):
    '''parses FETCH (BODY[HEADER.FIELDS (<space separated field-names>)])
    returns a dictionary of fields'''
    return dict([ [j.strip() for j in i.split(':', 1) ] 
        for i in data.strip().split('\r\n') ])

def parse_message_id(data):
    '''returns message number'''
    print 'here', data
    return int(data.split(' ', 1)[0])

def parse_rfc822_size(data):
    return int(SIZE_RE.search(data).group(1))

def get_attachment_names(data):
    '''return a list of names of all email attachments
    parses from any of the following:
      FETCH BODY
      FETCH BODYSTRUCTURE
    '''
    return ATTACHMENTS_RE.findall(data)