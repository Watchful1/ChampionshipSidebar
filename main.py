#!/usr/bin/python3

import praw
import os
import logging.handlers
import time
import sys
import configparser
import signal
import requests
import json
import traceback
import datetime

### Config ###
LOG_FOLDER_NAME = "logs"
SUBREDDIT = "Championship"
USER_AGENT = "ChampionshipSidebar (by /u/Watchful1)"
LOOP_TIME = 15*60

### Logging setup ###
LOG_LEVEL = logging.DEBUG
if not os.path.exists(LOG_FOLDER_NAME):
    os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 256

log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)
if LOG_FILENAME is not None:
	log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAXSIZE, backupCount=LOG_FILE_BACKUPCOUNT)
	log_formatter_file = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	log_fileHandler.setFormatter(log_formatter_file)
	log.addHandler(log_fileHandler)


teams = [{'team': 'Newcastle United FC', 'name': 'Newcastle', 'url': 'https://www.reddit.com/r/NUFC'}
	,{'team': 'Brighton & Hove Albion', 'name': 'Brighton', 'url': 'https://www.reddit.com/r/BrightonHoveAlbion'}
	,{'team': 'Huddersfield Town', 'name': 'Huddersfield', 'url': 'http://www.reddit.com/r/huddersfieldtownfc'}
	,{'team': 'Reading', 'name': 'Reading', 'url': 'http://www.reddit.com/r/Urz'}
	,{'team': 'Leeds United', 'name': 'Leeds', 'url': 'http://www.reddit.com/r/LeedsUnited'}
	,{'team': 'Sheffield Wednesday', 'name': 'Sheff Wed', 'url': 'http://www.reddit.com/r/SheffieldWednesday'}
	,{'team': 'Norwich City FC', 'name': 'Norwich', 'url': 'https://www.reddit.com/r/NorwichCity'}
	,{'team': 'Derby County', 'name': 'Derby', 'url': 'http://www.reddit.com/r/DerbyCounty'}
	,{'team': 'Fulham FC', 'name': 'Fulham', 'url': 'http://www.reddit.com/r/fulhamfc'}
	,{'team': 'Barnsley FC', 'name': 'Barnsley', 'url': 'https://www.reddit.com/r/BarnsleyFC'}
	,{'team': 'Preston North End', 'name': 'Preston', 'url': 'http://www.reddit.com/r/pne'}
	,{'team': 'Birmingham City', 'name': 'Birmingham', 'url': 'http://www.reddit.com/r/bcfc'}
	,{'team': 'Ipswich Town', 'name': 'Ipswich Town', 'url': 'http://www.reddit.com/r/IpswichTownFC'}
	,{'team': 'Cardiff City FC', 'name': 'Cardiff', 'url': 'http://www.reddit.com/r/bluebirds'}
	,{'team': 'Brentford FC', 'name': 'Brentford', 'url': 'http://www.reddit.com/r/Brentford'}
	,{'team': 'Aston Villa FC', 'name': 'Aston Villa', 'url': 'https://www.reddit.com/r/avfc'}
	,{'team': 'Nottingham Forest', 'name': 'Nottm Forest', 'url': 'http://www.reddit.com/r/nffc'}
	,{'team': 'Wolverhampton Wanderers FC', 'name': 'Wolves', 'url': 'http://www.reddit.com/r/WWFC'}
	,{'team': 'Queens Park Rangers', 'name': 'QPR', 'url': 'http://www.reddit.com/r/superhoops'}
	,{'team': 'Bristol City', 'name': 'Bristol City', 'url': 'http://www.reddit.com/r/BristolCity'}
	,{'team': 'Blackburn Rovers FC', 'name': 'Blackburn', 'url': 'http://www.reddit.com/r/brfc'}
	,{'team': 'Burton Albion FC', 'name': 'Burton', 'url': 'https://www.reddit.com/r/BurtonFC'}
	,{'team': 'Wigan Athletic FC', 'name': 'Wigan', 'url': 'https://www.reddit.com/r/latics'}
	,{'team': 'Rotherham United', 'name': 'Rotherham', 'url': 'http://www.reddit.com/r/RotherhamUtd'}
]

default = {'team': 'Unknown', 'name': 'Unknown', 'url': 'https://www.reddit.com/r/Championship'}

def teamToName(team):
	for teamHash in teams:
		if team == teamHash['team']:
			return teamHash
	log.warning("Could not parse team: "+team)
	return default


