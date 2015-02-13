# -*- coding: utf-8 -*-
import re
import datetime

import const
import scoring
import images
import trailers


class FilmMeta:
    def __init__(self, media, lang):
        self.media, self.lang, = media, lang

    @property
    def media(self):
        return self.media

    @media.setter
    def media(self, value):
        self.media = value

    @property
    def lang(self):
        return self.lang

    @lang.setter
    def lang(self, value):
        self.lang = value

    def makerequest(self, url, headerlist=None, cache_time=CACHE_1MONTH):
        json_data = None
        try:
            json_data = JSON.ObjectFromURL(url, sleep=2.0, headers=headerlist, cacheTime=cache_time)
            return json_data['data'] if 'data' in json_data else json_data
        except:
            pass

        return json_data


class KinopoiskMeta(FilmMeta):
    def makerequest(self, url, headerlist=None, cache_time=CACHE_1MONTH):
        headerlist = {
            'Image-Scale': 1,
            'countryID': 2,
            'cityID': 1,
            'Content-Lang': 'ru',
            'Accept': 'application/json',
            'device': 'android',
            'Android-Api-Version': 19,
            'clientDate': Datetime.Now().strftime("%H:%M %d.%m.%Y")
        }
        return FilmMeta.makerequest(self, url + '&key=' + Hash.MD5(url[len(const.KP_BASE_URL) + 1:] + const.KP_KEY),
                                    headerlist)

    def searchfilm(self, media_name):
        return self.makerequest(url=const.KP_MOVIE_SEARCH % String.Quote(media_name, usePlus=False))

    def getfilmdata(self, film_id):
        return self.makerequest(url=const.KP_MOVIE % film_id)

    def getpeople(self, film_id):
        return self.makerequest(url=const.KP_MOVIE_STAFF % film_id)

    def external_search(self, results, manual=False):
        title = None
        year = None
        theguid = self.media.guid
        kp_search = re.search(r'^(com.plexapp.agents.kinopoiskru://)([\d]+)\?.+', theguid)

        if kp_search and kp_search.group(1) and kp_search.group(2):
            theguid = kp_search.group(2)

        try:
            film_data = self.getfilmdata(theguid)
            if film_data:
                title = film_data['nameRU']
                year = int(film_data.get('year') or 0)
        except:
            pass

        if title is not None:
            results.Append(MetadataSearchResult(id=theguid, name=title, year=year, lang=self.lang, score=100))
            return False
        return True

    def search(self, results, manual=False):
        name = unicode(self.media.name)
        name = re.sub(r'\[.*?\]', '', name)
        media_name = name.lower()

        if self.media.year is None:
            yearmatch = const.RE_YEAR.search(media_name)
            if yearmatch:
                yearstr = yearmatch.group(1)
                yearint = int(yearstr)
                if 1900 < yearint < (datetime.date.today().year + 1) and yearstr != media_name:
                    self.media.year = yearint
                    media_name = media_name.replace(yearstr, '')

        json_obj = self.searchfilm(media_name)

        if not isinstance(json_obj, dict):
            return None

        itemindex = -1
        if 'items' in json_obj:
            for entry in json_obj['items']:
                if {'id', 'nameRU', 'year'} <= set(entry) and entry['type'] == 'KPFilmObject':
                    itemindex += 1
                    results.Append(
                        MetadataSearchResult(
                            id=entry['id'],
                            name=entry['nameRU'],
                            year=str(entry['year']),
                            lang=self.lang,
                            score=scoring.scoreTitle(entry, self.media, media_name, itemindex)
                        )
                    )

        results.Sort('score', descending=True)

    def getdata(self, metadata, force):
        film_dict = self.getfilmdata(metadata.id)
        if not isinstance(film_dict, dict):
            return None

        # title
        metadata.title = film_dict['nameRU'].replace(u'(видео)', '')
        if 'nameEN' in film_dict and film_dict['nameEN'] != film_dict['nameRU']:
            metadata.original_title = film_dict['nameEN']

        metadata.tagline = film_dict.get('slogan')
        metadata.countries.clear()
        if 'country' in film_dict:
            for country in film_dict['country'].split(', '):
                metadata.countries.add(country)

        metadata.genres.clear()
        for genre in film_dict['genre'].split(', '):
            metadata.genres.add(genre.strip().title())

        metadata.year = int(film_dict.get('year') or 0)
        metadata.content_rating = film_dict.get('ratingMPAA')
        metadata.content_rating_age = int(film_dict.get('ratingAgeLimits') or 0)

        metadata.originally_available_at = datetime.datetime.strptime(
            film_dict['rentData'].get('premiereWorld') or film_dict['rentData'].get('premiereRU'), '%d.%m.%Y'
        ).date() if 'rentData' in film_dict else None

        summary_add = ''
        if 'ratingData' in film_dict:
            metadata.rating = float(film_dict['ratingData'].get('rating'))
            summary_add = u'КиноПоиск: ' + film_dict['ratingData'].get('rating').__str__()
            if 'ratingVoteCount' in film_dict['ratingData']:
                summary_add += ' (' + film_dict['ratingData'].get('ratingVoteCount').__str__() + ')'
            summary_add += '. '

            if 'ratingIMDb' in film_dict['ratingData']:
                summary_add += u'IMDb: ' + film_dict['ratingData'].get('ratingIMDb').__str__()
            if 'ratingIMDbVoteCount' in film_dict['ratingData']:
                summary_add += ' (' + film_dict['ratingData'].get('ratingIMDbVoteCount').__str__() + ')'
            summary_add += '. '

        if summary_add != '':
            summary_add += '\n'
        metadata.summary = summary_add + film_dict.get('description')

        staff_dict = self.getpeople(metadata.id)
        metadata.directors.clear()
        metadata.writers.clear()
        metadata.producers.clear()
        metadata.roles.clear()
        for staff_type in staff_dict['creators']:
            for staff in staff_type:
                prole = staff.get('professionKey')
                pname = staff.get('nameRU') if len(staff.get('nameRU')) > 0 else staff.get('nameEN')
                if prole == 'actor':
                    role = metadata.roles.new()
                    role.actor = pname
                    if 'posterURL' in staff:
                        role.photo = 'http://win8.st.kp.yandex.net/actor/' + staff['id'][0] + '/' + staff['id'] + '.jpg'
                    role.role = staff.get('description')
                elif prole == 'director':
                    metadata.directors.add(pname)
                elif prole == 'writer':
                    metadata.writers.add(pname)
                elif prole == 'producer':
                    metadata.producers.add(pname)

        # Extras.
        try:
            # Do a quick check to make sure we've got the types available in this framework version, and that the server
            # is new enough to support the IVA endpoints.
            t = InterviewObject()
            if Util.VersionAtLeast(Platform.ServerVersion, 0,9,9,13):
                find_extras = True
            else:
                find_extras = False
                Log('Not adding extras: Server v0.9.9.13+ required')
        except NameError, e:
            Log('Not adding extras: Framework v2.5.0+ required')
            find_extras = False

        if find_extras and Prefs['load_extras'] and Prefs['extras_source'] in {u'Кинопоиск', u'Все источники'}:
            trailers.handle_kpru_trailers(const.KP_TRAILERS % metadata.id, metadata)


