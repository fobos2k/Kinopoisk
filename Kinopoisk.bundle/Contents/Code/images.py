# -*- coding: utf-8 -*-
import const


def handle_tmdb_images(metadata, tmdb_images_dict, lang, img_url):
    if tmdb_images_dict:
        valid_names = list()
        if tmdb_images_dict['posters']:
            max_average = max([(lambda p: float(p['vote_average']) or 5)(p) for p in tmdb_images_dict['posters']])
            max_count = max([(lambda p: float(p['vote_count']))(p) for p in tmdb_images_dict['posters']]) or 1

            for i, poster in enumerate(tmdb_images_dict['posters']):
                score = (float(poster['vote_average']) / max_average) * const.POSTER_SCORE_RATIO
                score += (float(poster['vote_count']) / max_count) * (1 - const.POSTER_SCORE_RATIO)
                tmdb_images_dict['posters'][i]['score'] = score

                # Boost the score for localized posters (according to the preference).
                if Prefs['prefer_local_art']:
                    if poster['iso_639_1'] == lang:
                        tmdb_images_dict['posters'][i]['score'] = poster['score'] + 1

                # Discount score for foreign posters.
                if poster['iso_639_1'] != lang and poster['iso_639_1'] is not None and poster['iso_639_1'] != 'en':
                    tmdb_images_dict['posters'][i]['score'] = poster['score'] - 1

            for i, poster in enumerate(sorted(tmdb_images_dict['posters'], key=lambda k: k['score'], reverse=True)):
                if i >= int(Prefs['max_posters']):
                    break
                else:
                    poster_url = img_url + 'original' + poster['file_path']
                    thumb_url = img_url + 'w154' + poster['file_path']
                    valid_names.append(poster_url)

                    if poster_url not in metadata.posters:
                        try:
                            metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(thumb_url).content,
                                                                         sort_order=i + 1)
                        except NameError, e:
                            pass

        metadata.posters.validate_keys(valid_names)

        valid_names = list()
        if tmdb_images_dict['backdrops']:
            max_average = max([(lambda p: float(p['vote_average']) or 5)(p) for p in tmdb_images_dict['backdrops']])
            max_count = max([(lambda p: float(p['vote_count']))(p) for p in tmdb_images_dict['backdrops']]) or 1

            for i, backdrop in enumerate(tmdb_images_dict['backdrops']):
                score = (float(backdrop['vote_average']) / max_average) * const.BACKDROP_SCORE_RATIO
                score += (float(backdrop['vote_count']) / max_count) * (1 - const.BACKDROP_SCORE_RATIO)
                tmdb_images_dict['backdrops'][i]['score'] = score

                # For backdrops, we prefer "No Language" since they're intended to sit behind text.
                if backdrop['iso_639_1'] == 'xx' or backdrop['iso_639_1'] == 'none':
                    tmdb_images_dict['backdrops'][i]['score'] = float(backdrop['score']) + 2

                # Boost the score for localized art (according to the preference).
                if backdrop['iso_639_1'] == lang:
                    tmdb_images_dict['backdrops'][i]['score'] = float(backdrop['score']) + 1

                # Discount score for foreign art.
                if backdrop['iso_639_1'] != lang and backdrop['iso_639_1'] is not None and backdrop['iso_639_1'] != 'en':
                    tmdb_images_dict['backdrops'][i]['score'] = float(backdrop['score']) - 1

            for i, backdrop in enumerate(sorted(tmdb_images_dict['backdrops'], key=lambda k: k['score'], reverse=True)):
                if i >= int(Prefs['max_backdrops']):
                    break
                else:
                    backdrop_url = img_url + 'original' + backdrop['file_path']
                    thumb_url = img_url + 'w300' + backdrop['file_path']
                    valid_names.append(backdrop_url)

                if backdrop_url not in metadata.art:
                    try:
                        metadata.art[backdrop_url] = Proxy.Preview(HTTP.Request(thumb_url).content, sort_order=i + 1)
                    except NameError, e:
                        pass

        metadata.art.validate_keys(valid_names)

def handle_mpdb_images(metadata, imdb, lang):
    pass

def handle_kpru_images(metadata, img_dict):
    pass