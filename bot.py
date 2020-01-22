#!/usr/bin/env python3

from irc.client import IRCClient
import argparse
import logging
import os
import signal
import socket
import ssl
import yaml
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    datefmt="%H:%M"
)


def load_config(path):
    with open(path, 'r') as conf_fd:
        return yaml.safe_load(conf_fd.read())


def live_debug(*ignore):
    import pdb
    pdb.set_trace()
signal.signal(signal.SIGUSR2, live_debug)


def run_bot():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file')
    args = parser.parse_args()

    conf = load_config(args.config_file)
    hostname = conf['server']
    port = conf['port']
    with socket.create_connection((hostname, port)) as sock:
        context = ssl.create_default_context()
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            bot = IRCClient(ssock, **conf['bot'])

            def reload_plugins(*ignore):
                nonlocal conf
                conf = load_config(args.config_file)
                bot.reset_plugin_state()
                bot.load_plugins(conf['plugins'], reload=True)
            signal.signal(signal.SIGUSR1, reload_plugins)
            logger.info(
                f"Use 'kill -SIGUSR1 {os.getpid()}' to reload all plugins."
            )

            bot.greet()
            bot.load_plugins(conf['plugins'])
            bot.event_loop()


if __name__ == '__main__':
    run_bot()
