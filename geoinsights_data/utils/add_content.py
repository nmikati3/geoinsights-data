import newspaper
import pandas as pd
import numpy as np

def get_content(to_add_df):

    urls = list(to_add_df['url'].dropna().unique())

    urls_seen = []
    texts = []
    titles = []
    publish_dates = []

    for url in urls:

        try:
            article = newspaper.Article(url)

            article.download()
            article.parse()
            text = article.text
            title = article.title
            publish_date = article.publish_date
            texts.append(text)
            urls_seen.append(url)
            titles.append(title)
            publish_dates.append(publish_date)

        except Exception as e:
            continue

    contents = pd.DataFrame([urls_seen,texts,titles,publish_dates],index=['url','content','title','publish_date']).T

    if len(contents) > 0:

        to_add_df = pd.merge(
            to_add_df,
            contents,
            how='left',
            on='url'
        )

        to_add_df = to_add_df[to_add_df['content'].notna()].reset_index(drop=True)

        to_add_df['date'] = pd.to_datetime(to_add_df['date'],errors='coerce').dt.tz_localize(None)
        to_add_df['publish_date'] = pd.to_datetime(to_add_df['publish_date'], errors='coerce', utc=True).dt.tz_localize(None)

        to_add_df.loc[
            (to_add_df['publish_date'] > to_add_df['date'] + pd.Timedelta(days=30)) |
            (to_add_df['publish_date'] < to_add_df['date'] - pd.Timedelta(days=30)) |
            (to_add_df['publish_date'] > pd.Timestamp.now()),
            'publish_date'
        ] = np.nan

        to_add_df['date'] = to_add_df['publish_date'].combine_first(to_add_df['date'])
        to_add_df['date'] = to_add_df['date'].astype(str).str[:10]

        to_add_df = to_add_df.drop(columns=['publish_date'])

    return to_add_df
