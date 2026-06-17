import os
from openai import OpenAI
import numpy as np
import pandas as pd
import ast
from polyfuzz import PolyFuzz
from pydantic import BaseModel
from typing import List
from geoinsights_data.utils.local_llms import get_labels_local_llm


openai_api_key = os.environ.get("OPENAI_API_KEY")
MODEL_NAME = os.environ.get("MODEL_NAME")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")

CLIENT = OpenAI(
    api_key = openai_api_key
)


def try_eval(variable_name,x):
  try:
    return ast.literal_eval(x)[variable_name]
  except Exception:
    return np.nan
  

def compute_embeddings(docs):
  embeddings = []
  for i in range(len(docs)//1000+1):
    if len(docs[1000*i:1000*(i+1)]) > 0:
      response = CLIENT.embeddings.create(input=docs[1000*i:1000*(i+1)], model='text-embedding-3-small')
      embeddings += [np.array(x.embedding) for x in response.data]
  return embeddings


def get_llm_classify(content,system_prompt):

  response = CLIENT.chat.completions.create(
    model=MODEL_NAME,
    temperature=0,
    top_p=0,
    response_format={
        "type": "json_object"
    },
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": content
        }
    ]
  )

  return response.choices[0].message.content


def llm_classify_data(to_classify_df,system_prompt):

  contents = list(to_classify_df['content'].dropna().unique())

  if len(contents) > 0:

    contents_seen = []
    labels = []

    for content in contents:
      try:
        labels.append(get_llm_classify(content,system_prompt))
        contents_seen.append(content)
      except Exception:
        continue

    classified = pd.DataFrame([contents_seen,labels],index=['content','label']).T

    classified['label'] = classified['label'].apply(lambda x: try_eval('filter_value',x))
    classified['filter_value'] = classified['label'] == 'True'

    classified = classified[classified['filter_value']].reset_index(drop=True)

    to_classify_df = pd.merge(
      to_classify_df,
      classified.drop(columns=['label','filter_value']),
      how='inner',
      on='content'
    ).reset_index(drop=True)

    to_classify_df = to_classify_df.dropna(subset=['date']).groupby(['content'],as_index=False).agg({
        'date':'min',
        'url':set,
        'source_url':set
    })

    to_classify_df['date'] = to_classify_df['date'].astype(str).str[:10]

    return to_classify_df
  
  else:
    return pd.DataFrame([],columns=['content','date','url','source_url'])


def get_labels(content,system_prompt):

  response = CLIENT.chat.completions.create(
    model=MODEL_NAME,
    temperature=0,
    top_p=0,
    response_format={
      "type": "json_object"
    },
    messages=[
      {
        "role": "system",
        "content": system_prompt
      },
      {
        "role": "user",
        "content": content
      }
    ],
  )

  return response.choices[0].message.content


def get_structured_labels(content,system_prompt,Structure):

    response = CLIENT.beta.chat.completions.parse(
      model=MODEL_NAME,
      temperature=0,
      top_p=0,
      response_format=Structure,
      messages=[
          {"role": "system","content": system_prompt},
          {"role": "user","content": content}
      ]
    )

    return response.choices[0].message.parsed


def exact_match(target,source):
  for i in source:
    if target == i:
      return i
  return np.nan


def correct_labels_with_fuzzy_matching(labels,reference_labels,threshold):

  model = PolyFuzz("TF-IDF")

  model.match(labels, reference_labels)
  similarities = model.get_matches().rename(columns={'From':'label','To':'reference'})

  similarities.loc[similarities['similarity'] < threshold, 'reference'] = 'Unknown'

  return similarities


