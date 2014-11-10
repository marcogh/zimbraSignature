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

    domains = sp.getAllDomains()

    for current_domain in domains:

        logging.debug("Getting all accounts for domain %s" % (current_domain))

        domainusers = sp.getAllAccounts(current_domain)

        for current_user in domainusers:

            logging.debug(
                "Checking, if user %s is active." % (current_user)
            )

            logging.debug(
                "Checking, if user %s has the zimlet configured"\
                 % (current_user)
             )

            # Connect to mailbox service using Administrator accounts

            # Get Mailbox Options from Provisioning

            sai = sp.getAccountInfo(
                AccountBy.name,
                current_user.getMail()
            )

            sa = sp.getAccount(current_user.getMail())

            # Check, wether account is active

            if not sa.isAccountStatusActive():
                logging.info("Account %s is inactive" % (current_user))
                continue

            sa.createSignature('testing',{"zimbraPrefMailSignatureHTML":"<div>ciao</div>"})
            raise IndexError







            dar = sp.delegateAuth(
                AccountBy.name,
                current_user.getMail(),
                60 * 60 * 24
            )

            opt = ZMailbox.Options(
                dar.getAuthToken(),
                sai.getAdminSoapURL()
            )

            mailbox = ZMailbox.getMailbox(opt)

            accountinfo = mailbox.getAccountInfo(True)

            defer_folder_id = None
            defer_tag_id = None

            for key in accountinfo.getZimletProps()[
                "zimbraZimletUserProperties"
            ]:
                if ("de_dieploegers_emaildefer" in key) and\
                   ("deferFolderId" in key):
                    defer_folder_id = key.split(":")[2]
                elif ("de_dieploegers_emaildefer" in key) and\
                   ("deferTagId" in key):
                    defer_tag_id = key.split(":")[2]

            if defer_folder_id != None and defer_tag_id != None:

                logging.info(
                    "Checking for deferred mails of user %s" % (current_user)
                )

                # Check, if folder and tag exist

                if mailbox.getTagById(defer_tag_id) == None:
                    logging.warn(
                        "Tag with ID %s doesn't exist for user %s" %
                        (
                            defer_tag_id,
                            current_user
                        )
                    )

                    continue

                if mailbox.getFolderById(defer_folder_id) == None:
                    logging.warn(
                        "Folder with ID %s doesn't exist for user %s" %
                        (
                            defer_folder_id,
                            current_user
                        )
                    )

                    continue

                # This user is using the defer-zimlet

                searchparams = ZSearchParams(
                    "inid: %s and date:<=+0minute" % (defer_folder_id)
                )

                searchparams.setTypes(ZSearchParams.TYPE_MESSAGE)

                searchparams.setTimeZone(
                    TimeZone.getTimeZone(
                        sa.getPrefTimeZoneId()[0]
                    )
                )

                searchparams.setLimit(9999)

                # Get E-Mails in the defer folder aged today and older

                results = mailbox.search(searchparams)

                if results.getHits().size() > 0:

                    logging.info(
                        "Found %d deferred mails" % (
                            results.getHits().size()
                        )
                    )

                else:

                    logging.info("No mails found")

                for i in range(results.getHits().size()):

                    current_message = results.getHits().get(i).getId()

                    logging.info("Moving message %d" % (i + 1))

                    logging.debug(
                        "Message: %s" % (
                            results.getHits().get(i).dump()
                        )
                    )

                    result = mailbox.moveMessage(
                        current_message,
                        mailbox.getInbox().getId()
                    )

                    logging.info("Marking message as read")

                    result = mailbox.markItemRead(
                        current_message,
                        False,
                        None
                    )

                    logging.info("Tagging message")

                    result = mailbox.tagMessage(
                        current_message,
                        defer_tag_id,
                        True
                    )
