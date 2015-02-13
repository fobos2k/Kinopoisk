# -*- coding: utf-8 -*-
from meta import KinopoiskMeta, MovieDBMeta


def Start():
    HTTP.CacheTime = CACHE_1WEEK


class KinopoiskAgent(Agent.Movies):
    name = 'Kinopoisk'
    languages = [Locale.Language.Russian]
    primary_provider = True
    fallback_agent = False
    accepts_from = ['com.plexapp.agents.localmedia']
    contributes_to = ['com.plexapp.agents.kinopoiskru']

    # search #
    def search(self, results, media, lang, manual=False):
        continuesearch = True
        kp = KinopoiskMeta(media, lang)
        if media.guid:
            continuesearch = kp.external_search(results, manual)
        if continuesearch:
            kp.search(results, manual)

    # update #
    def update(self, metadata, media, lang, force=False):
        if not metadata.id:
            return None
        kp = KinopoiskMeta(media, lang)
        kp.getdata(metadata, force)

        mdb = MovieDBMeta(media, lang)
        mdb.getdata(metadata, force)