USAGE = 'imaplive.py [OPTIONS]'
__version__ = '''Python-based IMAP4 Command-line Interface

Copyright (C) 2010 Brian Peterson, Jeremy Dye
This is free software; see LICENSE file for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Future:
1 . Fetch # args issue, need to check for <#.#> to determine if it is a partial fetch
'''
import imaplib, email
import csv, getpass, pprint, re, socket, sys

__all__ = ['Mail']

class Mail:
    
    last_state = None
    last_untagged_responses = {}
    LINE_SEP = '=' * 78 + '\n'

    def __init__(self, args):
        self.args = args
        imaplib.Debug = args.debug
        self.connect(args.host, args.port, args.telnet)

    def connect(self, host, port=None, telnet=False):
        if not port: 
            port = imaplib.IMAP4_PORT if telnet else imaplib.IMAP4_SSL_PORT  
        imap_obj = 'IMAP4' if telnet else 'IMAP4_SSL'
        s = 'imaplib.{0}({1!r}, {2})\n'
        self.verbose(s.format(imap_obj, host, port))
        self.verbose(self.LINE_SEP)
        try:
            self.imap = getattr(imaplib, imap_obj)(host, port)
        except socket.error as err_mesg:
            mesg = 'ERROR: Unable to connect to server "{0}".\n'
            mesg = mesg.format(host) + str(err_mesg) + '\n'
            self.cmd_failed(mesg, abort=True)
        self.show_imap_attr('welcome')
        self.show_imap_attr('capabilities')
        self.show_imap_attr('PROTOCOL_VERSION')    
        self.show_cmd_results()

    def login(self, username, password=None):
        if not password: password = getpass.getpass()
        mesg = '\nIMAP4.login("{1}", <password>)\n{0}'
        self.verbose(mesg.format(self.LINE_SEP, username))
        try:
            result = self.imap.login(username, password)[0]
        except imaplib.IMAP4.error as err_mesg:
            self.cmd_failed(str(err_mesg))
        else:
            self.show_cmd_results(result)

    def logout(self):
        if hasattr(self, 'imap'): 
            if self.imap.state == 'SELECTED':
                self.send_cmd('close')
            if self.imap.state == 'AUTH' :
                self.send_cmd('logout')
        sys.exit(0)
 
    def send_cmd(self, cmd, *args):
        arg_str = ', '.join([ '{0!r}'.format(i) for i in args ]) if args \
            else ''
        mesg = '\nIMAP4.{1}({2})\n{0}'
        self.verbose(mesg.format(self.LINE_SEP, cmd, arg_str))
        try:
            data = getattr(self.imap, cmd)(*args)
        except (imaplib.IMAP4.error, imaplib.IMAP4.readonly) as err_mesg:
            return self.cmd_failed(str(err_mesg) + '\n')
        except (imaplib.IMAP4.abort, socket.error) as err_mesg:
            self.cmd_failed(str(err_mesg) + '\n', abort=True)
        if self.args.verbose:
            self.show_cmd_results(cmd, data)
        return data

    # --- PARSE METHODS ---
    
    def parse_data(self, data, command):
        typ, data = data
        cmd, args = command
        if typ != 'OK' or cmd not in ['FETCH', 'UID']: return
        if cmd == 'UID': cmd, args = args.split(' ', 1)
        args = args.split(' ')
        if args == 'FLAGS':
            data = imaplib.ParseFlags(data)
        print 'typ, data = {0}'.format(pprint.pformat([typ, data]))

    # --- DISPLAY METHODS ---
    
    def get_changed_items(self, x, y):
        '''returns items in dict x that do not match dict y'''
        xkeys, ykeys = (set(x.keys()), set(y.keys()))
        new_keys = [ x[i] for i in xkeys.difference(ykeys) ]
        changed_keys = [ x[i] for i in xkeys.intersection(ykeys) 
            if x[i] != y[i] ]
        return new_keys + changed_keys

    def show_cmd_results(self, command=None, data=None, parse_data=None):
        if self.args.verbose:
            if (self.last_state != self.imap.state): self.show_state()
            changed_items = self.get_changed_items(
                self.imap.untagged_responses, self.last_untagged_responses)
            if changed_items: 
                mesg = 'IMAP4.untagged_responses = {0}'
                print mesg.format(pprint.pformat(changed_items))
                self.last_untagged_responses = self.imap.untagged_responses
        if data:
            if parse_data:
                self.parse_data(data, command)
            else:
                print 'typ, data = {0}'.format(pprint.pformat(data))

    def show_state(self):
        self.show_imap_attr('state')
        self.last_state = self.imap.state
               
    def show_imap_attr(self, attr):
        value = getattr(self.imap, attr)
        if value:
            self.verbose('IMAP4.{0} = {1!r}\n'.format(attr, value))

    def verbose(self, mesg):
        if self.args.verbose: sys.stdout.write(mesg)

    def cmd_failed(self, err_mesg, abort=False):
        sys.stderr.write(err_mesg)
        if abort:
            self.logout()
            sys.exit(1)

