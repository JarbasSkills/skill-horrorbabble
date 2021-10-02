from os.path import join, dirname

import biblioteca
from mycroft.skills.core import intent_file_handler
from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_workshop.skills.video_collection import VideoCollectionSkill
from pyvod import Collection


class HorrorBabbleSkill(VideoCollectionSkill):

    def __init__(self):
        super().__init__("HorrorBabble")
        self.supported_media = [MediaType.GENERIC,
                                MediaType.AUDIOBOOK,
                                MediaType.VIDEO]
        self.default_image = join(dirname(__file__), "ui", "bg.png")
        self.skill_logo = join(dirname(__file__), "ui",
                               "horrorbabble_icon.png")
        self.skill_icon = join(dirname(__file__), "ui",
                               "horrorbabble_icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.png")
        base_folder = biblioteca.download("ytcat_horrorbabble")
        path = join(base_folder, "horrorbabble.jsondb")
        logo = join(dirname(__file__), "res", "horrorbabble_logo.png")
        # load video catalog
        self.media_collection = Collection("horrorbabble", logo=logo,
                                           db_path=path)
        self.media_type = MediaType.AUDIOBOOK
        self.playback_type = PlaybackType.AUDIO

    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # matching
    def match_media_type(self, phrase, media_type):
        score = 0

        if self.voc_match(phrase, "audiobook") or \
                media_type == MediaType.AUDIOBOOK:
            score += 10
            if self.voc_match(phrase, "horror"):
                score += 30
                self.extend_timeout(1)

        if self.voc_match(phrase, "horrorstory"):
            score += 10

        if self.voc_match(phrase, "horrorbabble"):
            score += 80

        return score


def create_skill():
    return HorrorBabbleSkill()