class MovieDBMeta(FilmMeta):
    def makerequest(self, url, cache_time=CACHE_1MONTH):
        json_data = None
        try:
            json_data = JSON.ObjectFromURL(url, sleep=2.0, headers={'Accept': 'application/json'}, cacheTime=cache_time)
        except:
            Log('Error fetching JSON from The Movie Database.')
        return json_data

    def __init__(self, media, lang):
        self.config_dict = self.makerequest(url=const.TMDB_CONFIG, cache_time=CACHE_1WEEK * 2)
        FilmMeta.__init__(self, media, lang)

    def search(self, metadata):
        # search by title and year
        tmdb_dict = self.makerequest(
            url=const.TMDB_MOVIE_SEARCH % (
                String.Quote(metadata.title.encode('utf-8'))
                , metadata.year
                , self.lang
                , False
            )
        )

        # search by title
        if tmdb_dict is None or len(tmdb_dict['results']) == 0:
            tmdb_dict = self.makerequest(
                url=const.TMDB_MOVIE_SEARCH % (
                    String.Quote(metadata.title.encode('utf-8'))
                    , ''
                    , self.lang
                    , False
                )
            )

        # search by original title
        if metadata.original_title is not None and metadata.title != metadata.original_title \
                and (tmdb_dict is None or len(tmdb_dict['results'])) == 0:
            tmdb_dict = self.makerequest(
                url=const.TMDB_MOVIE_SEARCH % (
                    String.Quote(metadata.original_title.encode('utf-8'))
                    , ''
                    , self.lang
                    , False
                )
            )

        results = []
        if isinstance(tmdb_dict, dict) and 'results' in tmdb_dict:
            for i, movie in enumerate(sorted(tmdb_dict['results'], key=lambda k: k['popularity'], reverse=True)):
                score = 100

                original_title_penalty = 100
                if metadata.original_title and 'original_title' in movie:
                    original_title_penalty = scoring.computeTitlePenalty(metadata.original_title,
                                                                         movie['original_title'])
                title_penalty = scoring.computeTitlePenalty(metadata.title, movie['title'])
                title_penalty = min(title_penalty, original_title_penalty)
                score = score - title_penalty

                if metadata.originally_available_at and 'release_date' in movie:
                    days_diff = abs((
                                        metadata.originally_available_at - Datetime.ParseDate(
                                            movie['release_date']).date()
                                    ).days)
                    if days_diff == 0:
                        release_penalty = 0
                    elif days_diff <= 10:
                        release_penalty = 5
                    else:
                        release_penalty = 10
                    score = score - release_penalty

                results.append({'id': movie['id'], 'title': movie['title'], 'score': score})

            results = sorted(results, key=lambda item: item['score'], reverse=True)

        if len(results) > 0 and results[0]['score'] > 0:
            return results[0]['id']
        return None

    def getdata(self, metadata, force):
        tmdbid = self.search(metadata)
        if tmdbid:
            tmdb_dict = self.makerequest(url=const.TMDB_MOVIE % (tmdbid, self.lang))

            if not isinstance(tmdb_dict, dict) \
                    or 'overview' not in tmdb_dict \
                    or tmdb_dict['overview'] is None \
                    or tmdb_dict['overview'] == "":
                # Retry the query with no language specified if we didn't get anything from the initial request.
                tmdb_dict = self.makerequest(url=self.TMDB_MOVIE % (tmdbid, ''))

            imdbid = tmdb_dict['imdb_id']

            if 'production_companies' in tmdb_dict and len(tmdb_dict['production_companies']) > 0:
                metadata.studio = tmdb_dict['production_companies'][0]['name']

            images.handle_tmdb_images(metadata, tmdb_dict['images'], self.lang, self.config_dict['images']['base_url'])

            # Extras.
            try:
                # Do a quick check to make sure we've got the types available in this framework version, and that the server
                # is new enough to support the IVA endpoints.
                t = InterviewObject()
                if Util.VersionAtLeast(Platform.ServerVersion, 0,9,9,13):
                    find_extras = True
                else:
                    find_extras = False
                    Log('Not adding extras: Server v0.9.9.13+ required')
            except NameError, e:
                Log('Not adding extras: Framework v2.5.0+ required')
                find_extras = False

            if find_extras and Prefs['load_extras'] and Prefs['extras_source'] in {u'Plex IVA', u'Все источники'}:
                trailers.handle_iva_trailers(metadata, imdbid, self.lang)