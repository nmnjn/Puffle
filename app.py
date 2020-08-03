import json
import random
import re
import schedule
import time
import requests
from threading import Timer
from pathlib import Path

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

browser: webdriver.Chrome = None
config = None
timetable = None
active_meeting = None
uuid_regex = r"\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b"
hangup_thread: Timer = None

MAIL_ENDPOINT = "https://us-central1-puffle.cloudfunctions.net/mail"
MESSAGE_ENDPOINT = "https://us-central1-puffle.cloudfunctions.net/message"


class Meeting:
    def __init__(self, started_at, id):
        self.started_at = started_at
        self.id = id


class Channel:
    def __init__(self, name, meetings):
        self.name = name
        self.meetings = meetings

    def __str__(self):
        return self.name

    def get_elem(self, parent):
        try:
            channel_elem = parent.find_element_by_css_selector(f"ul>ng-include>li[data-tid*='channel-{self.name}-li']")
        except exceptions.NoSuchElementException:
            return None

        return channel_elem


class Team:
    def __init__(self, name, elem, channels=None):
        if channels is None:
            channels = []
        self.name = name
        self.elem = elem
        self.channels = channels

    def __str__(self):
        channel_string = '\n\t'.join([str(channel) for channel in self.channels])

        return f"{self.name}\n\t{channel_string}"

    def expand_channels(self):
        try:
            elem = self.elem.find_element_by_css_selector("div[class='channels']")
        except exceptions.NoSuchElementException:
            try:
                self.elem.click()
                elem = self.elem.find_element_by_css_selector("div[class='channels']")
            except exceptions.NoSuchElementException:
                return None
        return elem

    def init_channels(self):
        channels_elem = self.expand_channels()

        channel_elems = channels_elem.find_elements_by_css_selector("ul>ng-include>li")

        channel_names = [channel_elem.get_attribute("data-tid") for channel_elem in channel_elems]
        channel_names = [channel_name[channel_name.find('-channel-') + 9:channel_name.rfind("-li")] for channel_name
                         in
                         channel_names if channel_name is not None]

        self.channels = [Channel(channel_name, []) for channel_name in channel_names]

    def update_meetings(self):
        channels = self.expand_channels()

        for channel in self.channels:

            channel_elem = channel.get_elem(channels)
            try:
                active_meeting_elem = channel_elem.find_element_by_css_selector(
                    "a>active-calls-counter[is-meeting='true']")
            except exceptions.NoSuchElementException:
                continue

            active_meeting_elem.click()

            if wait_till_found("button[ng-click='ctrl.joinCall()']", 60) is None:
                continue

            join_meeting_elems = browser.find_elements_by_css_selector("button[ng-click='ctrl.joinCall()']")

            meeting_ids = []
            for join_meeting_elem in join_meeting_elems:
                try:
                    uuid = re.search(uuid_regex, join_meeting_elem.get_attribute('track-data'))
                    if uuid is None:
                        continue

                    meeting_ids.append(uuid.group(0))
                except exceptions.StaleElementReferenceException:
                    continue

            # remove duplicates
            meeting_ids = list(dict.fromkeys(meeting_ids))

            for meeting_id in meeting_ids:
                if meeting_id not in [meeting.id for meeting in channel.meetings]:
                    channel.meetings.append(Meeting(time.time(), meeting_id))

    def update_elem(self):
        self.elem = browser.find_element_by_css_selector(
            f"ul>li[role='treeitem'][class='match-parent team left-rail-item-kb-l2']>div[data-tid='team-{self.name}-li']")


def load_config(url):
    global config
    with open(url + '/config.json') as json_data_file:
        config = json.load(json_data_file)

def load_time_table(url):
    global timetable
    with open(url + '/timetable.json') as json_data_file:
        timetable = json.load(json_data_file)


def send_email(success, channel, team):
    if 'email-notification' in config and config['email-notification']:
        if 'p-email' in config and config['p-email'] != "":
            r = requests.post(url = MAIL_ENDPOINT, data = {"success": success, "email": config['p-email'], "channel": channel, "team": team})
            print(r.text)
        else:
            print("** Missing primary email: please enter your primary email in configs and restart the application. **")
    return


def send_message(success, channel, team):
    if 'phone-notification' in config and config['phone-notification']:
        if 'phone' in config and config['phone'] != "":
            r = requests.post(url = MESSAGE_ENDPOINT, data = {"success": success, "phone": config['phone'], "channel": channel, "team": team})
            print(r.text)
        else:
            print("** Missing phone number: please enter your phone-number in configs and restart the application. **")
    return 


