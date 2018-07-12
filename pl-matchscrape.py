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
import pandas as pd
import numpy as np
from datetime import datetime

import os

# open match page
options = Options()
final_match_id = 5946
# team aliases dict is used to associate team names with shortened versions
with open('team_aliases_dict.pkl', 'rb') as open_file:
    team_aliases = pkl.load(open_file)

def add_PL_match(match_id):
    print(datetime.now().time().strftime('%H:%M:%S'))
    print(f"opening match {match_id}")
    try:
        driver = webdriver.Firefox(firefox_options=options)
    except:
        driver = webdriver.Chrome(chromedriver) # for mac 
    driver.get(f"https://www.premierleague.com/match/{match_id}")

    # create dataframe dict
    match_data = dict()

    hometeam_selector = '//div[@class="team home"]'
    awayteam_selector = '//div[@class="team away"]'
    match_data['hometeam_name'] = driver.find_element_by_xpath(hometeam_selector).text
    match_data['awayteam_name'] = driver.find_element_by_xpath(awayteam_selector).text

    if match_data['hometeam_name'] not in team_aliases.keys() or match_data['awayteam_name'] not in team_aliases.keys():
        print(match_data['hometeam_name'] + 'or' + match_data['awayteam_name'] + "not found in premier league!")
        return

    print(match_data['hometeam_name'] + match_data['awayteam_name'])

    score_selector = '//div[@class="matchScoreContainer"]'
    print(driver.find_element_by_xpath(score_selector).text)
    match_data['home_goals'], match_data['away_goals'] = (driver.find_element_by_xpath(score_selector)
                                    .text.split('-')) #usually 2-0 or similar

    #get match info
    minfo_selector = '//div[@class="matchInfo"]'
    try:
        match_data['match_date'] = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, minfo_selector + '/div[@class="matchDate renderMatchDateContainer"]'))
        ).text
        print(match_data['match_date'])
    except:
        print("couldn't find match date after 10 seconds!")
    match_data['match_timestamp'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="matchDate renderMatchDateContainer"]').get_attribute("data-kickoff")
    match_data['match_referee'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="referee"]').text
    match_data['match_stadium'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="stadium"]').text
    match_data['match_attendance'] = driver.find_element_by_xpath(minfo_selector + '/div[@class="attendance hide-m"]').text

    #cause loading of stats table by clicking on tab
    stats_button_selector = '//ul[@class="tablist"]/li[contains(text(), "Stats")]'

    try:
        stats_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, stats_button_selector))
        )
    except:
        print("couldn't click stats button after 10 seconds!")
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

    # set defaults for yellow and red (might not exist in page)
    match_data['home_yellowcards'] = '0'
    match_data['away_yellowcards'] = '0'

    match_data['home_redcards'] = '0'
    match_data['away_redcards'] = '0'

    ## following rows can be yellow cards, red cards, and fouls
    for row in stats_table_rows[9:]:
        if row[1] == "Fouls":
            match_data['home_fouls'] = row[0]
            match_data['away_fouls'] = row[-1]
        elif row[1] == "Red":
            match_data['home_redcards'] = row[0]
            match_data['away_redcards'] = row[-1]
        elif row[1] == "Yellow":
            match_data['home_yellowcards'] = row[0]
            match_data['away_yellowcards'] = row[-1]

    # look into the league table
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
        print("couldn't find hometeam tablerow in league table after 10 seconds!")

    if len(driver.find_elements_by_xpath('//tbody[@class="standingEntriesContainer"]/tr')) < 20:
        print("Fewer than 20 teams in league!")
        return
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

    match_data['matchweek'] = driver.find_element_by_xpath('//span[@class="matchweekAmountContainer"]').text

    match_df = pd.DataFrame(match_data, index=[match_id])
    print(f'saving match {match_id}')
    with open('PLmatches.csv', 'a') as open_file:
        match_df.to_csv(open_file, header=False, mode='a')
    print('--------')

    driver.quit()

match_range = np.arange(5681, 9000)
with open('PLmatches.csv', 'r') as open_file:
    df = pd.read_csv(open_file, index_col=0)
index_set = set(df.index.tolist())
if match_range[0] in index_set or match_range[-1] in index_set:
    print("MATCHES ALREADY IN DATAFRAME")
    print(f'current match records: {min(index_set)} to {max(index_set)}')
    quit()
del(df)
for matchnum in match_range:
    time.sleep(3)
    add_PL_match(matchnum)