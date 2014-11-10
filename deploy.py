# -*- coding: utf-8 -*-
'''
Backend script for the "E-Mail defer"-Zimlet available
at https://github.com/dploeger/zimbra-zimlet-emaildefer

@author: Dennis Ploeger <develop@dieploegers.de>
'''

# Imports

# version 8
#from com.zimbra.client import ZMailbox
#from com.zimbra.common.account.Key import AccountBy
#from com.zimbra.client import ZSearchParams

from com.zimbra.cs.zclient import ZMailbox
from com.zimbra.cs.account.Provisioning import AccountBy
from com.zimbra.cs.zclient import ZSearchParams

from com.zimbra.cs.account.soap import SoapProvisioning

from com.zimbra.common.util import ZimbraLog

from java.util import TimeZone

import logging
from optparse import OptionParser

import ConfigParser

class MyParser(ConfigParser.ConfigParser):

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d

if __name__ == "__main__":

    # Interpret arguments
    config = MyParser()
    config.read('/home/marcogh/zimbraSignature/config.ini')
    confdict = config.as_dict()

    parser = OptionParser(
        usage="Usage: %prog [options] SERVER USERNAME PASSWORD",
        description="SERVER: Name/IP of Zimbra-Server, "
            + "USERNAME: Administrative account username, "
            + "PASSWORD: Password of administrative account"
    )

    parser.add_option(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        help="Be quiet doing things.",
    )

    parser.add_option(
        "-d",
        "--debug",
        action="store_true",
        dest="debug",
        help="Enable debug logging"
    )

    (options, args) = parser.parse_args()

    if (len(args) < 3):
        parser.error("Invalid number of arguments")

    (server_name, admin_account, admin_password) = args

    if options.quiet and options.debug:
        parser.error("Cannot specify debug and quiet at the same time.")

    if options.quiet:
        logging.basicConfig(level=logging.FATAL)
    elif options.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.debug("Starting deferAgent")

    # Configure log4j (mainly to avoid Warnings)

    ZimbraLog.toolSetupLog4jConsole("INFO", True, False)

    # Connect to admin service

    logging.debug(
        "Authenticating against Zimbra-Server %s with user %s" % (
            server_name,
            admin_account
        )
    )

    sp = SoapProvisioning()
    sp.soapSetURI("https://%s:7071/service/admin/soap" % (server_name))

    sp.soapAdminAuthenticate(admin_account, admin_password)

    logging.debug("Fetching all domains")

    for dept in confdict:
        for current_user in eval(confdict[dept]['users']):

            #sai = sp.getAccountInfo(
                            #AccountBy.name,
                            #current_user.getMail())

            sa = sp.getAccount('%s@elmaonline.it' % current_user)
            sa.createSignature('personal_signature',
                    {"zimbraPrefMailSignatureHTML":u"""
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<div class="Section1">
<font size="2" face="Arial">
-- 
<br>
<em>%s</em>
<br>
<strong>%s</strong>
<br>
<a href="mailto:%s" target="_blank">%s</a>
</font>
</div>
<br>

<div class="Section1">
<font face="Arial" size="2">
<strong>ELMA ASCENSORI spa</strong>
<br>
via S. Desiderio, 31
<br>
25020 Flero (BS) Italy <br>
</font>
</div>
<br>

<div class="Section1">
<font face="Arial" size="2">
tel. <a href="callto:+39.0303580936">+39.0303580936</a> - 
fax <a href="callto:+39.0303580190">+39.0303580190</a>
<br>
<a href="mailto:elma@elmaonline.it" target="_blank">elma@elmaonline.it</a> - 
<a href="http://www.elmaonline.it/" target="_blank">www.elmaonline.it</a><br>
<br>
partita IVA IT 03082160171 - codice fiscale 08710640155<br>
reg.imp.CCIAA BS 08710640155 - capitale sociale € 1.060.800 i.v.<br>
</font>
</div>
<br>

<div class="Section1">
<font face="Arial" size="1">
<p style="TEXT-ALIGN: justify">
Le informazioni contenute nella comunicazione che precede possono essere 
riservate e sono, comunque, destinate esclusivamente alla persona o 
all'ente sopraindicati. La diffusione, distribuzione e/o copiatura del 
documento trasmesso da parte di qualsiasi soggetto diverso dal 
destinatario e` proibita. La sicurezza e la correttezza dei messaggi di 
posta elettronica non possono essere garantite. Se avete ricevuto questo
messaggio per errore, Vi preghiamo di contattarci immediatamente. 
Grazie.</p>
<br>
<p style="TEXT-ALIGN: justify">
This communication is 
intended only for use by the addressee. It may contain confidential or 
privileged information. Transmission cannot be guaranteed to be secure 
or error-free. If you receive this communication unintentionally, please
inform us immediately. Thank you.</p>
</div> <!-- -->
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
""" % (sa.getDisplayName(),confdict[dept]['name'],sa.getUnicodeName(),sa.getUnicodeName(),)})


