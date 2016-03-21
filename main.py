import collections
import operator
import random
import configparser

import datetime
import kivy
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar

kivy.require('1.9.1') # replace with your current kivy version !

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ObjectProperty

import logging
# TODO:
# Move up/down
# Ingave spelers & tijd
# Logging, beschrijvend à la: "Om 14h25 wint Krist (king) een punt van Ruther"
# Als tijd op is, finale uitslag opslaan in tekstbestand
# (als ik nog tijd heb): als tijd op is, enkel nog winnaar tonen.


class Contestant(object):
    def __init__(self, name, score=0):
        self.name = name
        self.score = score

    def __unicode__(self):
        return self.name


class Timer(BoxLayout):
    def __init__(self, **kwargs):
        self.time = datetime.timedelta(seconds=0)
        self.is_running = True
        self.color = 'red'
        super(Timer, self).__init__(**kwargs)
        Window.bind(on_key_down=self.check_keyboard_event)
        self.start_clock()

    def start_clock(self):
        Clock.schedule_interval(self.subtract_second, 1.0)
        Clock.unschedule(self.blink)
        self.color = 'red'
        self.is_running = True

    def unpause_clock(self):
        self.ids.timer_box.color = (1,0,0,1)
        self.color = 'red'
        self.start_clock()

    def pause_clock(self):
        Clock.unschedule(self.subtract_second)
        Clock.schedule_interval(self.blink, 0.5)
        self.is_running = False

    def blink(self, dt):
        if self.color == 'red':
            self.ids.timer_box.color = (0,0,0,1)
            self.color = 'black'
        else:
            self.ids.timer_box.color = (1,0,0,1)
            self.color = 'red'

    def stop_clock(self):
        Clock.unschedule(self.subtract_second)
        self.is_running = False
        self.ids.timer_box.text = "The fight is over!"

    def check_keyboard_event(self, keyboard, keycode, text, modifiers, *args, **kwargs):
        if keycode == 32:   # Space is pressed
            if self.is_running:
                self.pause_clock()
            else:
                self.unpause_clock()

    def subtract_second(self, dt):
        self.time -= datetime.timedelta(seconds=1)
        if self.time == datetime.timedelta(seconds=0):
            self.stop_clock()
        self.ids.timer_box.text = "{time}".format(time=self.time)


class CurrentFight(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(CurrentFight, self).__init__(*args, **kwargs)

    def draw(self, king, contender):
        self.ids.king.text = "{name}".format(name=king.name)
        self.ids.contender.text = contender.name

class RankingHeader(BoxLayout):
    pass


class RankingLine(BoxLayout):
    # def __init__(self, *args, **kwargs):
    #     super(RankingLine, self).__init__(*args, **kwargs)
    pass



class RankingBody(BoxLayout):
    def draw(self, contestants):
        self.children[0].clear_widgets()    # Clear children of BoxLayout
        ranking = sorted(contestants.copy(), key=operator.attrgetter('score'), reverse=True)
        pos = 1
        previous_score = ranking[0].score
        for player in ranking:
            if player.score < previous_score:
                pos += 1
            line = RankingLine()
            line.ids.position.text = "{pos}.".format(pos=pos)
            line.ids.name.text = player.name
            line.ids.score.text = str(player.score)
            self.ids.ranking_body.add_widget(line)
            previous_score = player.score


class Ranking(BoxLayout):
    pass


class NextUpLine(BoxLayout):
    pass


class NextUp(BoxLayout):
    def draw(self, queue):
        self.ids.next_up_body.clear_widgets()

        for contestant in queue:
            lbl = NextUpLine()
            lbl.ids.name.text = contestant.name
            self.ids.next_up_body.add_widget(lbl)
            # self.ids.next_up_body.add_widget(Button(text="Move up"))
            # self.ids.next_up_body.add_widget(Button(text="Move down"))


class Root(BoxLayout):
    def __init__(self, contestants, start_timer, **kwargs):
        super(Root, self).__init__(**kwargs)
        self.contestants = contestants
        self.start_timer = int(start_timer)
        self.ids.timer.time = datetime.timedelta(seconds=self.start_timer)
        self.update()

    def update(self):
        # self.ids.current_fight.clear_widgets()
        self.draw_current_fight(self.contestants[0], self.contestants[1])
        self.draw_ranking(self.contestants)
        self.draw_up_next(self.contestants)

    def draw_current_fight(self, king, challenger):
        self.ids.current_fight.draw(king, challenger)

    def draw_ranking(self, rankings):
        self.ids.ranking.ids.ranking_body.draw(rankings)

    def draw_up_next(self, queue):
        self.ids.next_up.draw(queue[2:])

    def add_point_for_king(self):
        self.contestants[0].score += 1
        self.update()

    def substract_point_for_king(self):
        self.contestants[0].score -= 1
        self.update()

    def add_point_for_challenger(self):
        self.contestants[1].score += 1
        logging.info("{challenger} wint een punt van {king} en heeft nu {score} punt(en).".format(
            challenger=self.contestants[1].name,
            king=self.contestants[0].name,
            score=self.contestants[1].score)
        )
        # King moved back to queue
        self.contestants += [self.contestants.pop(0)]

        self.update()

    def substract_point_for_challenger(self):
        self.contestants[1].score -= 1
        self.update()

    def move_king_to_queue(self):
        self.contestants += [self.contestants.pop(0)]
        self.update()

    def move_challenger_back_to_queue(self):
        self.contestants += [self.contestants.pop(1)]
        self.update()


class ScoreboardApp(App):
    def __init__(self, *args, **kwargs):
        super(ScoreboardApp, self).__init__(*args, **kwargs)
        # Read initial values (time & contestants)

        parser = configparser.ConfigParser()
        parser.read('initial_values.ini')
        self.contestants = [Contestant(name=name) for name in parser.get("contestants", "names").split("\n")]
        random.shuffle(self.contestants)
        self.start_timer = parser.get('time', 'time_remaining')

    def build(self):
        return Root(self.contestants, self.start_timer)


if __name__ == '__main__':
    logging.basicConfig(filename='.\wedstrijdverslag.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    ScoreboardApp().run()
