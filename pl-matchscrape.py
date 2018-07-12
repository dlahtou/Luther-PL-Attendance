""" The goal of this file is to create a method that
can scrape a single match from premierleague.com/match/{match_id}
for its relevant data
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle as pkl
import time
from pprint import pprint

import os
print(time.process_time())

# open match page
options = Options()
driver = webdriver.Firefox(firefox_options=options)
match_id = 7501
driver.get(f"https://www.premierleague.com/match/{match_id}")

# team aliases dict is used to associate team names with shortened versions
with open('team_aliases_dict.pkl', 'rb') as open_file:
    team_aliases = pkl.load(open_file)

# create dataframe dict
match_data = {'match_id': match_id}

hometeam_selector = '//div[@class="team home"]'
awayteam_selector = '//div[@class="team away"]'
match_data['hometeam_name'] = driver.find_element_by_xpath(hometeam_selector).text
match_data['awayteam_name'] = driver.find_element_by_xpath(awayteam_selector).text

score_selector = '//div[@class="matchScoreContainer"]'
match_data['home_goals'], match_data['away_goals'] = (driver.find_element_by_xpath(score_selector)
                                .text.split('-')) #usually 2-0 or similar

#get match info
minfo_selector = '//div[@class="matchInfo"]'
match_data['match_date'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="matchDate renderMatchDateContainer"]').text
match_data['match_timestamp'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="matchDate renderMatchDateContainer"]').get_attribute("data-kickoff")
match_data['match_referee'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="referee"]').text
match_data['match_stadium'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="stadium"]').text
match_data['match_attendance'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="attendance hide-m"]').text

#cause loading of stats table by clicking on tab
stats_button_selector = '//ul[@class="tablist"]/li[contains(text(), "Stats")]'

print(time.process_time())
try:
    stats_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, stats_button_selector))
    )
except:
    print("couldn't click stats button after 10 seconds!")
print(time.process_time())
stats_button.click()

stats_table_selector = '//tbody[@class="matchCentreStatsContainer"]/tr'
try:
    test_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, stats_table_selector))
    )
except:
    print("couldn't find stats table after 10 seconds!")
stats_table_rows = [e.text.split(' ') for e
                    in driver.find_elements_by_xpath(stats_table_selector)]

# elements generally contained as [HOME_STAT, STAT_NAME, AWAY_STAT]
match_data['home_possession'] = stats_table_rows[0][0]
match_data['away_possession'] = stats_table_rows[0][-1]

match_data['home_shotsontarget'] = stats_table_rows[1][0]
match_data['away_shotsontarget'] = stats_table_rows[1][-1]

match_data['home_shots'] = stats_table_rows[2][0]
match_data['away_shots'] = stats_table_rows[2][-1]

match_data['home_touches'] = stats_table_rows[3][0]
match_data['away_touches'] = stats_table_rows[3][-1]

match_data['home_passes'] = stats_table_rows[4][0]
match_data['away_passes'] = stats_table_rows[4][-1]

match_data['home_tackles'] = stats_table_rows[5][0]
match_data['away_tackles'] = stats_table_rows[5][-1]

match_data['home_clearances'] = stats_table_rows[6][0]
match_data['away_clearances'] = stats_table_rows[6][-1]

match_data['home_corners'] = stats_table_rows[7][0]
match_data['away_corners'] = stats_table_rows[7][-1]

match_data['home_offsides'] = stats_table_rows[8][0]
match_data['away_offsides'] = stats_table_rows[8][-1]

match_data['home_yellowcards'] = stats_table_rows[9][0]
match_data['away_yellowcards'] = stats_table_rows[9][-1]

match_data['home_fouls'] = stats_table_rows[10][0]
match_data['away_fouls'] = stats_table_rows[10][-1]

league_table_button_selector = '//a[@class=" mcNavButton matchWeekTableButton"]'
league_table_button = driver.find_element_by_xpath(league_table_button_selector)
league_table_button.click()

hometeam_tablerow_name = team_aliases[match_data['hometeam_name']]
awayteam_tablerow_name = team_aliases[match_data['awayteam_name']]

hometeam_tablerow_selector = f'//tbody[@class="standingEntriesContainer"]/tr[@data-filtered-table-row-name="{hometeam_tablerow_name}"]'
try:
    hometeam_tablerow = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, hometeam_tablerow_selector))
    )
except:
    print("couldn't find league table after 10 seconds!")
hometeam_tablerow = driver.find_element_by_xpath(hometeam_tablerow_selector)
awayteam_tablerow_selector = f'//tbody[@class="standingEntriesContainer"]/tr[@data-filtered-table-row-name="{awayteam_tablerow_name}"]'
awayteam_tablerow = driver.find_element_by_xpath(awayteam_tablerow_selector)

htr_stringlist = hometeam_tablerow.text.split(' ')
atr_stringlist = awayteam_tablerow.text.split(' ')

# stats from league table generally as [LEAGUE_RANK, ..., PLAYED, GOAL_DIFF, POINTS]
match_data['home_leaguerank'] = htr_stringlist[0]
match_data['away_leaguerank'] = atr_stringlist[0]

match_data['home_matchesplayed'] = htr_stringlist[-3]
match_data['away_matchesplayed'] = atr_stringlist[-3]

match_data['home_goaldifferential'] = htr_stringlist[-2]
match_data['away_goaldifferential'] = atr_stringlist[-2]

match_data['home_leaguepts'] = htr_stringlist[-1]
match_data['away_leaguepts'] = atr_stringlist[-1]
pprint(match_data, indent=1)

driver.quit()