from django.db import models

# Create your models here.
import BaseXClient

class Database:
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    session.execute("create db musicbox")