def wait_till_found(sel, timeout):
    try:
        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, sel))
        WebDriverWait(browser, timeout).until(element_present)

        return browser.find_element_by_css_selector(sel)
    except exceptions.TimeoutException:
        print("Timeout waiting for element.")
        return None

def wait_till_clickable(sel, timeout):
    try:
        element_present = EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
        WebDriverWait(browser, timeout).until(element_present)
        return browser.find_element_by_css_selector(sel)
    except exceptions.TimeoutException:
        print("Timeout waiting for element.")
        return None


def get_teams():
    # find all team names
    team_elems = browser.find_elements_by_css_selector(
        "ul>li[role='treeitem']>div[sv-element]")
    team_names = [team_elem.get_attribute("data-tid") for team_elem in team_elems]
    team_names = [team_name[team_name.find('team-') + 5:team_name.rfind("-li")] for team_name in team_names]

    team_list = [Team(team_names[i], team_elems[i], None) for i in range(len(team_elems))]
    return team_list



def hangup():
    try:
        hangup_btn = browser.find_element_by_css_selector("button[data-tid='call-hangup']")
        hangup_btn.click()

        if hangup_thread:
            hangup_thread.cancel()
    except exceptions.NoSuchElementException:
        return


def join_meeting(subject):

    global browser, config, active_meeting, hangup_thread

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    browser.get("https://teams.microsoft.com")

    if config['email'] != "" and config['password'] != "":
        login_email = wait_till_found("input[type='email']", 30)
        if login_email is not None:
            login_email.send_keys(config['email'])
            time.sleep(2)

        # find the element again to avoid StaleElementReferenceException
        login_email = wait_till_found("input[type='email']", 5)
        if login_email is not None:
            login_email.send_keys(Keys.ENTER)

        login_pwd = wait_till_found("input[type='password']", 30)
        if login_pwd is not None:
            login_pwd.send_keys(config['password'])
            time.sleep(2)

        # find the element again to avoid StaleElementReferenceException
        login_pwd = wait_till_found("input[type='password']", 5)
        if login_pwd is not None:
            login_pwd.send_keys(Keys.ENTER)

        time.sleep(2)
        keep_logged_in = wait_till_found("input[id='idBtn_Back']", 5)
        if keep_logged_in is not None:
            keep_logged_in.click()
        
        time.sleep(2)
        skip_web_app = wait_till_found("a[data-tid='early-desktop-promo-use-web']", 5)
        if skip_web_app is not None:
            skip_web_app.click()

        # time.sleep(2)
        # settings_button = wait_till_found("button[id='school-app-settings-button']", 5)
        # if settings_button is not None:
        #     settings_button.click()

        # time.sleep(2)
        # switch_view = wait_till_found("button[data-tid='school-app-settings-switch-view']", 5)
        # if switch_view is not None:
        #     switch_view.click()

    print("Waiting for teams to connect...")

    if wait_till_found("div[data-tid='team-channel-list']", 60 * 5) is None:
        exit(1)

    teams = get_teams()
    if len(teams) == 0:
        print("Nothing found, is Teams in grid mode? Please change teams view to list mode and try again.")
        exit(1)

    for team in teams:
        team.init_channels()
        team.update_meetings()

    print("\nFound Teams and Channels: ")
    for team in teams:
        print(team)


    print("Joining " + subject['team'] + " - " + subject['channel'])

    meeting_to_join = Meeting(-1, None) if active_meeting is None else active_meeting
    meeting_team = None
    meeting_channel = None

    for team in teams:
        if team.name == subject['team']:
            for channel in team.channels:
                if channel.name == subject['channel']:
                    for meeting in channel.meetings:
                        if meeting.started_at > meeting_to_join.started_at:
                            meeting_to_join = meeting
                            meeting_team = team
                            meeting_channel = channel

    if meeting_team is None:
        print("No meeting found to join.")
        send_email("fail", subject['channel'], subject['team'])
        send_message("fail", subject['channel'], subject['team'])
        return False

    hangup()

    channels_elem = meeting_team.expand_channels()

    meeting_channel.get_elem(channels_elem).click()

    print(meeting_to_join.id)

    join_btn = wait_till_found(f"button[data-tid='join-btn-{meeting_to_join.id}']", 60)
    if join_btn is None:
        print("unable to join meeting..")
        send_email("fail", subject['channel'], subject['team'])
        send_message("fail", subject['channel'], subject['team'])
        return False

    join_btn.click()

    join_now_btn = wait_till_found("button[data-tid='prejoin-join-button']", 30)
    if join_now_btn is None:
        print("unable to join meeting..")
        send_email("fail", subject['channel'], subject['team'])
        send_message("fail", subject['channel'], subject['team'])
        return False

    # turn camera off
    video_btn = browser.find_element_by_css_selector("toggle-button[data-tid='toggle-video']>div>button")
    video_is_on = video_btn.get_attribute("aria-pressed")
    if video_is_on == "true":
        video_btn.click()

    # turn mic off
    audio_btn = browser.find_element_by_css_selector("toggle-button[data-tid='toggle-mute']>div>button")
    audio_is_on = audio_btn.get_attribute("aria-pressed")
    if audio_is_on == "true":
        audio_btn.click()

    if 'random_delay' in config and config['random_delay']:
        delay = random.randrange(10, 31, 1)
        print(f"Wating for {delay}s")
        time.sleep(delay)

    # find the element again to avoid StaleElementReferenceException
    join_now_btn = wait_till_found("button[data-tid='prejoin-join-button']", 30)
    if join_now_btn is None:
        print("unable to join meeting..")
        print("Unable to find the join button..")
        send_email("fail", subject['channel'], subject['team'])
        send_message("fail", subject['channel'], subject['team'])
        return False

    join_now_btn.click()

    browser.find_element_by_css_selector("span[data-tid='appBarText-Teams']").click()

    active_meeting = meeting_to_join

    print("Joined " + subject['team'] + " - " + subject['channel'])
    send_email("success", subject['channel'], subject['team'])
    send_message("success", subject['channel'], subject['team'])

    if subject['duration'] > 0:
        hangup_thread = Timer(subject['duration']*60, hangup)
        hangup_thread.start()

    for team in teams:
        team.update_elem()

    return True


