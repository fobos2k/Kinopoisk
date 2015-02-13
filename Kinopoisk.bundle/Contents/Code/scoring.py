# -*- coding: utf-8 -*-

import translit, difflib, re, const

def scoreTitle(entry, media, mediaName, idx):
    score = 100

    score = score - (idx * const.SCORE_PENALTY_ITEM_ORDER)

    yearpenalty = const.SCORE_PENALTY_YEAR
    mediayear = int(media.year or 0)
    year = int(re.sub('[^0-9]','', entry['year']) or 0)
    if mediayear != 0 and year != 0:
        yeardiff = abs(mediayear - year)
        if not yeardiff:
            yearpenalty = 0
        elif yeardiff == 1:
            yearpenalty = int(const.SCORE_PENALTY_YEAR / 4)
        elif yeardiff == 2:
            yearpenalty = int(const.SCORE_PENALTY_YEAR / 3)
    else:
        # If year is unknown, don't penalize the score too much.
        yearpenalty = int(const.SCORE_PENALTY_YEAR / 3)

    score = score - yearpenalty

    titlepenalty = computeTitlePenalty(mediaName, entry['nameRU'])

    alttitlepenalty = 100
    if 'nameEN' in entry:
        alttitlepenalty = computeTitlePenalty(mediaName, entry['nameEN'])

    try:
        detranslifiedmedianame = translit.detranslify(mediaName)
        detranslifiedtitlepenalty = computeTitlePenalty(detranslifiedmedianame, entry['nameRU'])
        titlepenalty = min(detranslifiedtitlepenalty, titlepenalty)

        if 'nameEN' in entry:
            detranslifiedalttitlepenalty = computeTitlePenalty(detranslifiedmedianame, entry['nameEN'])
            alttitledetranslified = translit.detranslify(entry['nameEN'])
            reverseddetranslifiedalttitlepenalty = computeTitlePenalty(detranslifiedmedianame, alttitledetranslified)
            alttitlepenalty = min(detranslifiedalttitlepenalty, reverseddetranslifiedalttitlepenalty, alttitlepenalty)
    except:
        pass

    titlepenalty = min(titlepenalty, alttitlepenalty)
    score = score - titlepenalty

    if idx == 0 and score <= 80:
        score = score + 5
    return score

def computeTitlePenalty(medianame, title):
    medianame = medianame.lower()
    title = title.lower()
    if medianame != title:
        diffratio = difflib.SequenceMatcher(None, medianame, title).ratio()
        penalty = int(const.SCORE_PENALTY_TITLE * (1 - diffratio))
        if penalty >= 15:
            medianameparts = medianame.split()
            titleparts = title.split()
            if len(medianameparts) <= len(titleparts):
                i = 0
                penaltyalt = max(5, int(round((1.0 - (float(len(medianameparts)) / len(titleparts))) * 15 - 5)))
                penaltyperpart = const.SCORE_PENALTY_TITLE / len(medianameparts)
                for mediaNamePart in medianameparts:
                    partdiffratio = difflib.SequenceMatcher(None, mediaNamePart, titleparts[i]).ratio()
                    penaltyalt = penaltyalt + int(penaltyperpart * (1 - partdiffratio))
                    i = i + 1
                penalty = min(penalty, penaltyalt)
        return penalty
    return 0