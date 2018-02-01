# Copyright (c) 2018  gevent contributors. See LICENSE for details.

from _socket import gaierror
from _socket import error
from _socket import getservbyname
from _socket import getaddrinfo

from gevent._compat import string_types
from gevent._compat import integer_types

from gevent.socket import SOCK_STREAM
from gevent.socket import SOCK_DGRAM
from gevent.socket import SOL_TCP
from gevent.socket import AI_CANONNAME
from gevent.socket import EAI_SERVICE
from gevent.socket import AF_INET
from gevent.socket import AI_PASSIVE


def _lookup_port(port, socktype):
    # pylint:disable=too-many-branches
    socktypes = []
    if isinstance(port, string_types):
        try:
            port = int(port)
        except ValueError:
            try:
                if socktype == 0:
                    origport = port
                    try:
                        port = getservbyname(port, 'tcp')
                        socktypes.append(SOCK_STREAM)
                    except error:
                        port = getservbyname(port, 'udp')
                        socktypes.append(SOCK_DGRAM)
                    else:
                        try:
                            if port == getservbyname(origport, 'udp'):
                                socktypes.append(SOCK_DGRAM)
                        except error:
                            pass
                elif socktype == SOCK_STREAM:
                    port = getservbyname(port, 'tcp')
                elif socktype == SOCK_DGRAM:
                    port = getservbyname(port, 'udp')
                else:
                    raise gaierror(EAI_SERVICE, 'Servname not supported for ai_socktype')
            except error as ex:
                if 'not found' in str(ex):
                    raise gaierror(EAI_SERVICE, 'Servname not supported for ai_socktype')
                else:
                    raise gaierror(str(ex))
            except UnicodeEncodeError:
                raise error('Int or String expected', port)
    elif port is None:
        port = 0
    elif isinstance(port, integer_types):
        pass
    else:
        raise error('Int or String expected', port, type(port))
    port = int(port % 65536)
    if not socktypes and socktype:
        socktypes.append(socktype)
    return port, socktypes


def _resolve_special(hostname, family):
    if hostname == '':
        result = getaddrinfo(None, 0, family, SOCK_DGRAM, 0, AI_PASSIVE)
        if len(result) != 1:
            raise error('wildcard resolved to multiple address')
        return result[0][4][0]
    return hostname


class AbstractResolver(object):

    def gethostbyname(self, hostname, family=AF_INET):
        hostname = _resolve_special(hostname, family)
        return self.gethostbyname_ex(hostname, family)[-1][0]

    def gethostbyname_ex(self, hostname, family=AF_INET):
        aliases = []
        addresses = []
        tuples = self.getaddrinfo(hostname, 0, family,
                                  SOCK_STREAM,
                                  SOL_TCP, AI_CANONNAME)
        canonical = tuples[0][3]
        for item in tuples:
            addresses.append(item[4][0])
        # XXX we just ignore aliases
        return (canonical, aliases, addresses)

    def getaddrinfo(self, host, port, family=0, socktype=0, proto=0, flags=0):
        raise NotImplementedError()
