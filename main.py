import page2
import schedule
import time

page2.login()
page2.df_to_excel()


schedule.every(3).minutes.do(page2.df_to_excel)
#schedule.every().day.at("22:30").do(searchResults.searhEverySesult)

while True:
    schedule.run_pending()