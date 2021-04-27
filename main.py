import page2
import page1
import schedule

page1.runPage()
page2.runPage()


schedule.every(3).minutes.do(page2.df_to_excel)
schedule.every(3).minutes.do(page1.df_to_excel)
#schedule.every().day.at("22:30").do(searchResults.searhEverySesult)

while True:
    schedule.run_pending()