# -*- coding: utf-8 -*-
KP_BASE_URL = 'https://ext.kinopoisk.ru/ios/3.4.1'
KP_KEY = 'samuraivbolote'
RE_YEAR = Regex('([1-2][0-9]{3})')

KP_MOVIE_SEARCH = '%s/getKPLiveSearch?keyword=%%s' % KP_BASE_URL
KP_MOVIE = '%s/getKPFilmDetailView?filmID=%%s' % KP_BASE_URL
KP_MOVIE_STAFF = '%s/getStaffList?type=all&filmID=%%s' % KP_BASE_URL
KP_MOVIE_IMAGES = '%s/getGallery?filmID=%%s' % KP_BASE_URL
KP_TRAILERS = 'http://www.kinopoisk.ru/film/%s/video/type/1/'

SCORE_PENALTY_ITEM_ORDER = 1
SCORE_PENALTY_YEAR = 20
SCORE_PENALTY_TITLE = 40

TMDB_BASE_URL = 'https://api.tmdb.org/3'
TMDB_API_KEY = 'a3dc111e66105f6387e99393813ae4d5'
TMDB_CONFIG = '%s/configuration?api_key=%s' % (TMDB_BASE_URL, TMDB_API_KEY)

TMDB_MOVIE_SEARCH = '%s/search/movie?api_key=%s&query=%%s&year=%%s&language=%%s&include_adult=%%s' % (TMDB_BASE_URL, TMDB_API_KEY)
TMDB_MOVIE = '%s/movie/%%s?api_key=%s&append_to_response=created_by,production_companies,images&language=%%s&include_image_language=en,ru,null' % (TMDB_BASE_URL, TMDB_API_KEY)
TMDB_MOVIE_IMAGES = '%s/movie/%%s/images?api_key=%s' % (TMDB_BASE_URL, TMDB_API_KEY)

ARTWORK_ITEM_LIMIT = 2
POSTER_SCORE_RATIO = .3
BACKDROP_SCORE_RATIO = .3

MPDB_ROOT = 'http://movieposterdb.plexapp.com'
MPDB_JSON = '%s/1/request.json?imdb_id=%%s&api_key=p13x2&secret=%%s&width=720&thumb_width=100' % MPDB_ROOT
MPDB_SECRET = 'e3c77873abc4866d9e28277a9114c60c'

KP_TRAILERS_URL = 'kpru://%s'
TYPE_MAP = {'primary_trailer': TrailerObject,
            'trailer': TrailerObject,
            'interview': InterviewObject,
            'behind_the_scenes': BehindTheScenesObject,
            'scene_or_sample': SceneOrSampleObject}

PLEXMOVIE_EXTRAS_URL = 'http://127.0.0.1:32400/services/iva/metadata/%s?lang=%s&extras=1'
IVA_ASSET_URL = 'iva://api.internetvideoarchive.com/2.0/DataService/VideoAssets(%s)?lang=%s&bitrates=%s&duration=%s'
TYPE_ORDER = ['primary_trailer', 'trailer', 'behind_the_scenes', 'interview', 'scene_or_sample']
IVA_LANGUAGES = {-1   : Locale.Language.Unknown,
                 0   : Locale.Language.English,
                 12  : Locale.Language.Swedish,
                 3   : Locale.Language.French,
                 2   : Locale.Language.Spanish,
                 32  : Locale.Language.Dutch,
                 10  : Locale.Language.German,
                 11  : Locale.Language.Italian,
                 9   : Locale.Language.Danish,
                 26  : Locale.Language.Arabic,
                 44  : Locale.Language.Catalan,
                 8   : Locale.Language.Chinese,
                 18  : Locale.Language.Czech,
                 80  : Locale.Language.Estonian,
                 33  : Locale.Language.Finnish,
                 5   : Locale.Language.Greek,
                 15  : Locale.Language.Hebrew,
                 36  : Locale.Language.Hindi,
                 29  : Locale.Language.Hungarian,
                 276 : Locale.Language.Indonesian,
                 7   : Locale.Language.Japanese,
                 13  : Locale.Language.Korean,
                 324 : Locale.Language.Latvian,
                 21  : Locale.Language.Norwegian,
                 24  : Locale.Language.Persian,
                 40  : Locale.Language.Polish,
                 17  : Locale.Language.Portuguese,
                 28  : Locale.Language.Romanian,
                 4   : Locale.Language.Russian,
                 105 : Locale.Language.Slovak,
                 25  : Locale.Language.Thai,
                 64  : Locale.Language.Turkish,
                 493 : Locale.Language.Ukrainian,
                 50  : Locale.Language.Vietnamese}