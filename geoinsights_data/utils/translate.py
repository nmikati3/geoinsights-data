from langdetect import detect
from deep_translator import GoogleTranslator
import time
import pandas as pd


def detect_lang(x):
  try:
    return detect(x)
  except Exception:
    return 'Language Not Detected'
  

def translate_dataset(data):

  #detect language of each url
  data['language'] = data['preprocessed_url'].apply(detect_lang)

  #translate non-english urls
  non_english_df = data[data['language'] != 'en'].drop_duplicates(subset=['preprocessed_url'])

  if len(non_english_df) == 0:
    return data

  batch_size = 1024

  articles = []
  translated_articles = []

  for i in range(int(len(non_english_df)/batch_size)+1):

    try:
      translated_articles += GoogleTranslator(
        source='auto',
        target='en'
      ).translate_batch(list(non_english_df['preprocessed_url'])[i*batch_size:(i+1)*batch_size])
      articles += list(non_english_df['preprocessed_url'])[i*batch_size:(i+1)*batch_size]

    except Exception:
      continue

    time.sleep(10)

  translated_data = pd.DataFrame([articles,translated_articles],index=['preprocessed_url','translated_url']).T
  translated_data = translated_data.drop_duplicates(subset=['translated_url'])

  non_english_df = pd.merge(
    non_english_df,
    translated_data,
    how='left',
    on='preprocessed_url'
  )

  data = pd.merge(
    data,
    non_english_df[['preprocessed_url','translated_url']],
    how='left',
    on='preprocessed_url'
  )

  #keep original url if it is english, otherwise keep translated url
  data['translated_url'] = data['translated_url'].combine_first(data['preprocessed_url'])

  data = data.dropna(subset=['translated_url']).reset_index(drop=True)

  data = data.drop(columns=['language'])
  
  return data