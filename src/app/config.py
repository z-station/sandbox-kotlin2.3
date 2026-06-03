import os
from os import environ as env
from os.path import join
from tempfile import gettempdir


TIMEOUT = 15  # seconds
SANDBOX_USER_UID = int(env.get('SANDBOX_USER_UID', os.getuid()))
SANDBOX_DIR = env.get('SANDBOX_DIR', gettempdir())
KOTLIN_HOME = env.get('KOTLIN_HOME', '/opt/kotlinc')
KOTLIN_CLASSPATH = ':'.join(
    join(KOTLIN_HOME, 'lib', name)
    for name in (
        'kotlin-stdlib.jar',
        'kotlin-stdlib-jdk8.jar',
        'kotlin-stdlib-jdk7.jar',
    )
)
