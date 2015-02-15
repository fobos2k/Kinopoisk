# -*- coding: utf-8 -*-
import re
import const
from qtparse import *
from urllib2 import HTTPError


def handle_kpru_trailers(url, metadata):
    page = HTML.ElementFromURL(url, headers={
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36',
        'Accept': 'text/html'
    })
    if len(page) != 0:
        trailers = []  # trailers dict
        qtp = QtParser()
        for tr in page.xpath("//div/table[2]/tr[2]/td/table/tr[*//a[@onclick] and (*//div[contains(@class,'flag2')] or not(*//div[contains(@class,'flag') and span]))]"):
            tr_info = {'title': tr.xpath('.//div/a[not(@onclick)]/text()')[0], 'data': [], 'img_id':
                tr.xpath('.//following-sibling::tr[1]//div[@class="listTrailerShare"]/attribute::data-url')[0].split(
                    '/')[-2]}
            for quol in tr.xpath(
                    ".//following-sibling::tr[2]/td/table/tr/td/table/tr[*/a[contains(@href,'kp.cdn.yandex.net')]]"):
                tr_link = quol.xpath('.//td[3]/a/attribute::href')[0].split('link=')[-1]
                if tr_link.split('.')[-1] in {'mp4', 'mov'}:
                    try:
                        if qtp.openurl(tr_link):
                            tr_data = qtp.analyze()
                            tr_info['data'].append({
                                'streams': tr_data['streams'],
                                'audio': tr_data['audio'],
                                'video': tr_data['video'],
                                'bt': int(tr_data['bitrate']),
                                'dr': int(tr_data['playtime_seconds']),
                                'lnk': tr_link,
                                'id': re.search('-([0-9]+)\.', tr_link).group(1)
                            })
                    except:
                        pass
            if len(tr_info['data']) != 0:
                trailers.append(tr_info)

        trailers = sorted(trailers, key=lambda k: len(k['data']), reverse=True)

        extras = []
        for trailer in trailers:
            extra_type = 'trailer'
            spoken_lang = 'ru'
            trailer_json = JSON.StringFromObject(trailer['data'])
            extras.append({'type': extra_type,
                           'lang': spoken_lang,
                           'extra': const.TYPE_MAP[extra_type](
                               url=const.KP_TRAILERS_URL % String.Encode(trailer_json),
                               title=trailer['title'],
                               year=None,
                               originally_available_at=None,
                               thumb='http://kp.cdn.yandex.net/%s/3_%s.jpg' % (metadata.id, trailer['img_id']))})

        for extra in extras:
            metadata.extras.add(extra['extra'])

def handle_iva_trailers(metadata, imdbid, lang):
    try:
        req = const.PLEXMOVIE_EXTRAS_URL % (imdbid[2:], lang)
        xml = XML.ElementFromURL(req)

        extras = []
        media_title = None
        for extra in xml.xpath('//extra'):
            avail = Datetime.ParseDate(extra.get('originally_available_at'))
            lang_code = int(extra.get('lang_code')) if extra.get('lang_code') else -1
            subtitle_lang_code = int(extra.get('subtitle_lang_code')) if extra.get('subtitle_lang_code') else -1

            spoken_lang = const.IVA_LANGUAGES.get(lang_code) or Locale.Language.Unknown
            subtitle_lang = const.IVA_LANGUAGES.get(subtitle_lang_code) or Locale.Language.Unknown
            include = False

            # Include extras in section language...
            if spoken_lang == lang:

                # ...if there are no subs or english.
                if subtitle_lang_code in {-1, Locale.Language.English}:
                    include = True

            # Include foreign language extras if they have subs in the section language.
            if spoken_lang != lang and subtitle_lang == lang:
                include = True

            # Always include English language extras anyway (often section lang options are not available), but only if they have no subs.
            if spoken_lang == Locale.Language.English and subtitle_lang_code == -1:
                include = True

            # Exclude non-primary trailers and scenes.
            extra_type = 'primary_trailer' if extra.get('primary') == 'true' else extra.get('type')
            if extra_type == 'trailer' or extra_type == 'scene_or_sample':
                include = False

            if include:

                bitrates = extra.get('bitrates') or ''
                duration = int(extra.get('duration') or 0)

                # Remember the title if this is the primary trailer.
                if extra_type == 'primary_trailer':
                    media_title = extra.get('title')

                # Add the extra.
                if extra_type in const.TYPE_MAP:
                    extras.append({ 'type' : extra_type,
                                    'lang' : spoken_lang,
                                    'extra' : const.TYPE_MAP[extra_type](url=const.IVA_ASSET_URL % (extra.get('iva_id'), spoken_lang, bitrates, duration),
                                                                   title=extra.get('title'),
                                                                   year=avail.year,
                                                                   originally_available_at=avail,
                                                                   thumb=extra.get('thumb') or '')})
                else:
                    Log('Skipping extra %s because type %s was not recognized.' % (extra.get('iva_id'), extra_type))

        # Sort the extras, making sure the primary trailer is first.
        extras.sort(key=lambda e: const.TYPE_ORDER.index(e['type']))

        # If our primary trailer is in English but the library language is something else, see if we can do better.
        if len(extras) > 0 and lang != Locale.Language.English and extras[0]['lang'] == Locale.Language.English:
            lang_matches = [t for t in xml.xpath('//extra') if t.get('type') == 'trailer' and const.IVA_LANGUAGES.get(int(t.get('subtitle_lang_code') or -1)) == lang]
            lang_matches += [t for t in xml.xpath('//extra') if t.get('type') == 'trailer' and const.IVA_LANGUAGES.get(int(t.get('lang_code') or -1)) == lang]
            if len(lang_matches) > 0:
                extra = lang_matches[0]
                spoken_lang = const.IVA_LANGUAGES.get(int(extra.get('lang_code') or -1)) or Locale.Language.Unknown
                extras[0]['lang'] = spoken_lang
                extras[0]['extra'].url = const.IVA_ASSET_URL % (extra.get('iva_id'), spoken_lang, extra.get('bitrates') or '', int(extra.get('duration') or 0))
                extras[0]['extra'].thumb = extra.get('thumb') or ''
                Log('Adding trailer with spoken language %s and subtitled langauge %s to match library language.' % (spoken_lang, const.IVA_LANGUAGES.get(int(extra.get('subtitle_lang_code') or -1)) or Locale.Language.Unknown))

        # Clean up the found extras.
        extras = [scrub_extra(extra, media_title) for extra in extras]

        # Add them in the right order to the metadata.extras list.
        for extra in extras:
            metadata.extras.add(extra['extra'])

        Log('Added %d of %d extras.' % (len(metadata.extras), len(xml.xpath('//extra'))))
    except HTTPError, e:
        if e.code == 403:
            Log('Skipping online extra lookup (an active Plex Pass is required).')

def scrub_extra(extra, media_title):

    e = extra['extra']

    # Remove the "Movie Title: " from non-trailer extra titles.
    if media_title is not None:
        r = re.compile(media_title + ': ', re.IGNORECASE)
        e.title = r.sub('', e.title)

    # Remove the "Movie Title Scene: " from SceneOrSample extra titles.
    if media_title is not None:
        r = re.compile(media_title + ' Scene: ', re.IGNORECASE)
        e.title = r.sub('', e.title)

    # Capitalise UK correctly.
    e.title = e.title.replace('Uk', 'UK')

    return extra