from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.log import LOG
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from youtube_archivist import YoutubeMonitor


class HorrorBabbleSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super().__init__("HorrorBabble")
        self.supported_media = [MediaType.GENERIC,
                                MediaType.AUDIOBOOK]
        self.skill_icon = join(dirname(__file__), "ui", "horrorbabble_icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.png")
        self.archive = YoutubeMonitor(db_name="horrorbabble",
                                      min_duration=30 * 60,
                                      logger=LOG)

    def initialize(self):
        url = "https://www.youtube.com/channel/UCIvp_SM7UrKuFgR3W77fWcg"
        bootstrap = "https://github.com/JarbasSkills/skill-horrorbabble/raw/dev/bootstrap.json"
        self.archive.bootstrap_from_url(bootstrap)
        self.archive.monitor(url)
        self.archive.setDaemon(True)
        self.archive.start()

    # matching
    def match_skill(self, phrase, media_type):
        score = 0
        if self.voc_match(phrase, "audiobook") or \
                media_type == MediaType.AUDIOBOOK:
            score += 10
            if self.voc_match(phrase, "horror"):
                score += 30
        if self.voc_match(phrase, "horrorstory"):
            score += 10
        if self.voc_match(phrase, "horrorbabble"):
            score += 80
        return score

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "audiobook")
        title = self.remove_voc(title, "horrorbabble")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join(
            [w for w in title.split(" ") if w])  # remove extra spaces

    def calc_score(self, phrase, match, base_score=0):
        score = base_score
        score += 100 * fuzzy_match(phrase.lower(), match["title"].lower())
        return min(100, score)

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
        base_score = self.match_skill(phrase, media_type)
        if self.voc_match(phrase, "horrorbabble"):
            if self.voc_match(phrase, "horrorbabble", exact=True):
                base_score = 100
            yield self.get_playlist(base_score)

        if media_type == MediaType.AUDIOBOOK:
            # only search db if user explicitly requested audiobooks
            phrase = self.normalize_title(phrase)
            for url, video in self.archive.db.items():
                yield {
                    "title": video["title"],
                    "author": "Horror Babble",
                    "match_confidence": self.calc_score(phrase, video, base_score),
                    "media_type": MediaType.AUDIOBOOK,
                    "uri": "youtube//" + url,
                    "playback": PlaybackType.AUDIO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["thumbnail"],
                    "bg_image": self.default_bg
                }

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


def create_skill():
    return HorrorBabbleSkill()
