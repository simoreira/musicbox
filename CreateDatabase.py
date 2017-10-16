# -*- coding: utf-8 -*-

import BaseXClient

session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')

session.execute("create db musicbox")
print(session.info())
