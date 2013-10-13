# General
import glob
import json
import os
import shlex
import socket
import subprocess
import sys

# Plugin superclass
from rpcdaemon.lib.plugin import Plugin


# Glance image sync handler
class ImageSync(Plugin):
    def __init__(self, connection, config, handler=None):
        # Initialize base Plugin
        Plugin.__init__(self, connection, config, handler)

        # Store glance data dir
        self.datadir = self.pconfig['filesystem_store_datadir']

    def update(self, body, message):
        self.logger.debug(json.dumps(body, indent=2, sort_keys=True))

        # Check the type of event
        event = body['event_type']
        if event in ['image.update', 'image.delete']:
            # Extract pieces
            payload = body['payload']
            host = body['publisher_id']
            image = os.path.join(self.datadir, payload['id'])

            # Got an image update from someone besides me?
            if event == 'image.update' and host != socket.gethostname():
                self.logger.info(
                    'Update detected on %s. Syncing image %s' % (
                        host,
                        image
                    )
                )
                # Rsync image
                subprocess.call(
                    shlex.split(
                        # Rsync with quiet/compression
                        'rsync -qzae "ssh -o StrictHostKeyChecking=no"'
                        '%s@%s:%s %s' % (
                            self.config['rsync_user'],
                            host,
                            image,
                            image
                        )
                    ),
                    # Log output if any
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
            # Maybe deleted instead?
            elif event == 'image.delete':
                self.logger.info(
                    'Delete detected on %s. Removing image %s' % (
                        host,
                        image
                    )
                )
                # Temp file glob from rsync still in progress
                temp = os.path.join(self.datadir, '.*%s*' % payload['id'])

                # No temp file?
                if not glob.glob(temp):
                    # Safe to delete image
                    os.remove(image)

        # ACK message in any case
        message.ack()
