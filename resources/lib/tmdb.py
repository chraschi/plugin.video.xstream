# -*- coding: utf-8 -*-
import json, re
from requestHandler import cRequestHandler
from resources.lib.config import cConfig
try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus


class cTMDB:
    TMDB_GENRES = {12: 'Abenteuer', 14: 'Fantasy', 16: 'Animation', 18: 'Drama', 27: 'Horror', 28: 'Action', 35: 'Komödie', 36: 'Historie', 37: 'Western', 53: 'Thriller', 80: 'Krimi', 99: 'Dokumentarfilm', 878: 'Science Fiction', 9648: 'Mystery', 10402: 'Musik', 10749: 'Liebesfilm', 10751: 'Familie', 10752: 'Kriegsfilm', 10759: 'Action & Adventure', 10762: 'Kids', 10763: 'News', 10764: 'Reality', 10765: 'Sci-Fi & Fantasy', 10766: 'Soap', 10767: 'Talk', 10768: 'War & Politics', 10770: 'TV-Film'}
    URL = 'https://api.themoviedb.org/3/'
    URL_TRAILER = 'plugin://plugin.video.youtube/play/?video_id=%s'

    def __init__(self, api_key='', lang='de'):
        self.api_key = '86dd18b04874d9c94afadde7993d94e3'
        self.lang = lang
        self.poster = 'https://image.tmdb.org/t/p/%s' % cConfig().getSetting('poster_tmdb')
        self.fanart = 'https://image.tmdb.org/t/p/%s' % cConfig().getSetting('backdrop_tmdb')

    def search_movie_name(self, name, year='', page=1, advanced='false'):
        name = re.sub(" +", " ", name)
        if year:
            term = quote_plus(name) + '&year=' + year
        else:
            term = quote_plus(name)
        meta = self._call('search/movie', 'query=' + term + '&page=' + str(page))
        if 'errors' not in meta and 'status_code' not in meta:
            if 'total_results' in meta and meta['total_results'] == 0 and year:
                meta = self.search_movie_name(name, '')
            if 'total_results' in meta and meta['total_results'] != 0:
                movie = ''
                if meta['total_results'] == 1:
                    movie = meta['results'][0]
                else:
                    for searchMovie in meta['results']:
                        if searchMovie['genre_ids'] and 99 not in searchMovie['genre_ids']:
                            if searchMovie['title'].lower() == name.lower():
                                movie = searchMovie
                                break
                    if not movie:
                        for searchMovie in meta['results']:
                            if searchMovie['genre_ids'] and 99 not in searchMovie['genre_ids']:
                                if year:
                                    if 'release_date' in searchMovie and searchMovie['release_date']:
                                        release_date = searchMovie['release_date']
                                        yy = release_date[:4]
                                        if int(year) - int(yy) > 1:
                                            continue
                                movie = searchMovie
                                break
                    if not movie:
                        movie = meta['results'][0]
                if advanced == 'true':
                    tmdb_id = movie['id']
                    meta = self.search_movie_id(tmdb_id)
                else:
                    meta = movie
        else:
            meta = {}
        return meta

    def search_tvshow_name(self, name, year='', page=1, genre='', advanced='false'):
        name = name.lower()
        if '- staffel' in name:
            name = re.sub('-[^>]\wtaffel[^>]\d+', '', name)
        elif 'staffel' in name:
            name = re.sub('\wtaffel[^>]\d+', '', name)
        if year:
            term = quote_plus(name) + '&year=' + year
        else:
            term = quote_plus(name)
        meta = self._call('search/tv', 'query=' + term + '&page=' + str(page))
        if 'errors' not in meta and 'status_code' not in meta:
            if 'total_results' in meta and meta['total_results'] == 0 and year:
                meta = self.search_tvshow_name(name, '')
            if 'total_results' in meta and meta['total_results'] != 0:
                movie = ''
                if meta['total_results'] == 1:
                    movie = meta['results'][0]
                else:
                    for searchMovie in meta['results']:
                        if genre == '' or genre in searchMovie['genre_ids']:
                            movieName = searchMovie['name']
                            if movieName.lower() == name.lower():
                                movie = searchMovie
                                break
                    if not movie:
                        for searchMovie in meta['results']:
                            if genre and genre in searchMovie['genre_ids']:
                                if year:
                                    if 'release_date' in searchMovie and searchMovie['release_date']:
                                        release_date = searchMovie['release_date']
                                        yy = release_date[:4]
                                        if int(year) - int(yy) > 1:
                                            continue
                                movie = searchMovie
                                break
                    if not movie:
                        movie = meta['results'][0]
                if advanced == 'true':
                    tmdb_id = movie['id']
                    meta = self.search_tvshow_id(tmdb_id)
                else:
                    meta = movie
        else:
            meta = {}
        return meta

    def search_person_name(self, name):
        name = re.sub(" +", " ", name)
        term = quote_plus(name)
        meta = self._call('search/person', 'query=' + term)
        if 'errors' not in meta and 'status_code' not in meta:
            if 'total_results' in meta and meta['total_results'] != 0:
                meta = meta['results'][0]
                person_id = meta['id']
                meta = self.search_person_id(person_id)
        else:
            meta = {}
        return meta

    def search_movie_id(self, movie_id, append_to_response='append_to_response=trailers,credits'):
        result = self._call('movie/' + str(movie_id), append_to_response)
        result['tmdb_id'] = movie_id
        return result

    def search_tvshow_id(self, show_id, append_to_response='append_to_response=external_ids,videos,credits'):
        result = self._call('tv/' + str(show_id), append_to_response)
        result['tmdb_id'] = show_id
        return result

    def search_person_id(self, person_id):
        result = self._call('person/' + str(person_id))
        result['tmdb_id'] = person_id
        return result

    def _format(self, meta, name):
        _meta = {}
        _meta['genre'] = ''
        _meta['writer'] = ''
        if 'id' in meta:
            _meta['tmdb_id'] = meta['id']
        if 'budget' in meta and meta['budget']:
            _meta['budget'] = "{:,} $".format(meta['budget'])
        if 'revenue' in meta and meta['revenue']:
            _meta['revenue'] = "{:,} $".format(meta['revenue'])
        if 'original_title' in meta and meta['original_title']:
            _meta['original_title'] = meta['original_title']
        if 'original_language' in meta and meta['original_language']:
            _meta['original_language'] = meta['original_language']
        if 'tmdb_id' in meta:
            _meta['tmdb_id'] = meta['tmdb_id']
        if 'imdb_id' in meta:
            _meta['imdb_id'] = meta['imdb_id']
        elif 'external_ids' in meta:
            _meta['imdb_id'] = meta['external_ids']['imdb_id']
        if 'mpaa' in meta:
            _meta['mpaa'] = meta['mpaa']
        if 'media_type' in meta:
            _meta['media_type'] = meta['media_type']
        if 'release_date' in meta:
            _meta['premiered'] = meta['release_date']
        elif 'first_air_date' in meta:
            _meta['premiered'] = meta['first_air_date']
        elif 'premiered' in meta and meta['premiered']:
            _meta['premiered'] = meta['premiered']
        elif 's_premiered' in meta and meta['s_premiered']:
            _meta['premiered'] = meta['s_premiered']
        elif 'air_date' in meta and meta['air_date']:
            _meta['premiered'] = meta['air_date']
        if 'year' in meta:
            _meta['year'] = meta['year']
        elif 's_year' in meta:
            _meta['year'] = meta['s_year']
        else:
            try:
                if 'premiered' in _meta and _meta['premiered']:
                    _meta['year'] = int(_meta['premiered'][:4])
            except Exception:
                pass
        if 'rating' in meta:
            _meta['rating'] = meta['rating']
        elif 'vote_average' in meta:
            _meta['rating'] = meta['vote_average']
        if 'votes' in meta:
            _meta['votes'] = meta['votes']
        elif 'vote_count' in meta:
            _meta['votes'] = meta['vote_count']
        duration = 0
        if 'runtime' in meta and meta['runtime']:
            duration = int(meta['runtime'])
        elif 'episode_run_time' in meta and meta['episode_run_time']:
            duration = int(meta['episode_run_time'][0])
        if duration < 300:
            duration *= 60
        if duration > 1:
            _meta['duration'] = duration
        if 'overview' in meta and meta['overview']:
            _meta['plot'] = meta['overview']
        elif 'parts' in meta:
            _meta['plot'] = meta['parts'][0]['overview']
        elif 'biography' in meta:
            _meta['plot'] = meta['biography']
        if 'studio' in meta:
            _meta['studio'] = meta['studio']
        elif 'production_companies' in meta:
            _meta['studio'] = ''
            for studio in meta['production_companies']:
                if _meta['studio'] == '':
                    _meta['studio'] += studio['name']
                else:
                    _meta['studio'] += ' / ' + studio['name']
        if 'genre' in meta:
            listeGenre = meta['genre']
            if '{' in listeGenre:
                meta['genres'] = eval(listeGenre)
            else:
                _meta['genre'] = listeGenre
        if 'genres' in meta:
            for genre in meta['genres']:
                if _meta['genre'] == '':
                    _meta['genre'] += genre['name']
                else:
                    _meta['genre'] += ' / ' + genre['name']
        elif 'genre_ids' in meta:
            genres = self.getGenresFromIDs(meta['genre_ids'])
            _meta['genre'] = ''
            for genre in genres:
                if _meta['genre'] == '':
                    _meta['genre'] += genre
                else:
                    _meta['genre'] += ' / ' + genre
        elif 'parts' in meta:
            genres = self.getGenresFromIDs(meta['parts'][0]['genre_ids'])
            _meta['genre'] = ''
            for genre in genres:
                if _meta['genre'] == '':
                    _meta['genre'] += genre
                else:
                    _meta['genre'] += ' / ' + genre
        trailer_id = ''
        if 'trailer' in meta and meta['trailer']:
            _meta['trailer'] = meta['trailer']
        elif 'trailers' in meta:
            try:
                trailers = meta['trailers']['youtube']
                for trailer in trailers:
                    if trailer['type'] == 'Trailer':
                        if 'VF' in trailer['name']:
                            trailer_id = trailer['source']
                            break
                if not trailer_id:
                    trailer_id = meta['trailers']['youtube'][0]['source']
                _meta['trailer'] = self.URL_TRAILER % trailer_id
            except:
                pass
        elif 'videos' in meta and meta['videos']:
            try:
                trailers = meta['videos']
                if len(trailers['results']) > 0:
                    for trailer in trailers['results']:
                        if trailer['type'] == 'Trailer' and trailer['site'] == 'YouTube':
                            trailer_id = trailer['key']
                            if 'de' in trailer['iso_639_1']:
                                trailer_id = trailer['key']
                                break
                    if not trailer_id:
                        trailer_id = meta['videos'][0]['key']
                    _meta['trailer'] = self.URL_TRAILER % trailer_id
            except:
                pass
        if 'backdrop_path' in meta and meta['backdrop_path']:
            _meta['backdrop_path'] = meta['backdrop_path']
            _meta['backdrop_url'] = self.fanart + str(_meta['backdrop_path'])
        elif 'parts' in meta:
            nbFilm = len(meta['parts'])
            _meta['backdrop_path'] = meta['parts'][nbFilm - 1]['backdrop_path']
            _meta['backdrop_url'] = self.fanart + str(_meta['backdrop_path'])
        if 'poster_path' in meta and meta['poster_path']:
            _meta['poster_path'] = meta['poster_path']
            _meta['cover_url'] = self.poster + str(_meta['poster_path'])
        elif 'parts' in meta:
            nbFilm = len(meta['parts'])
            _meta['poster_path'] = meta['parts'][nbFilm - 1]['poster_path']
            _meta['cover_url'] = self.fanart + str(_meta['poster_path'])
        elif 'profile_path' in meta:
            _meta['poster_path'] = meta['profile_path']
            _meta['cover_url'] = self.poster + str(_meta['poster_path'])
        elif 'file_path' in meta:
            _meta['poster_path'] = meta['file_path']
            _meta['cover_url'] = self.poster + str(_meta['poster_path'])
            _meta['backdrop_path'] = _meta['poster_path']
            _meta['backdrop_url'] = self.fanart + str(_meta['backdrop_path'])
        if 's_poster_path' in meta and meta['s_poster_path']:
            _meta['poster_path'] = meta['s_poster_path']
            _meta['cover_url'] = self.poster + str(meta['s_poster_path'])
        if 'tagline' in meta and meta['tagline']:
            _meta['tagline'] = meta['tagline']
        if 'status' in meta:
            _meta['status'] = meta['status']
        if 'writer' in meta and meta['writer']:
            _meta['writer'] = meta['writer']
        if 'director' in meta and meta['director']:
            _meta['director'] = meta['director']
        if 'credits' in meta and meta['credits']:
            strmeta = str(meta['credits'])
            listCredits = eval(strmeta)
            casts = listCredits['cast']
            crews = []
            if len(casts) > 0:
                licast = []
                if 'crew' in listCredits:
                    crews = listCredits['crew']
                if len(crews) > 0:
                    _meta['credits'] = "{'cast': " + str(casts) + ", 'crew': " + str(crews) + "}"
                    for cast in casts:
                        licast.append((cast['name'], cast['character'], self.poster + str(cast['profile_path']), str(cast['id'])))
                    _meta['cast'] = licast
                else:
                    _meta['credits'] = "{'cast': " + str(casts) + '}'
            if len(crews) > 0:
                for crew in crews:
                    if crew['job'] == 'Director':
                        _meta['director'] = crew['name']
                    elif crew['department'] == 'Writing':
                        if _meta['writer'] != '':
                            _meta['writer'] += ' / '
                        _meta['writer'] += '%s (%s)' % (crew['job'], crew['name'])
                    elif crew['department'] == 'Production' and 'Producer' in crew['job']:
                        if _meta['writer'] != '':
                            _meta['writer'] += ' / '
                        _meta['writer'] += '%s (%s)' % (crew['job'], crew['name'])
        return _meta

    def get_meta(self, media_type, name, imdb_id='', tmdb_id='', year='', season='', episode='', advanced='false'):
        name = re.sub(" +", " ", name)
        meta = {}
        if media_type == 'movie':
            if tmdb_id:
                meta = self.search_movie_id(tmdb_id)
            elif name:
                meta = self.search_movie_name(name, year, advanced=advanced)
        elif media_type == 'tvshow':
            if tmdb_id:
                meta = self.search_tvshow_id(tmdb_id)
            elif name:
                meta = self.search_tvshow_name(name, year, advanced=advanced)
        elif media_type == 'person':
            if tmdb_id:
                meta = self.search_person_id(tmdb_id)
            elif name:
                meta = self.search_person_name(name)
        if meta and 'id' in meta:
            meta = self._format(meta, name)
        return meta

    def getUrl(self, url, page=1, term=''):
        try:
            if term:
                term = term + '&page=' + str(page)
            else:
                term = 'page=' + str(page)
            result = self._call(url, term)
        except:
            return False
        return result

    def _call(self, action, append_to_response=''):
        url = '%s%s?language=%s&api_key=%s' % (self.URL, action, self.lang, self.api_key)
        if append_to_response:
            url += '&%s' % append_to_response
        if 'person' in url:
            url = url.replace('&page=', '')
        oRequestHandler = cRequestHandler(url, ignoreErrors=True)
        name = oRequestHandler.request()
        data = json.loads(name)
        if 'status_code' in data and data['status_code'] == 34:
            return {}
        return data

    def getGenresFromIDs(self, genresID):
        sGenres = []
        for gid in genresID:
            genre = self.TMDB_GENRES.get(gid)
            if genre:
                sGenres.append(genre)
        return sGenres

    def _format_episodes(self, meta, name):
        _meta = {}
        if 'air_date' in meta:
            _meta['aired'] = meta['air_date']
        if 'episode_number' in meta:
            _meta['episode'] = meta['episode_number']
        if 'name' in meta:
            _meta['title'] = meta['name']
        if 'overview' in meta:
            _meta['plot'] = meta['overview']
        if 'production_code' in meta:
            _meta['code'] = str(meta['production_code'])
        if 'season_number' in meta:
            _meta['season'] = meta['season_number']
        if 'still_path' in meta:
            _meta['cover_url'] = self.poster + meta['still_path']
        if 'vote_average' in meta:
            _meta['rating'] = meta['vote_average']
        if 'vote_count' in meta:
            _meta['votes'] = meta['vote_count']
        if 'crew' in meta:
            _meta['writer'] = ''
            _meta['director'] = ''
            _meta['cast'] = ''
            for crew in meta['crew']:
                if crew['department'] == 'Directing':
                    if _meta['director'] != '':
                        _meta['director'] += ' / '
                    _meta['director'] += '%s: %s' % (crew['job'], crew['name'])
                elif crew['department'] == 'Writing':
                    if _meta['writer'] != '':
                        _meta['writer'] += ' / '
                    _meta['writer'] += '%s: %s' % (crew['job'], crew['name'])
        if 'guest_stars' in meta:
            licast = []
            for c in meta['guest_stars']:
                licast.append((c['name'], c['character'], self.poster + str(c['profile_path'])))
            _meta['cast'] = licast
        return _meta

    def get_meta_episodes(self, media_type, name, tmdb_id='', season='', episode='', advanced='false'):
        meta = {}
        if media_type == 'episode' and tmdb_id and season and episode:
            url = '%stv/%s/season/%s?api_key=%s&language=de' % (self.URL, tmdb_id, season, self.api_key)
            Data = cRequestHandler(url, ignoreErrors=True).request()
            if Data:
                meta = json.loads(Data)
        if 'episodes' in meta:
            for e in meta['episodes']:
                if 'episode_number':
                    if e['episode_number'] == int(episode):
                        return self._format_episodes(e, name)
        else:
            return {}
