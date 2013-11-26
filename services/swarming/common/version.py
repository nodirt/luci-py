# Copyright 2013 The Swarming Authors. All rights reserved.
# Use of this source code is governed by the Apache v2.0 license that can be
# found in the LICENSE file.

"""Version.

Generates the current version of the swarm bot code. Located in the common
directory since it will be run on both the server and the slave bots.
"""


import hashlib
import os

from common import swarm_constants


def GenerateSwarmSlaveVersion(slave_machine_script, start_slave_contents):
  """Returns the SHA1 hash of the swarm slave code, representing the version.

  When run on a slave, this is the currently running version. When run on
  the server it is the version that all slaves should run.

  Args:
    slave_machine_script: The location of slave_machine.py, since its
        location may vary depending if this is run on the server or a slave.
    start_slave_contents: The contents of the start_slave_script. On the server
        it is stored in the database, but it is on disk on the slaves.

  Returns:
    The SHA1 hash of the slave code.
  """
  version_hash = hashlib.sha1()

  version_hash.update(start_slave_contents)

  try:
    with open(slave_machine_script, 'rb') as main_file:
      version_hash.update(main_file.read())

    local_test_runner = os.path.join(swarm_constants.SWARM_ROOT_DIR,
                                     swarm_constants.TEST_RUNNER_DIR,
                                     swarm_constants.TEST_RUNNER_SCRIPT)

    with open(local_test_runner, 'rb') as f:
      version_hash.update(f.read())

    common_dir = os.path.join(swarm_constants.SWARM_ROOT_DIR,
                              swarm_constants.COMMON_DIR)
    for common_file in swarm_constants.SWARM_BOT_COMMON_FILES:
      with open(os.path.join(common_dir, common_file), 'rb') as support_file:
        version_hash.update(support_file.read())
  except IOError:
    # If any files are missing don't worry about it, the version hash will be
    # different so we will get them in the next update.
    pass

  return version_hash.hexdigest()