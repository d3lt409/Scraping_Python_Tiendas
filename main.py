import page2
import schedule

page2.login()
schedule.every(3).minutes.do(page2.df_to_excel)
page2.df_to_excel()
while True:
    schedule.run_pending()