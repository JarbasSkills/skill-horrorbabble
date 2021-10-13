from os.path import join, dirname

import biblioteca
from mycroft.skills.core import intent_file_handler
from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.log import LOG
from ovos_workshop.skills.common_play import ocp_search
from ovos_workshop.skills.video_collection import VideoCollectionSkill
from pyvod import Collection


class HorrorBabbleSkill(VideoCollectionSkill):

    def __init__(self):
        super().__init__("HorrorBabble")
        self.supported_media = [MediaType.GENERIC,
                                MediaType.AUDIOBOOK]
        self.default_image = join(dirname(__file__), "ui", "bg.png")
        self.skill_icon = join(dirname(__file__), "ui",
                               "horrorbabble_icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.png")
        base_folder = biblioteca.download("ytcat_horrorbabble")
        path = join(base_folder, "horrorbabble.jsondb")
        LOG.info(path)
        self.skill_logo = join(dirname(__file__), "res",
                               "horrorbabble_logo.png")
        # load video catalog
        self.media_collection = Collection("horrorbabble",
                                           logo=self.skill_logo,
                                           db_path=path)

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # matching
    def get_base_score(self, phrase, media_type):
        score = 0

        if self.voc_match(phrase, "audiobook") or \
                media_type == MediaType.AUDIOBOOK:
            score += 10
            if self.voc_match(phrase, "horror"):
                score += 40

        if self.voc_match(phrase, "horrorstory"):
            score += 15

        if self.voc_match(phrase, "horrorbabble"):
            score += 90

        return score

    @ocp_search()
    def ocp_horror_stories(self, phrase, media_type):
        score = self.get_base_score(phrase, media_type)

        if score < 50:
            return
        pl = [
            {
                "match_confidence": score,
                "media_type": MediaType.AUDIOBOOK,
                "uri": "youtube//" + entry["url"],
                "playback": PlaybackType.AUDIO,
                "image": entry.get("thumbnail") or self.skill_logo,
                "bg_image": self.default_bg,
                "skill_icon": self.skill_icon,
                "title": entry["title"]
            } for entry in self.videos  # VideoCollectionSkill property
        ]
        if pl:
            return [{
                "match_confidence": score,
                "media_type": MediaType.AUDIOBOOK,
                "playlist": pl,
                "playback": PlaybackType.AUDIO,
                "skill_icon": self.skill_icon,
                "image": self.skill_logo,
                "bg_image": self.default_bg,
                "title": f"HorrorBabble Collection (Playlist)"
            }]


def create_skill():
    return HorrorBabbleSkill()
