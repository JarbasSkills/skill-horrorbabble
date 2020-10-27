from mycroft.skills.common_play_skill import CommonPlaySkill, \
    CPSMatchLevel, CPSTrackStatus, CPSMatchType
from mycroft.skills.core import intent_file_handler
from mycroft.util.parse import fuzzy_match, match_one
from pyvod import Collection, Media
from os.path import join, dirname
import random
from json_database import JsonStorageXDG
import datetime


def datestr2ts(datestr):
    y = int(datestr[:4])
    m = int(datestr[4:6])
    d = int(datestr[-2:])
    dt = datetime.datetime(y, m, d)
    return dt.timestamp()


class HorrorBabbleSkill(CommonPlaySkill):

    def __init__(self):
        super().__init__("HorrorBabble")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.AUDIOBOOK,
                                CPSMatchType.VIDEO]

        path = join(dirname(__file__), "res", "HorrorBabble.jsondb")
        # load video catalog
        videos = Collection("HorrorBabble",
                            logo=join(dirname(__file__), "res",
                                      "horrorbabble_logo.png"),
                            db_path=path)
        self.videos = [ch.as_json() for ch in videos.entries]
        print(self.videos)

        self.sort_videos()

    def sort_videos(self):
        # this will filter private and live videos
        videos = [v for v in self.videos
                  if v.get("upload_date") and not v.get("is_live")]
        # sort by upload date
        videos = sorted(videos,
                             key=lambda kv: datestr2ts(kv["upload_date"]),
                             reverse=True)
        # live streams before videos
        self.videos =  [v for v in self.videos if v.get("is_live")] + videos
        print(self.videos)

    def initialize(self):
        self.add_event('skill-horrorbabble.jarbasskills.home',
                       self.handle_homescreen)
        self.gui.register_handler("skill-horrorbabble.jarbasskills.play_event",
                                  self.play_video_event)
        self.gui.register_handler(
            "skill-horrorbabble.jarbasskills.clear_history",
            self.handle_clear_history)

    def get_intro_message(self):
        self.speak_dialog("intro")

    @intent_file_handler('horrorbabblehome.intent')
    def handle_homescreen_utterance(self, message):
        self.handle_homescreen(message)

    # homescreen
    def handle_homescreen(self, message):
        self.gui.clear()
        self.gui["mytvtogoHomeModel"] = self.videos
        self.gui["historyModel"] = JsonStorageXDG("horrorbabble-history").get(
            "model", [])
        self.gui.show_page("Homescreen.qml", override_idle=True)

    # play via GUI event
    def play_video_event(self, message):
        video_data = message.data["modelData"]
        self.play_horrorbabble(video_data)

    # clear history GUI event
    def handle_clear_history(self, message):
        historyDB = JsonStorageXDG("horrorbabble-history")
        historyDB["model"] = []
        historyDB.store()

    # common play
    def add_to_history(self, video_data):
        # History
        historyDB = JsonStorageXDG("horrorbabble-history")
        if "model" not in historyDB:
            historyDB["model"] = []
        historyDB["model"].append(video_data)
        historyDB.store()
        self.gui["historyModel"] = historyDB["model"]

    def play_horrorbabble(self, video_data):
        # TODO audio only
        # if self.gui.connected:
        #    ...
        # else:
        #    self.audioservice.play(video_data["url"])
        # add to playback history

        self.add_to_history(video_data)
        # play video
        video = Media.from_json(video_data)
        url = str(video.streams[0])
        self.gui.play_video(url, video.name)

    def match_media_type(self, phrase, media_type):
        match = None
        score = 0

        if self.voc_match(phrase,
                          "video") or media_type == CPSMatchType.VIDEO:
            score += 0.05
            match = CPSMatchLevel.GENERIC

        if self.voc_match(phrase, "audiobook") or\
                media_type == CPSMatchType.AUDIOBOOK:
            score += 0.1
            match = CPSMatchLevel.CATEGORY

        if self.voc_match(phrase,
                          "horrorstory"):
            score += 0.1
            match = CPSMatchLevel.CATEGORY

        if self.voc_match(phrase, "horrorbabble"):
            score += 0.3
            match = CPSMatchLevel.TITLE

        return match, score

    def CPS_match_query_phrase(self, phrase, media_type):
        leftover_text = phrase
        best_score = 0

        # see if media type is in query, base_score will depend if "scifi"
        # or "video" is in query
        match, base_score = self.match_media_type(phrase, media_type)

        videos = list(self.videos)

        best_video = random.choice(videos)

        # score video data
        for ch in videos:
            score = 0
            # score tags
            tags = list(set(ch.get("tags", [])))
            if tags:
                # tag match bonus
                for tag in tags:
                    tag = tag.lower().strip()
                    if tag in phrase:
                        match = CPSMatchLevel.CATEGORY
                        score += 0.1
                        leftover_text = leftover_text.replace(tag, "")

            # score description
            words = ch.get("description", "").split(" ")
            for word in words:
                if len(word) > 4 and word in leftover_text:
                    score += 0.05

            if score > best_score:
                best_video = ch
                best_score = score

        # match video name
        for ch in videos:
            title = ch["title"]

            score = fuzzy_match(leftover_text, title)
            if score >= best_score:
                # TODO handle ties
                match = CPSMatchLevel.TITLE
                best_video = ch
                best_score = score
                leftover_text = title

        if not best_video:
            self.log.debug("No HorrorBabble matches")
            return None

        if best_score < 0.6:
            self.log.debug("Low score, randomizing results")
            best_video = random.choice(videos)

        score = base_score + best_score

        if self.voc_match(phrase, "horrorbabble"):
            score += 0.15

        if score >= 0.85:
            match = CPSMatchLevel.EXACT
        elif score >= 0.7:
            match = CPSMatchLevel.MULTI_KEY
        elif score >= 0.5:
            match = CPSMatchLevel.TITLE

        self.log.debug("Best HorrorBabble video: " + best_video["title"])

        if match is not None:
            return (leftover_text, match, best_video)
        return None

    def CPS_start(self, phrase, data):
        self.play_horrorbabble(data)


def create_skill():
    return HorrorBabbleSkill()