def parse_special(command, args, is_uid):
    if command == 'EXAMINE':
        command = 'SELECT' # use 'select' to execute examine command
        args.append(True)  # set 'select' readonly flag
    elif command == 'FETCH':
        # check message-parts string for <start.length> octet specifier
        match = re.search('<(\d+)\.(\d+)>', args[1])
        if match:
            command = 'FETCH_PARTIAL'
            args += match.groups()
    return ('UID', [command] + args) if is_uid else (command, args)

def parse_command(cmd):
    '''Returns (command, args...)'''
    cmd = list(csv.reader([cmd.strip().replace(' ', ',')]))[0]
    idx = lambda x: min(x, len(cmd))
    command = cmd[0].upper()
    is_uid, is_parse = (command == 'UID', command == 'PARSE')
    if is_uid or is_parsed: command, cmd = (cmd[idx(1)], cmd[idx(2):])
    if command in COMMANDS:
        args, ARGS = (None, COMMANDS[command][0])
        num_args = idx(len(ARGS))
        if num_args:
            args = cmd[1:num_args] + [' '.join(cmd[num_args:])]
            args = [ i.replace(',', ' ') for i in args ]
        required_args = [ '{0!r}'.format(i) for i in ARGS if i[0] != '[' ]
        if len(args) >= len(required_args): 
            return (parse_special(command, args, is_uid), is_parse)
        mesg = 'ERROR: {0} requires the following arguments... {1}.\n'
        sys.stderr.write(mesg.format(command, ', '.join(required_args))) 
    else:
        mesg = 'ERROR: {0} is not a supported command.\n'
        sys.stderr.write(mesg.format(command))
    return (None, None)

def main(args):
    from imapcmds import *
    
    mail = Mail(args)
    while 1:
        user_input = raw_input('>>> ')
        if not user_input: break
        command, args, parse_data = parse_command(user_input)
        if command == 'LOGIN': 
            mail.login(args[0])
        elif command == 'LOGOUT': 
            mail.logout()
        elif command: 
            mail.send_cmd(command, *args)
            self.show_cmd_results((cmd, args), data, parse_data)

if __name__ == '__main__':
    from cmd_line_args import Args
    args = Args(USAGE, __version__)
    args.parser.add_argument('--debug', type=int, 
        help='Debug level 1-5')
    args.parser.add_argument('--verbose', action='store_true', default=False, 
        help='Disable verbose mode')
    args.parser.add_argument('--host', default='localhost', 
        help='IMAP server hostanme')
    args.parser.add_argument('--port', type=int, 
        help='IMAP server hostanme')
    args.parser.add_argument('--telnet', action='store_true', 
        help='Use telnet instead of SSL')
    args.parser.add_argument('--uid', action='store_true', 
        help='Use UID')
    main(args.parse())
