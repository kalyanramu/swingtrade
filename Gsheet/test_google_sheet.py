from google_sheet import gsheet
sheet = gsheet("testgsheets-creds.json","Prints")
df = sheet.read_df('test')
print(df)

print(df.iloc[1]['triggerlevel'])

df.loc[1,'triggerlevel'] = 180

print(df)
sheet.write_df('test',df)