def schedule_call(day, subject):
    if day == 'Monday':
        schedule.every().monday.at(subject['time']).do(join_meeting, subject=subject)
    if day == 'Tuesday':
        schedule.every().tuesday.at(subject['time']).do(join_meeting, subject=subject)
    if day == 'Wednesday':
        schedule.every().wednesday.at(subject['time']).do(join_meeting, subject=subject)
    if day == 'Thursday':
        schedule.every().thursday.at(subject['time']).do(join_meeting, subject=subject)
    if day == 'Friday':
        schedule.every().friday.at(subject['time']).do(join_meeting, subject=subject)
    if day == 'Saturday':
        schedule.every().saturday.at(subject['time']).do(join_meeting, subject=subject)


def main():

    global browser, config, timetable

    path = str(Path().absolute())

    url = path + '/config'

    load_config(url) 

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    browser.get("https://teams.microsoft.com")

    if config['email'] != "" and config['password'] != "":
        login_email = wait_till_found("input[type='email']", 60)
        if login_email is not None:
            login_email.send_keys(config['email'])
            time.sleep(2)

        # find the element again to avoid StaleElementReferenceException
        login_email = wait_till_found("input[type='email']", 60)
        if login_email is not None:
            login_email.send_keys(Keys.ENTER)

        login_pwd = wait_till_found("input[type='password']", 60)
        if login_pwd is not None:
            login_pwd.send_keys(config['password'])
            time.sleep(2)

        # find the element again to avoid StaleElementReferenceException
        login_pwd = wait_till_found("input[type='password']", 60)
        if login_pwd is not None:
            login_pwd.send_keys(Keys.ENTER)

        time.sleep(2)
        keep_logged_in = wait_till_found("input[id='idBtn_Back']", 60)
        if keep_logged_in is not None:
            keep_logged_in.click()
        
        time.sleep(2)
        skip_web_app = wait_till_found("a[data-tid='early-desktop-promo-use-web']", 60)
        if skip_web_app is not None:
            skip_web_app.click()

    print("Waiting for teams to connect...")
    if wait_till_found("div[data-tid='team-channel-list']", 60 * 5) is None:
        exit(1)

    teams = get_teams()
    if len(teams) == 0:
        print("I was not able to find any teams! If teams is in grid mode, please change it to list mode!")
        exit(1)

    for team in teams:
        team.init_channels()
        team.update_meetings()

    print("\nFound the following teams and channels: ")

    # send_email(True, "General", "VII SEM BTech (CSE) STA SECTION E")
    # send_message(True, "General", "VII SEM BTech (CSE) STA SECTION E")

    for team in teams:
        print(team)

    browser.close()
    load_time_table(url)

    print("\n")

    for day in timetable:
            for subject in timetable[day]:
                schedule_call(day, subject)
                print('Scheduling ' + subject['team'] + ' - ' + subject['channel'] + ' at ' + subject['time'] + ' every ' + day +'!')


    print("\n*** Please do not close this window! *** \n\n")
                
    while 1:
        time.sleep(1)
        schedule.run_pending()


if __name__ == "__main__":
    main()
