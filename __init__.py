from pyvod import Collection
from os.path import join, dirname, basename
from ovos_workshop.skills.video_collection import VideoCollectionSkill
from mycroft.skills.core import intent_file_handler
from pyvod import Collection, Media
from os.path import join, dirname, basename
from ovos_workshop.frameworks.cps import CPSMatchType, CPSPlayback, \
    CPSMatchConfidence


class HorrorBabbleSkill(VideoCollectionSkill):
    def __init__(self):
        super().__init__("HorrorBabble")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.AUDIOBOOK,
                                CPSMatchType.VIDEO]
        self.default_image = join(dirname(__file__), "ui", "bg.png")
        self.skill_logo = join(dirname(__file__), "ui", "horrorbabble_icon.png")
        self.skill_icon = join(dirname(__file__), "ui", "horrorbabble_icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.png")
        path = join(dirname(__file__), "res", "HorrorBabble.jsondb")
        logo = join(dirname(__file__), "res",  "horrorbabble_logo.png")
        # load video catalog
        self.media_collection = Collection("HorrorBabble", logo=logo, db_path=path)
        self.media_type = CPSMatchType.AUDIOBOOK
        self.playback_type = CPSPlayback.AUDIO

    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('home.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # matching
    def match_media_type(self, phrase, media_type):
        score = 0

        if self.voc_match(phrase, "audiobook") or\
                media_type == CPSMatchType.AUDIOBOOK:
            score += 10
            if self.voc_match(phrase, "horror"):
                score += 30
                self.CPS_extend_timeout(1)

        if self.voc_match(phrase, "horrorstory"):
            score += 10

        if self.voc_match(phrase, "horrorbabble"):
            score += 80

        return score


def create_skill():
    return HorrorBabbleSkill()