def clean_labels(to_correct_df,row_id,column_name,reference_labels,column_type,matching_type,threshold,fill_missing_with='Unknown'):

  model = PolyFuzz("TF-IDF")

  if column_type == 'list':
    labels = list(to_correct_df[column_name].explode().dropna().unique())
  else:
    labels = list(to_correct_df[column_name].dropna().unique())

  if len(labels) > 0:

    if matching_type == 'fuzzy':
      model.match(labels, reference_labels)
      similarities = model.get_matches().rename(columns={'From':'label','To':'reference','Similarity':'similarity'})
      similarities.loc[similarities['similarity'] < threshold, 'reference'] = fill_missing_with

    else:
      matches = [exact_match(i,reference_labels) for i in labels]
      similarities = pd.DataFrame([labels,matches],index=['label','reference']).T
      similarities = similarities.fillna({'reference':fill_missing_with})

    to_correct_df_cleaned = to_correct_df[[row_id,column_name]]

    if column_type == 'list':
      to_correct_df_cleaned = to_correct_df_cleaned.explode(column_name)

    to_correct_df_cleaned[column_name] = to_correct_df_cleaned[column_name].fillna(fill_missing_with)

    to_correct_df_cleaned = pd.merge(to_correct_df_cleaned,similarities,how='left',left_on=column_name,right_on='label')

    if column_type == 'list':
      to_correct_df_cleaned = to_correct_df_cleaned.groupby(row_id)['reference'].apply(set).reset_index()
      to_correct_df_cleaned['reference'] = to_correct_df_cleaned['reference'].apply(lambda x: list(x))
    else:
      to_correct_df_cleaned = to_correct_df_cleaned[[row_id,'reference']]

    to_correct_df_cleaned = to_correct_df_cleaned.rename(columns={'reference':'cleaned_'+column_name})

    to_correct_df = pd.merge(to_correct_df,to_correct_df_cleaned,how='left',on=row_id)

  return to_correct_df


def summarize_data(to_summarize_df,system_prompt,column_to_summarize):

  contents = list(to_summarize_df[column_to_summarize].dropna().unique())
  contents_seen = []
  summaries = []

  for content in contents:
    try:
      summaries.append(get_labels_local_llm(content,system_prompt))
      contents_seen.append(content)
    except Exception:
      continue

  summarized = pd.DataFrame([contents_seen,summaries],index=[column_to_summarize,'summary']).T
  summarized['summary'] = summarized['summary'].apply(lambda x: try_eval('summary',x))

  if len(summarized) > 0:

    to_summarize_df = pd.merge(
      to_summarize_df,
      summarized,
      how='inner',
      on=column_to_summarize
    ).reset_index(drop=True)

    to_summarize_df = to_summarize_df.dropna(subset=['summary']).reset_index(drop=True)

  return to_summarize_df


def label(to_label_df,system_prompt,columns):

  contents = list(to_label_df["summary"].dropna().unique())
  contents_seen = []
  labels = []

  for content in contents:
    try:
      labels.append(get_labels(content,system_prompt))
      contents_seen.append(content)
    except Exception:
      continue

  labeled = pd.DataFrame([contents_seen,labels],index=['summary','label']).T
  for column_name in list(columns.keys()):
    labeled[column_name] = labeled['label'].apply(lambda x: try_eval(column_name,x))

  if len(labeled) > 0:

    to_label_df = pd.merge(
      to_label_df,
      labeled.drop(columns=['label']),
      how='inner',
      on='summary'
    ).reset_index(drop=True)

    for column_name in list(columns.keys()):
      column_type = columns[column_name]["column_type"]
      reference_labels = columns[column_name]["reference_labels"]
      matching_type = columns[column_name]["matching_type"]
      threshold = columns[column_name]["threshold"]
      if matching_type == 'rules':
        rule_function = columns[column_name]["rule"]
        to_label_df = rule_function(to_label_df)
      elif matching_type != 'no matching':
        to_label_df = clean_labels(to_label_df,'content',column_name,reference_labels,column_type,matching_type,threshold)

  return to_label_df


def clean_victims_in_data(to_summarize,system_prompt):

  class Victims(BaseModel):
    victims: List[str]

  ids = list(to_summarize['incident_id'])
  initial_victims = list(to_summarize['victims'])
  ids_seen = []
  victims = []

  for i in range(len(ids)):
    try:
      victims.append(get_structured_labels(str(set(initial_victims[i])),system_prompt,Victims).victims)
      ids_seen.append(ids[i])
    except Exception as e:
      victims.append(list(set(initial_victims[i])))
      ids_seen.append(ids[i])

  to_summarize['cleaned_victims'] = victims
  to_summarize['cleaned_victims'] = to_summarize['cleaned_victims'].apply(lambda x: list(set(x)))

  to_summarize = to_summarize.drop(columns=['victims'])

  to_summarize['cleaned_victims'] = to_summarize['cleaned_victims'].apply(lambda x: list(set(x)))
  to_summarize['number_of_victims'] = to_summarize['cleaned_victims'].apply(lambda x: len(x))

  return to_summarize

  

  