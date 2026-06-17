import pandas as pd
from geoinsights_data.utils.llm import summarize_data, clean_victims_in_data, compute_embeddings
import ast
import numpy as np
from collections import Counter

# Sample deduplication function
def deduplicate_frequent_elements(lst, threshold=0.2):
    total = len(lst)
    if total == 0:
        return []
    count = Counter(lst)
    return [elem for elem, freq in count.items() if freq / total > threshold]


def create_incident_table(df,columns_list_to_list,columns_string_to_list):

    df['incident_start_date'] = pd.to_datetime(df['incident_start_date'],format='ISO8601')

    df = df.rename(columns={'summary':'summaries'})

    for column in columns_list_to_list:
        df.loc[df[column] == '[nan]',column] = '[]'
        df[column] = df[column].fillna('[]').apply(lambda x: list(ast.literal_eval(x)))

    df['content_with_date'] = 'Date: ' + df['incident_start_date'].astype(str).str[:10] + '/n' + df['content']

    agg_rules = {
        'incident_start_date':'min',
        'report_id':pd.Series.nunique,
        'content_with_date':set,
        'summaries':set,
    }

    for column in columns_list_to_list:
        agg_rules[column] = lambda x: sum(x, [])

    for column in columns_string_to_list + ['url','source_url']:
        agg_rules[column] = list


    incidents = df.groupby(['incident_id'],as_index=False).agg(agg_rules).rename(columns={
        'report_id':'number_of_reports'
    })

    for column in columns_list_to_list + columns_string_to_list:
        incidents[column] = incidents[column].apply(lambda x: deduplicate_frequent_elements([i for i in x if i != 'Unknown']))
    for column in ['content_with_date','summaries']:
        incidents[column] = incidents[column].apply(lambda x: list(x))

    incidents['summaries'] = incidents['summaries'].apply(lambda x: frozenset(set(x)))

    return incidents


def incident_summarize_data(
        df,
        already_calculated_incidents,
        system_prompt,
        columns_list_to_list,
        columns_list_to_string,
        columns_added,
        clean_victims,
        clean_victims_system_prompt
    ):

    incidents = create_incident_table(df,columns_list_to_list,columns_list_to_string)

    if len(already_calculated_incidents) > 0:

        already_calculated_incidents['summaries'] = already_calculated_incidents['summaries'].apply(lambda x: frozenset(set(ast.literal_eval(x))))

        incidents = pd.merge(
            incidents,
            already_calculated_incidents[[
                'summaries',
                'incident_summary',
            ] + columns_added].drop_duplicates(),
            how='outer',
            on='summaries',
            indicator=True
        )

    else:
        incidents['_merge'] = 'left_only'
        incidents['incident_summary'] = np.nan

    incidents['summaries'] = incidents['summaries'].apply(lambda x: list(x))

    already_summarized = incidents[incidents['_merge'] == 'both'].drop(columns=['_merge']).reset_index(drop=True)

    to_summarize = incidents[incidents['_merge'] == 'left_only'].drop(columns=[
        '_merge',
        'incident_summary',
    ] + columns_added).reset_index(drop=True)

    top_incidents = to_summarize[to_summarize['number_of_reports'] > 1].drop_duplicates(subset=['content_with_date'])

    top_incidents['content_with_date'] = top_incidents['content_with_date'].astype(str)

    top_incidents = summarize_data(top_incidents,system_prompt,'content_with_date').rename(columns={
        'summary':'incident_summary'
    })

    top_incidents = top_incidents[['incident_id','incident_summary']]

    to_summarize = pd.merge(to_summarize,top_incidents,how='left',on='incident_id')

    to_summarize['incident_start_date'] = pd.to_datetime(to_summarize['incident_start_date'],format='ISO8601')
    to_summarize['incident_summary'] = to_summarize['incident_summary'].combine_first(to_summarize['summaries'].str[0])
    to_summarize['incident_summary'] = 'Incident Start Date: ' + to_summarize['incident_start_date'].astype(str) + '\n'  + to_summarize['incident_summary']

    if clean_victims:
        to_summarize = clean_victims_in_data(to_summarize,clean_victims_system_prompt)

    incidents = pd.concat([to_summarize,already_summarized]).reset_index(drop=True)
    incidents['incident_start_date'] = pd.to_datetime(incidents['incident_start_date'],format='ISO8601')

    incidents['incident_start_date'] = incidents['incident_start_date'].astype(str).str[:10]

    return incidents


def compute_incident_embeddings_data(incidents):

    incidents['incident_start_date'] = pd.to_datetime(incidents['incident_start_date'],format='ISO8601')

    incidents['week_end_date'] = incidents['incident_start_date'].apply(lambda x: (x + pd.offsets.Week(weekday=6)).date())

    list_dates = incidents['week_end_date'].sort_values().unique()
    all_docs = []
    all_embeddings = []

    for date in list_dates:

        docs = list(incidents[incidents['week_end_date'] == date]['incident_summary'].dropna())

        all_docs+= docs
        all_embeddings+= compute_embeddings(docs)

    embeddings = pd.merge(
        incidents,
        pd.DataFrame([all_docs,all_embeddings],index=['incident_summary','embedding']).T.drop_duplicates(subset=['incident_summary']),
        how='left',
        on='incident_summary'
    )[['incident_id','embedding']]

    for i in range(len(embeddings['embedding'][0])):
        embeddings[i] = embeddings['embedding'].str[i]

    del embeddings['embedding']

    return embeddings



