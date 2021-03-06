# This file is part of Merlin.
# Merlin is the Copyright (C)2008,2009,2010 of Robin K. Hansen, Elliot Rosemarine, Andreas Jacobsen.

# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 
from sys import stdout
from traceback import format_exc
from Core.config import Config
# For email
import socket
from smtplib import SMTP, SMTPException, SMTPSenderRefused, SMTPRecipientsRefused
from ssl import SSLError

CRLF = "\r\n"
encoding = "latin1"

def decode(text):
    # Converts strings to Unicode
    if type(text) is unicode:
        return text
    elif type(text) is str:
        return text.decode(encoding)
    else:
        raise UnicodeError

def encode(text):
    # Converts Unicode to strings
    if type(text) is str:
        return text
    elif type(text) is unicode:
        return text.encode(encoding)
    else:
        raise UnicodeError

def log(filename, log, traceback=True, spacing=True):
    def _log(file):
        file.write(encode(log) + "\n")
        if traceback is True:
            file.write(format_exc() + "\n")
        if spacing is True:
            file.write("\n\n")
    try:
        file = Config.get("Misc", filename)
        if file == "stdout":
            _log(stdout)
        else:
            with open(file, "a") as file:
                _log(file)
    finally:
        if filename == "excalibur":
            if "d" not in Config.get("Misc", "maillogs"):
                return
        elif filename[0] not in Config.get("Misc", "maillogs"):
            return
        if traceback:
            sep = "\n\n" if spacing else "\n"
            log = sep.join([log, format_exc()])
        for addr in Config.get("Misc", "logmail").split():
            send_email("%s: %s" % (Config.get("Connection", "nick"), filename), log, addr)

errorlog = lambda text, traceback=True: log("errorlog", text, traceback=traceback)
scanlog = lambda text, traceback=False, spacing=False: log("scanlog", text, traceback=traceback, spacing=spacing or traceback)
arthurlog = lambda text, traceback=True: log("arthurlog", text, traceback=traceback)
excaliburlog = lambda text, traceback=False, spacing=False: log("excalibur", text, traceback=traceback, spacing=spacing or traceback)

def send_email(subject, message, addr):
    try:
        if (Config.get("smtp", "port") == "0"):
            smtp = SMTP("localhost")
        else:
            smtp = SMTP(Config.get("smtp", "host"), Config.get("smtp", "port"))

        if not ((Config.get("smtp", "host") == "localhost") or (Config.get("smtp", "host") == "127.0.0.1")):
            try:
                smtp.starttls()
            except SMTPException as e:
                raise SMSError("unable to shift connection into TLS: %s" % (str(e),))

            try:
                smtp.login(Config.get("smtp", "user"), Config.get("smtp", "pass"))
            except SMTPException as e:
                raise SMSError("unable to authenticate: %s" % (str(e),))

        try:
             smtp.sendmail(Config.get("smtp", "frommail"), addr, "To:%s\nFrom:%s\nSubject:%s\n%s\n" % (addr, "\"%s\" <%s>" % (
                                                           Config.get("Connection", "nick"), Config.get("smtp", "frommail")), subject, message))
        except SMTPSenderRefused as e:
            raise SMSError("sender refused: %s" % (str(e),))
        except SMTPRecipientsRefused as e:
            raise SMSError("unable to send: %s" % (str(e),))

        smtp.quit()

    except (socket.error, SSLError, SMTPException, SMSError) as e:
        return "Error sending message: %s" % (str(e),)
