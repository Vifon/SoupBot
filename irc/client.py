from .message import IRCMessage
from types import SimpleNamespace
from typing import Dict, List, Any, Iterator
import logging
import sqlite3
import time
logger = logging.getLogger(__name__)


class IRCClient:
    def __init__(
            self,
            socket,
            buffer_size=2048,
            encoding='utf-8',
            sqlite_db=':memory:',
            **config,
    ):
        self.socket = socket
        self.buffer_size = buffer_size
        self.encoding = encoding
        self.config = config
        self.logger = logger.getChild(type(self).__name__)
        self.db = sqlite3.connect(
            sqlite_db,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._buffer = bytearray()
        self.plugins = []
        self.shared_data = SimpleNamespace()

    def __iter__(self) -> Iterator[IRCMessage]:
        return self

    def __next__(self) -> IRCMessage:
        return self.recv()

    @property
    def nick(self) -> str:
        # TODO: Return real nick when the nick collisions handling
        # gets implemented, not the one in the config.
        return self.config['nick']

    def recv(self) -> IRCMessage:
        separator = b"\r\n"
        separator_pos = self._buffer.find(separator)
        while separator_pos == -1:
            self._buffer.extend(self.socket.recv(self.buffer_size))
            separator_pos = self._buffer.find(separator)
        msg = self._buffer[:separator_pos].decode(self.encoding)
        self._buffer = self._buffer[separator_pos+len(separator):]
        self.logger.info(">>> %s", repr(msg))
        return IRCMessage.parse(msg)

    def send(self, command: str, *args: str, body: str = None, delay: int = 2):
        msg = IRCMessage(command, *args, body=body)
        self.sendmsg(msg, delay)

    def sendmsg(self, msg: IRCMessage, delay: int):
        self.logger.info("<<< %s", msg)
        self.socket.send(f"{msg}\r\n".encode(self.encoding))
        time.sleep(delay)

    def greet(self):
        self.send(
            "USER", self.config['nick'], "*", "*", body=self.config['name'],
            delay=0,
        )
        self.send('NICK', self.config['nick'], delay=0)
        # TODO: Handle nick collisions.

    def event_loop(self):
        for msg in self:
            for plugin in self.plugins:
                try:
                    if plugin.react(msg):
                        break
                except Exception:
                    self.logger.exception(
                        "%s caused an exception during processing: %s",
                        plugin, repr(msg),
                    )

    def load_plugins(self, plugins: List[str], old_data: Dict[str, Any] = None):
        if old_data is None:
            old_data = {}

        failed_plugins = []

        def load_plugins_helper():
            def load_or_reload(module):
                import importlib
                if old_data:
                    return importlib.reload(importlib.import_module(module))
                else:
                    return importlib.import_module(module)

            for plugin_name in plugins:
                if isinstance(plugin_name, dict):
                    plugin_name, plugin_config = next(iter(plugin_name.items()))
                else:
                    plugin_config = None

                plugin_module, plugin_class = plugin_name.rsplit(".", 1)
                try:
                    plugin = getattr(
                        load_or_reload(plugin_module),
                        plugin_class)(
                            config=plugin_config,
                            client=self,
                            old_data=old_data.get(plugin_class),
                        )
                    yield plugin
                except Exception:
                    self.logger.exception(
                        "%s caused an exception during loading.", plugin
                    )
                    failed_plugins.append(plugin_class)

        self.plugins.extend(load_plugins_helper())
        self.logger.info(
            "Initialized plugins: %s",
            [type(plugin).__name__ for plugin in self.plugins],
        )
        if failed_plugins:
            self.logger.warning("Failed plugins: %s", failed_plugins)


    def unload_plugins(self) -> Dict[str, Any]:
        self.logger.info("Unloading plugins…")
        old_data = vars(self.shared_data)
        self.plugins = []
        self.shared_data = SimpleNamespace()
        return old_data
