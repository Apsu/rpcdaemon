# General
from glob import glob
from os import remove, system
from socket import gethostname

# Plugin superclass
from rpcdaemon.lib.plugin import Plugin

# Glance image sync handler
class ImageSync(Plugin):
    def __init__(self, connection, config, handler=None):
        # Initialize base Plugin
        Plugin.__init__(self, self.__name__, connection, config, handler)

        # Store glance data dir
        self.datadir = self.pconfig['filesystem_store_datadir']

    def update(self, body, message):
        # Extract pieces
        payload = body['payload']
        image = "%s/%s" % (self.datadir, payload['id'])
        event = body['event_type']
        host = body['publisher_id']

        # Got an image update from someone besides me?
        if event == 'image.update' and host != gethostname():
            self.logger.info(
                'Update detected on %s. Syncing image %s' % (
                    host, image
                )
            )
            # Rsync image
            system(
                'rsync -ae "ssh -o StrictHostKeyChecking=no"'
                '%s@%s:%s %s' % (self.config['rsync_user'], host, image, image)
            )
        # Maybe deleted instead?
        elif event == 'image.delete':
            self.logger.info(
                'Delete detected on %s. Removing image %s' % (
                    host, image
                )
            )
            # Temp file glob from rsync still in progress
            temp = '%s/.*%s*' % (self.datadir, payload['id'])

            # No temp file?
            if not glob(temp):
                # Safe to delete image
                remove(image)

        # ACK message in any case
        message.ack()
