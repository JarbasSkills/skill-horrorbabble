from os.path import join, dirname
import random

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.log import LOG
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from youtube_archivist import YoutubeMonitor


class HorrorBabbleSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, *kwargs):
        self.supported_media = [MediaType.AUDIOBOOK]
        self.skill_icon = join(dirname(__file__), "ui", "horrorbabble_icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.png")
        self.archive = YoutubeMonitor(db_name="horrorbabble",
                                      min_duration=30 * 60,
                                      logger=LOG)
        super().__init__(*args, *kwargs)

    def initialize(self):
        self._sync_db()
        self.load_ocp_keywords()

    def _sync_db(self):
        bootstrap = "https://github.com/JarbasSkills/skill-horrorbabble/raw/dev/bootstrap.json"
        self.archive.bootstrap_from_url(bootstrap)
        self.schedule_event(self._sync_db, random.randint(3600, 24 * 3600))

    def load_ocp_keywords(self):
        book_names = []
        book_authors = []
        for url, data in self.archive.db.items():
            t = data["title"].split("/")[0].strip()
            if " by " in t:
                title, author = t.split(" by ")
                title = title.replace('"', "").strip()
                author = author.split("(")[0].strip()
                book_names.append(title)
                book_authors.append(author)
                if " " in author:
                    book_authors += author.split(" ")
            elif t.startswith('"') and t.endswith('"'):
                book_names.append(t[1:-1])
            else:
                book_names.append(t)
        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "book_author",
                                  list(set(book_authors)))
        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "book_name",
                                  list(set(book_names)))
        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "audiobook_streaming_provider",
                                  ["HorrorBabble", "Horror Babble"])
        
    def get_playlist(self, score=50):
        return {
            "match_confidence": score,
            "media_type": MediaType.AUDIOBOOK,
            "playlist": self.featured_media(),
            "playback": PlaybackType.AUDIO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "bg_image": self.default_bg,
            "title": "Horror Babble (Playlist)",
            "author": "Horror Babble"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = 15 if media_type == MediaType.AUDIOBOOK else 0
        entities = self.ocp_voc_match(phrase)

        author = entities.get("book_author")
        title = entities.get("book_name")
        source = entities.get('audiobook_streaming_provider','')
        
        if source == 'HorrorBabble':
            base_score += 30
            
        candidates = list(self.archive.db.values())
        if title or author:
                
            if author:
                base_score += 30
                candidates = [video for video in candidates 
                              if author.lower() in video["title"].lower()]
            if title:
                base_score += 30
                candidates = [video for video in candidates 
                              if title.lower() in video["title"].lower()]
                
            for video in candidates:
                yield {
                        "title": video["title"],
                        "author": author or "Horror Babble",
                        "match_confidence": min(100, base_score),
                        "media_type": MediaType.AUDIOBOOK,
                        "uri": "youtube//" + url,
                        "playback": PlaybackType.AUDIO,
                        "skill_icon": self.skill_icon,
                        "skill_id": self.skill_id,
                        "image": video["thumbnail"],
                        "bg_image": self.default_bg
                    }

        elif source == 'HorrorBabble':
            yield self.get_playlist(min(100, base_score))


    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "image": video["thumbnail"],
            "match_confidence": 70,
            "media_type": MediaType.AUDIOBOOK,
            "uri": "youtube//" + url,
            "playback": PlaybackType.AUDIO,
            "skill_icon": self.skill_icon,
            "bg_image": video["thumbnail"],
            "skill_id": self.skill_id
        } for url, video in self.archive.db.items()]
