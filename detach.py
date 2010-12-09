#!/usr/bin/env python
USAGE = 'detach.py [OPTIONS]\nSee RFC3501 for options details.'
__version__ = '''Python IMAP4 attachment tool'''
import pprint
import email, getpass, imaplib, os.path, re, StringIO, sys, time
import parse_fetch
from mail import Mail

class Detach:

    MESSAGE_PARTS = '(RFC822.SIZE BODY[HEADER.FIELDS (FROM DATE SUBJECT)] BODY)'    

    def fetch(self, mesg_nums):
        typ, data = self.mail.send_cmd('FETCH', mesg_nums, self.MESSAGE_PARTS)
        result = [ self.parse(data[i:i+2]) for i in range(0, len(data), 2) ]
        self.mail.verbose(pprint.pformat(result))
        return result

    def connect(self, args):
        if not args.host:
            try:
                from imap_config import HOSTNAME
                args.host = HOSTNAME
            except ImportError:
                args.host = None
        self.mail = Mail(args)
    
    def login(self, username):
        password = None
        if not username:         
            try:
                from imap_config import USERNAME, PASSWORD
                username, password = (USERNAME, PASSWORD)
            except ImportError:
                pass
        self.mail.login(username, password)

    def logout(self):
        self.mail.logout()

    def parse(self, data):
        mesg = parse_fetch.parse_fields(data[0][1])
        mesg['num'] = parse_fetch.parse_message_id(data[0][0])
        mesg['size'] = parse_fetch.parse_rfc822_size(data[0][0])
        mesg['num_attachments'] = len(parse_fetch.get_attachment_names(data[1]))
        return mesg

    def search(self, search_criterion):
        typ, data = self.mail.send_cmd('SEARCH', None, search_criterion)
        mesg_nums = data[0].replace(' ', ',')
        mesg = 'SEARCH returned {0} message(s).\n'
        mesg_count = (arg_nums.count(',') + 1) if mesg_nums else 0
        self.mail.verbose(mesg.format(mesg_count))
        return arg.nums

    def select(self, mailbox='INBOX'):
        typ, data = self.mail.send_cmd('SELECT', mailbox)
        mesg = 'Found {0} message(s) in {1!r}.\n'
        self.mail.verbose(mesg.format(data[0], mailbox))


def main(args):
    mail = Detach()
    mail.connect(args)
    mail.login(args.username)
    mail.select(args.mbox)
    if args.search: arg.nums = mail.search(args.search, args.nums)
    mail.fetch(args.nums)
    mail.logout()      

if __name__ == '__main__':
    from cmd_line_args import Args
    args = Args(USAGE, __version__)
    args.parser.add_argument('--debug', type=int, 
        help='Debug level 1-5')
    args.parser.add_argument('--verbose', action='store_true', 
        help='Disable verbose mode')
    args.parser.add_argument('--host', default=None, 
        help='IMAP server hosname')
    args.parser.add_argument('--username', 
        help='IMAP login name, user@domain')
    args.parser.add_argument('--port', type=int, 
        help='IMAP server port number')
    args.parser.add_argument('--telnet', action='store_true', 
        help='Use telnet instead of SSL')
    args.parser.add_argument('--uid', action='store_true', 
        help='Use UID')
    # -----------------------------------------------------------------------
    args.parser.add_argument('--mbox', default='Inbox', 
        help='Mailbox (folder) to display, default="INBOX"')
    args.parser.add_argument('--search', default=None,
        help='Message search criteria (RFC3501)')
    args.parser.add_argument('-n', '--nums', default='*',
        help='Message numbers (RFC3501)')
    main(args.parse())
