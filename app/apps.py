from django.apps import AppConfig
from django.shortcuts import render



class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
       """
       This function is called when startup.
       """
       from .regular_notifications import start # <= さっき作った start関数をインポート
       start()

    