def getSchedule():
	try:
		resp = requests.get(url="http://api.football-data.org/v1/competitions/427/fixtures", headers={'User-Agent': USER_AGENT})
		jsonData = json.loads(resp.text)
		games = jsonData['fixtures']
		gamesOut = []
		dates = set()
		for game in games:
			gameDate = datetime.datetime.strptime(game['date'], "%Y-%m-%dT%H:%M:%SZ")
			if gameDate.date() >= datetime.datetime.utcnow().date():
				dates.add(gameDate.date())
				if len(dates) > 2 and len(gamesOut) >= 10:
					return gamesOut
				gamesOut.append({'date': gameDate
						,'home': teamToName(game['homeTeamName'])
						,'away': teamToName(game['awayTeamName'])
					})
	except Exception as err:
		log.warning("Exception parsing schedule")
		log.warning(traceback.format_exc())
		return None


def getTable():
	try:
		resp = requests.get(url="http://api.football-data.org/v1/soccerseasons/427/leagueTable", headers={'User-Agent': USER_AGENT})
		jsonData = json.loads(resp.text)
		table = jsonData['standing']
		tableOut = []
		for team in table:
			tableOut.append({'team': teamToName(team['teamName'])
					,'gamesPlayed': team['playedGames']
					,'goalDifference': team['goalDifference']
					,'points': team['points']
				})
		return tableOut
	except Exception as err:
		log.warning("Exception parsing schedule")
		log.warning(traceback.format_exc())
		return None


def signal_handler(signal, frame):
	log.info("Handling interupt")
	sys.exit(0)

log.debug("Connecting to reddit")

signal.signal(signal.SIGINT, signal_handler)

once = False
debug = False
user = None
if len(sys.argv) >= 2:
	user = sys.argv[1]
	for arg in sys.argv:
		if arg == 'once':
			once = True
		elif arg == 'debug':
			debug = True
else:
	log.error("No user specified, aborting")
	sys.exit(0)


try:
	r = praw.Reddit(
		user
		,user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error("User "+user+" not in praw.ini, aborting")
	sys.exit(0)

username = str(r.user.me())

log.info("Logged into reddit as /u/"+username)

while True:
	startTime = time.perf_counter()
	log.debug("Starting run")
	skip = False

	games = getSchedule()
	if games is None:
		log.warning("Could not parse schedule, skipping run")
		skip = True

	table = getTable()
	if table is None:
		log.warning("Could not parse table, skipping run")
		skip = True

	if not skip:
		subreddit = r.subreddit(SUBREDDIT)
		description = subreddit.description
		begin = description[0:description.find("#Championship Table")]
		end = description[description.find("#Top Scorers"):]

		output = ["#Championship Table\n"]
		output.append("Pos	|	Team	|	Pld	|	GD	|	Pts\n")
		output.append("|--|--|--|--|--|\n")
		count = 1
		for team in table:
			output.append("|")
			output.append(str(count))
			output.append("|[")
			output.append(team['team']['name'])
			output.append("](")
			output.append(team['team']['url'])
			output.append(")|")
			output.append(str(team['gamesPlayed']))
			output.append("|")
			output.append(str(team['goalDifference']))
			output.append("|")
			output.append(str(team['points']))
			output.append("|")
			output.append("\n")

			count += 1
		output.append("-------------\n\n")
		output.append("Last updated ")
		output.append(datetime.datetime.utcnow().strftime("%d/%m/%y"))
		output.append(" by [")
		output.append(username)
		output.append("](https://www.reddit.com/u/")
		output.append(username)
		output.append(")\n\n")

		output.append("#Fixtures")
		gameDate = None
		for game in games:
			if gameDate is None or gameDate.date() != game['date'].date():
				if gameDate is not None:
					output.append("-------------")
				gameDate = game['date']
				output.append("\n\n**")
				output.append(gameDate.strftime("%d/%m"))
				output.append("**\n\n")
				output.append("|Time|Home|Away|\n")
				output.append("|:--|:--|:--|\n")

			output.append("|")
			output.append(game['date'].strftime("%H:%M"))
			output.append("|")
			output.append(game['home']['name'])
			output.append("|")
			output.append(game['away']['name'])
			output.append("|")
			output.append("\n")

		output.append("-------------\n\n")
		output.append("Last updated ")
		output.append(datetime.datetime.utcnow().strftime("%d/%m/%y"))
		output.append(" by [")
		output.append(username)
		output.append("](https://www.reddit.com/u/")
		output.append(username)
		output.append(")\n\n")

		subreddit.mod.update(description=begin+''.join(output)+end)

	log.debug("Run complete after: %d", int(time.perf_counter() - startTime))
	if once:
		break
	time.sleep(LOOP_TIME)
