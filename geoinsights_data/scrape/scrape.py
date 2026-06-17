from geoinsights_data.utils.collect import (
    get_csv_data,
    get_bucket,
    write_csv_data
)
import pandas as pd
import newspaper
import os
from interruptingcow import timeout

task_index = int(os.environ.get("CLOUD_RUN_TASK_INDEX", 0)) + 1
bucket = get_bucket()

sources = get_csv_data('sources/sources.csv',bucket)
urls = get_csv_data('sources/urls{}.csv'.format(task_index),bucket)

sources = sources[sources['COUNT_URLS'] >= 100]

all_sources = list(sources['SourceCommonName'].unique())
all_urls = []
sources_seen = []

all_sources = all_sources[(task_index-1)*2000:task_index*2000]

for source in all_sources:
  try:
    with timeout(120, exception=RuntimeError):
      paper = newspaper.build('http://' + source)
      all_urls += [article.url for article in paper.articles]
      sources_seen += [source for article in paper.articles]
  except Exception as e:
    continue


today = pd.Timestamp.now().strftime('%Y-%m-%d')

collected_urls = pd.DataFrame([all_urls,[today for url in all_urls],sources_seen],index=['url','collection_date','source']).T
collected_urls = pd.concat([urls.drop_duplicates(subset=['url']),collected_urls]).drop_duplicates(subset=['url'],keep='first').reset_index(drop=True)

write_csv_data(collected_urls,'sources/urls{}.csv'.format(task_index),bucket)