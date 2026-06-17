import numpy as np
import pandas as pd
import json
import ast
from geoinsights_data.utils.collect import get_european_union_countries, get_csv_data, get_bucket, write_parquet_data
from geoinsights_data.utils.collect import clean_for_api_and_write_as_json

VARIABLES_INCIDENTS = [
    'incident_id',
    'incident_start_date',
    'number_of_reports',
    'url_list',
    'source_url_list',
    'content_list',
    'summaries',
    'initiating_countries',
    'benefiting_countries',
    'receiving_countries',
    'receiving_economic_sectors',
    'initiators',
    'beneficiaries',
    'receivers',
    'incident_sub_types',
    'incident_type',
    'incident_summary'
]

VARIABLES_REPORTS = [
    'report_id',
    'date',
    'url',
    'source_url',
    'content',
    'summary',
    'initiating_countries',
    'benefiting_countries',
    'receiving_countries',
    'receiving_economic_sectors',
    'initiators',
    'beneficiaries',
    'receivers',
    'incident_sub_types',
    'incident_type',
    'incident_id',
    'incident_start_date',
    'number_of_reports',
    'source_country',
    'source_ownership_structure',
    'source_political_ideological_affiliation',
    'source_geographic_focus',
    'source_target_audience',
    'source_journalistic_style',
    'source_source_reliability'
]

def process_sanctions_incidents(sanctions):

    eu_countries = get_european_union_countries()

    sanctions['cleaned_imposing_country'] = sanctions['cleaned_imposing_country'].apply(lambda x: ast.literal_eval(x))
    sanctions['cleaned_targeted_country'] = sanctions['cleaned_targeted_country'].apply(lambda x: ast.literal_eval(x))

    sanctions.loc[
        sanctions['cleaned_imposing_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_imposing_country'
    ] = sanctions.loc[
        sanctions['cleaned_imposing_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_imposing_country'
    ].apply(lambda x: list(set(x + ['European Union'])))

    sanctions.loc[
        sanctions['cleaned_targeted_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_country'
    ] = sanctions.loc[
        sanctions['cleaned_targeted_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_country'
    ].apply(lambda x: list(set(x + ['European Union'])))

    sanctions['cleaned_imposing_country'] = sanctions['cleaned_imposing_country'].astype(str)
    sanctions['cleaned_targeted_country'] = sanctions['cleaned_targeted_country'].astype(str)

    sanctions = sanctions.rename(columns={
        'url':'url_list',
        'source_url':'source_url_list',
        'content_with_date':'content_list',
        'summary':'summaries',
        'cleaned_imposing_country':'initiating_countries',
        'cleaned_targeted_country':'receiving_countries'
    })

    sanctions['receiving_economic_sectors'] = np.nan
    sanctions['receivers'] = np.nan
    sanctions['initiators'] = sanctions['initiating_countries']
    sanctions['beneficiaries'] = np.nan
    sanctions['incident_sub_types'] = np.nan
    sanctions['benefiting_countries'] = np.nan

    sanctions['incident_id'] = 'sanctions-'+sanctions['incident_id']
    sanctions['incident_type'] = 'sanctions'

    sanctions = sanctions[VARIABLES_INCIDENTS]

    return sanctions


def process_cyber_incidents(cyber):

    eu_countries = get_european_union_countries()

    cyber['cleaned_attacking_countries'] = cyber['cleaned_attacking_countries'].apply(lambda x: ast.literal_eval(x))
    cyber['cleaned_targeted_countries'] = cyber['cleaned_targeted_countries'].apply(lambda x: ast.literal_eval(x))

    cyber.loc[
        cyber['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ] = cyber.loc[
        cyber['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    cyber.loc[
        cyber['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ] = cyber.loc[
        cyber['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    cyber['cleaned_attacking_countries'] = cyber['cleaned_attacking_countries'].astype(str)
    cyber['cleaned_targeted_countries'] = cyber['cleaned_targeted_countries'].astype(str)
    
    cyber = cyber.rename(columns={
        'url':'url_list',
        'source_url':'source_url_list',
        'content_with_date':'content_list',
        'summary':'summaries',
        'cleaned_attacking_countries':'initiating_countries',
        'cleaned_targeted_countries':'receiving_countries',
        'cleaned_targeted_economic_sectors':'receiving_economic_sectors',
        'cleaned_attackers':'initiators',
        'cleaned_victims':'receivers',
        'cleaned_cyber_incident_type':'incident_sub_types'
    })

    cyber['benefiting_countries'] = np.nan
    cyber['beneficiaries'] = np.nan

    cyber['incident_id'] = 'cyber-'+cyber['incident_id']
    cyber['incident_type'] = 'cyber'

    cyber = cyber[VARIABLES_INCIDENTS]

    return cyber


def process_military_aid_incidents(military_aid):

    eu_countries = get_european_union_countries()

    military_aid['cleaned_providing_countries'] = military_aid['cleaned_providing_countries'].apply(lambda x: ast.literal_eval(x))
    military_aid['cleaned_receiving_countries'] = military_aid['cleaned_receiving_countries'].apply(lambda x: ast.literal_eval(x))

    military_aid.loc[
        military_aid['cleaned_providing_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_providing_countries'
    ] = military_aid.loc[
        military_aid['cleaned_providing_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_providing_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_aid.loc[
        military_aid['cleaned_receiving_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_receiving_countries'
    ] = military_aid.loc[
        military_aid['cleaned_receiving_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_receiving_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_aid['cleaned_providing_countries'] = military_aid['cleaned_providing_countries'].astype(str)
    military_aid['cleaned_receiving_countries'] = military_aid['cleaned_receiving_countries'].astype(str)

    military_aid = military_aid.rename(columns={
        'url':'url_list',
        'source_url':'source_url_list',
        'content_with_date':'content_list',
        'summary':'summaries',
        'cleaned_providing_countries':'initiating_countries',
        'cleaned_receiving_countries':'benefiting_countries',
    })

    military_aid['receiving_economic_sectors'] = np.nan
    military_aid['receiving_countries'] = np.nan
    military_aid['receivers'] = np.nan
    military_aid['initiators'] = military_aid['initiating_countries']
    military_aid['beneficiaries'] = military_aid['benefiting_countries']
    military_aid['incident_sub_types'] = np.nan

    military_aid['incident_id'] = 'military-aid-'+military_aid['incident_id']
    military_aid['incident_type'] = 'military-aid'

    military_aid = military_aid[VARIABLES_INCIDENTS]

    return military_aid


def process_summits_incidents(summits):

    eu_countries = get_european_union_countries()

    summits['cleaned_participating_countries'] = summits['cleaned_participating_countries'].apply(lambda x: ast.literal_eval(x))

    summits.loc[
        summits['cleaned_participating_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_participating_countries'
    ] = summits.loc[
        summits['cleaned_participating_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_participating_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    summits['cleaned_participating_countries'] = summits['cleaned_participating_countries'].astype(str)


    summits = summits.rename(columns={
        'url':'url_list',
        'source_url':'source_url_list',
        'content_with_date':'content_list',
        'summary':'summaries',
        'cleaned_participating_countries':'initiating_countries',
        'cleaned_summit_name':'incident_sub_types'
    })

    summits['receiving_economic_sectors'] = np.nan
    summits['receiving_countries'] = np.nan
    summits['benefiting_countries'] = np.nan
    summits['receivers'] = np.nan
    summits['initiators'] = summits['initiating_countries']
    summits['beneficiaries'] = np.nan

    summits['incident_id'] = 'international-summits-'+summits['incident_id']
    summits['incident_type'] = 'summits'

    summits = summits[VARIABLES_INCIDENTS]

    return summits


def process_military_offensive_incidents(military_offensive):

    eu_countries = get_european_union_countries()

    military_offensive['cleaned_attacking_countries'] = military_offensive['cleaned_attacking_countries'].apply(lambda x: ast.literal_eval(x))
    military_offensive['cleaned_targeted_countries'] = military_offensive['cleaned_targeted_countries'].apply(lambda x: ast.literal_eval(x))

    military_offensive.loc[
        military_offensive['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ] = military_offensive.loc[
        military_offensive['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_offensive.loc[
        military_offensive['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ] = military_offensive.loc[
        military_offensive['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_offensive['cleaned_attacking_countries'] = military_offensive['cleaned_attacking_countries'].astype(str)
    military_offensive['cleaned_targeted_countries'] = military_offensive['cleaned_targeted_countries'].astype(str)

    military_offensive = military_offensive.rename(columns={
        'url':'url_list',
        'source_url':'source_url_list',
        'content_with_date':'content_list',
        'summary':'summaries',
        'cleaned_attacking_countries':'initiating_countries',
        'cleaned_targeted_countries':'receiving_countries',
    })

    military_offensive['receiving_economic_sectors'] = np.nan
    military_offensive['benefiting_countries'] = np.nan
    military_offensive['receivers'] = military_offensive['receiving_countries']
    military_offensive['initiators'] = military_offensive['initiating_countries']
    military_offensive['beneficiaries'] = np.nan
    military_offensive['incident_sub_types'] = np.nan

    military_offensive['incident_id'] = 'military-offensive-'+military_offensive['incident_id']
    military_offensive['incident_type'] = 'military-offensive'

    military_offensive = military_offensive[VARIABLES_INCIDENTS]

    return military_offensive


def process_sanctions_reports(sanctions):

    eu_countries = get_european_union_countries()

    sanctions['cleaned_imposing_country'] = sanctions['cleaned_imposing_country'].apply(lambda x: [x])
    sanctions['cleaned_targeted_country'] = sanctions['cleaned_targeted_country'].apply(lambda x: [x])

    sanctions.loc[
        sanctions['cleaned_imposing_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_imposing_country'
    ] = sanctions.loc[
        sanctions['cleaned_imposing_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_imposing_country'
    ].apply(lambda x: list(set(x + ['European Union'])))

    sanctions.loc[
        sanctions['cleaned_targeted_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_country'
    ] = sanctions.loc[
        sanctions['cleaned_targeted_country'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_country'
    ].apply(lambda x: list(set(x + ['European Union'])))

    sanctions['cleaned_imposing_country'] = sanctions['cleaned_imposing_country'].astype(str)
    sanctions['cleaned_targeted_country'] = sanctions['cleaned_targeted_country'].astype(str)

    sanctions = sanctions.rename(columns={
        'num_reports':'number_of_reports',
        'cleaned_imposing_country':'initiating_countries',
        'cleaned_targeted_country':'receiving_countries'
    })

    sanctions['receiving_economic_sectors'] = np.nan
    sanctions['receivers'] = np.nan
    sanctions['initiators'] = sanctions['initiating_countries']
    sanctions['beneficiaries'] = np.nan
    sanctions['incident_sub_types'] = np.nan
    sanctions['benefiting_countries'] = np.nan

    sanctions['incident_id'] = 'sanctions-'+sanctions['incident_id']
    sanctions['report_id'] = 'sanctions-'+sanctions['report_id']
    sanctions['incident_type'] = 'sanctions'

    sanctions = sanctions[VARIABLES_REPORTS]

    return sanctions


def process_cyber_reports(cyber):

    eu_countries = get_european_union_countries()

    list_columns = [
        'cleaned_attacking_countries',
        'cleaned_targeted_countries'
    ]

    for column in list_columns:
      cyber[column] = cyber[column].fillna('[]')
      cyber.loc[cyber[column] == '[nan]',column] = '[]'
      cyber[column] = cyber[column].fillna('[]')

    cyber['cleaned_attacking_countries'] = cyber['cleaned_attacking_countries'].apply(lambda x: ast.literal_eval(x))
    cyber['cleaned_targeted_countries'] = cyber['cleaned_targeted_countries'].apply(lambda x: ast.literal_eval(x))

    cyber.loc[
        cyber['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ] = cyber.loc[
        cyber['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    cyber.loc[
        cyber['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ] = cyber.loc[
        cyber['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    cyber['cleaned_attacking_countries'] = cyber['cleaned_attacking_countries'].astype(str)
    cyber['cleaned_targeted_countries'] = cyber['cleaned_targeted_countries'].astype(str)
    
    cyber = cyber.rename(columns={
        'num_reports':'number_of_reports',
        'cleaned_attacking_countries':'initiating_countries',
        'cleaned_targeted_countries':'receiving_countries',
        'cleaned_targeted_economic_sectors':'receiving_economic_sectors',
        'cleaned_attackers':'initiators',
        'victims':'receivers',
        'cleaned_cyber_incident_type':'incident_sub_types'
    })

    cyber['benefiting_countries'] = np.nan
    cyber['beneficiaries'] = np.nan

    cyber['report_id'] = 'cyber-'+cyber['report_id']
    cyber['incident_id'] = 'cyber-'+cyber['incident_id']
    cyber['incident_type'] = 'cyber'

    cyber = cyber[VARIABLES_REPORTS]

    return cyber


def process_military_aid_reports(military_aid):

    eu_countries = get_european_union_countries()

    list_columns = [
        'cleaned_providing_countries',
        'cleaned_receiving_countries'
    ]

    for column in list_columns:
      military_aid[column] = military_aid[column].fillna('[]')
      military_aid.loc[military_aid[column] == '[nan]',column] = '[]'
      military_aid[column] = military_aid[column].fillna('[]')

    military_aid['cleaned_providing_countries'] = military_aid['cleaned_providing_countries'].apply(lambda x: ast.literal_eval(x))
    military_aid['cleaned_receiving_countries'] = military_aid['cleaned_receiving_countries'].apply(lambda x: ast.literal_eval(x))

    military_aid.loc[
        military_aid['cleaned_providing_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_providing_countries'
    ] = military_aid.loc[
        military_aid['cleaned_providing_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_providing_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_aid.loc[
        military_aid['cleaned_receiving_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_receiving_countries'
    ] = military_aid.loc[
        military_aid['cleaned_receiving_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_receiving_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_aid['cleaned_providing_countries'] = military_aid['cleaned_providing_countries'].astype(str)
    military_aid['cleaned_receiving_countries'] = military_aid['cleaned_receiving_countries'].astype(str)

    military_aid = military_aid.rename(columns={
        'num_reports':'number_of_reports',
        'cleaned_providing_countries':'initiating_countries',
        'cleaned_receiving_countries':'benefiting_countries',
    })

    military_aid['receiving_economic_sectors'] = np.nan
    military_aid['receiving_countries'] = np.nan
    military_aid['receivers'] = np.nan
    military_aid['initiators'] = military_aid['initiating_countries']
    military_aid['beneficiaries'] = military_aid['benefiting_countries']
    military_aid['incident_sub_types'] = np.nan

    military_aid['report_id'] = 'military-aid-'+military_aid['report_id']
    military_aid['incident_id'] = 'military-aid-'+military_aid['incident_id']
    military_aid['incident_type'] = 'military-aid'

    military_aid = military_aid[VARIABLES_REPORTS]

    return military_aid


def process_summits_reports(summits):

    eu_countries = get_european_union_countries()

    list_columns = [
        'cleaned_participating_countries'
    ]

    for column in list_columns:
      summits[column] = summits[column].fillna('[]')
      summits.loc[summits[column] == '[nan]',column] = '[]'
      summits[column] = summits[column].fillna('[]')

    summits['cleaned_participating_countries'] = summits['cleaned_participating_countries'].apply(lambda x: ast.literal_eval(x))

    summits.loc[
        summits['cleaned_participating_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_participating_countries'
    ] = summits.loc[
        summits['cleaned_participating_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_participating_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    summits['cleaned_participating_countries'] = summits['cleaned_participating_countries'].astype(str)


    summits = summits.rename(columns={
        'num_reports':'number_of_reports',
        'cleaned_participating_countries':'initiating_countries',
        'cleaned_summit_name':'incident_sub_types'
    })

    summits['receiving_economic_sectors'] = np.nan
    summits['receiving_countries'] = np.nan
    summits['benefiting_countries'] = np.nan
    summits['receivers'] = np.nan
    summits['initiators'] = summits['initiating_countries']
    summits['beneficiaries'] = np.nan

    summits['report_id'] = 'international-summits-'+summits['report_id']
    summits['incident_id'] = 'international-summits-'+summits['incident_id']
    summits['incident_type'] = 'summits'

    summits = summits[VARIABLES_REPORTS]

    return summits


def process_military_offensive_reports(military_offensive):

    eu_countries = get_european_union_countries()

    list_columns = [
        'cleaned_attacking_countries',
        'cleaned_targeted_countries'
    ]

    for column in list_columns:
      military_offensive[column] = military_offensive[column].fillna('[]')
      military_offensive.loc[military_offensive[column] == '[nan]',column] = '[]'
      military_offensive[column] = military_offensive[column].fillna('[]')

    military_offensive['cleaned_attacking_countries'] = military_offensive['cleaned_attacking_countries'].apply(lambda x: ast.literal_eval(x))
    military_offensive['cleaned_targeted_countries'] = military_offensive['cleaned_targeted_countries'].apply(lambda x: ast.literal_eval(x))

    military_offensive.loc[
        military_offensive['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ] = military_offensive.loc[
        military_offensive['cleaned_attacking_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_attacking_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_offensive.loc[
        military_offensive['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ] = military_offensive.loc[
        military_offensive['cleaned_targeted_countries'].apply(lambda x: len(set(x) & set(eu_countries)) > 0),
        'cleaned_targeted_countries'
    ].apply(lambda x: list(set(x + ['European Union'])))

    military_offensive['cleaned_attacking_countries'] = military_offensive['cleaned_attacking_countries'].astype(str)
    military_offensive['cleaned_targeted_countries'] = military_offensive['cleaned_targeted_countries'].astype(str)

    military_offensive = military_offensive.rename(columns={
        'num_reports':'number_of_reports',
        'cleaned_attacking_countries':'initiating_countries',
        'cleaned_targeted_countries':'receiving_countries',
    })

    military_offensive['receiving_economic_sectors'] = np.nan
    military_offensive['benefiting_countries'] = np.nan
    military_offensive['receivers'] = military_offensive['receiving_countries']
    military_offensive['initiators'] = military_offensive['initiating_countries']
    military_offensive['beneficiaries'] = np.nan
    military_offensive['incident_sub_types'] = np.nan

    military_offensive['report_id'] = 'military-offensive-'+military_offensive['report_id']
    military_offensive['incident_id'] = 'military-offensive-'+military_offensive['incident_id']
    military_offensive['incident_type'] = 'military-offensive'

    military_offensive = military_offensive[VARIABLES_REPORTS]

    return military_offensive


def process_sanctions_embeddings(sanctions_embeddings):

    sanctions_embeddings['incident_id'] = 'sanctions-'+sanctions_embeddings['incident_id']

    return sanctions_embeddings


def process_cyber_embeddings(cyber_embeddings):

    cyber_embeddings['incident_id'] = 'cyber-'+cyber_embeddings['incident_id']

    return cyber_embeddings


def process_military_aid_embeddings(military_aid_embeddings):

    military_aid_embeddings['incident_id'] = 'military-aid-'+military_aid_embeddings['incident_id']

    return military_aid_embeddings


def process_summits_embeddings(summits_embeddings):

    summits_embeddings['incident_id'] = 'international-summits-'+summits_embeddings['incident_id']

    return summits_embeddings


def process_military_offensive_embeddings(military_offensive_embeddings):

    military_offensive_embeddings['incident_id'] = 'military-offensive-'+military_offensive_embeddings['incident_id']

    return military_offensive_embeddings


def merge_datasets_incidents(datasets):

    incidents = pd.concat(datasets).reset_index(drop=True)

    list_columns = [
        'benefiting_countries',
        'receiving_countries',
        'receiving_economic_sectors',
        'beneficiaries',
        'receivers',
        'incident_sub_types'
    ]

    for column in list_columns:
        incidents[column] = incidents[column].fillna('[]')
        incidents.loc[incidents[column] == '[nan]',column] = '[]'
        incidents[column] = incidents[column].fillna('[]')

    #saving elements in list with double quotes instead of single quotes to be able to use json.loads
    incidents['url_list'] = incidents['url_list'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['source_url_list'] = incidents['source_url_list'].apply(lambda x: json.dumps([i for i in eval(x,{"__builtins__": None}, {"nan": np.nan}) if pd.notna(i)]))
    incidents['initiating_countries'] = incidents['initiating_countries'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['benefiting_countries'] = incidents['benefiting_countries'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['receiving_countries'] = incidents['receiving_countries'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['receiving_economic_sectors'] = incidents['receiving_economic_sectors'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['initiators'] = incidents['initiators'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['beneficiaries'] = incidents['beneficiaries'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['receivers'] = incidents['receivers'].apply(lambda x: json.dumps(ast.literal_eval(x)))
    incidents['incident_sub_types'] = incidents['incident_sub_types'].apply(lambda x: json.dumps([i for i in eval(x,{"__builtins__": None}, {"nan": np.nan}) if pd.notna(i)]))

    incidents['number_of_distinct_receivers'] = incidents['receivers'].apply(lambda x: len(set(x)))

    return incidents


def merge_datasets_reports(sanctions,cyber,military_aid,summits,military_offensive):

    reports = pd.concat([sanctions,cyber,military_aid,summits,military_offensive]).reset_index(drop=True)

    list_columns = [
        'initiating_countries',
        'benefiting_countries',
        'receiving_countries',
        'receiving_economic_sectors',
        'initiators',
        'beneficiaries',
        'receivers'
    ]

    for column in list_columns:
        reports[column] = reports[column].fillna('[]')
        reports.loc[reports[column] == '[nan]',column] = '[]'
        reports[column] = reports[column].fillna('[]')

        #saving elements in list with double quotes instead of single quotes to be able to use json.loads
        reports[column] = reports[column].apply(lambda x: json.dumps(ast.literal_eval(x)))

    reports = reports.rename(columns={
        'date':'report_start_date',
        'number_of_reports':'number_of_reports_in_incident',
        'initiating_countries':'normalized_initiating_countries',
        'benefiting_countries':'normalized_benefiting_countries',
        'receiving_countries':'normalized_receiving_countries',
        'receiving_economic_sectors':'normalized_receiving_economic_sectors'
    })

    return reports


def merge_embeddings(embeddings_datasets):

    embeddings = pd.concat(embeddings_datasets).reset_index(drop=True)

    embeddings['embedding'] = embeddings[[str(i) for i in range(1536)]].values.tolist()
    embeddings = embeddings.drop(columns=[str(i) for i in range(1536)])

    return embeddings
    
    
def merge_incidents_and_embeddings(incidents,embeddings):
    
    incidents = incidents.merge(embeddings,on='incident_id',how='left')

    incidents = incidents.drop(columns=[
        'content_list',
        'summaries'
    ])

    incidents['embedding'] = incidents['embedding'].astype(str)

    return incidents


def join_datasets_incidents(
        sanctions_file_path,
        cyber_file_path,
        military_aid_file_path,
        summits_file_path,
        military_offensive_file_path,
        sanctions_embeddings_file_path,
        cyber_embeddings_file_path,
        military_aid_embeddings_file_path,
        summits_embeddings_file_path,
        military_offensive_embeddings_file_path
    ):

    bucket = get_bucket()

    sanctions = get_csv_data(sanctions_file_path,bucket)
    cyber = get_csv_data(cyber_file_path,bucket)
    military_aid = get_csv_data(military_aid_file_path,bucket)
    summits = get_csv_data(summits_file_path,bucket)
    military_offensive = get_csv_data(military_offensive_file_path,bucket)

    sanctions_embeddings = get_csv_data(sanctions_embeddings_file_path,bucket)
    cyber_embeddings = get_csv_data(cyber_embeddings_file_path,bucket)
    military_aid_embeddings = get_csv_data(military_aid_embeddings_file_path,bucket)
    summits_embeddings = get_csv_data(summits_embeddings_file_path,bucket)
    military_offensive_embeddings = get_csv_data(military_offensive_embeddings_file_path,bucket)

    sanctions = process_sanctions_incidents(sanctions)
    cyber = process_cyber_incidents(cyber)
    military_aid = process_military_aid_incidents(military_aid)
    summits = process_summits_incidents(summits)
    military_offensive = process_military_offensive_incidents(military_offensive)

    sanctions_embeddings = process_sanctions_embeddings(sanctions_embeddings)
    cyber_embeddings = process_cyber_embeddings(cyber_embeddings)
    military_aid_embeddings = process_military_aid_embeddings(military_aid_embeddings)
    summits_embeddings = process_summits_embeddings(summits_embeddings)
    military_offensive_embeddings = process_military_offensive_embeddings(military_offensive_embeddings)

    datasets = [sanctions,cyber,military_aid,summits,military_offensive]
    embeddings_datasets = [sanctions_embeddings,cyber_embeddings,military_aid_embeddings,summits_embeddings,military_offensive_embeddings]

    incidents = merge_datasets_incidents(datasets)

    incidents_for_json = incidents.copy(deep=True)

    incidents_for_json = incidents_for_json[[
        'incident_id',
        'incident_start_date',
        'incident_summary',
        'number_of_reports',
        'content_list',
        'summaries',
        'url_list',
        'source_url_list',
        'initiating_countries',
        'benefiting_countries',
        'receiving_countries',
        'receiving_economic_sectors',
        'initiators',
        'beneficiaries',
        'receivers',
        'incident_sub_types',
        'incident_type'
    ]].rename(columns={
        'number_of_reports':'number_of_reports_in_incident',
        'content_with_date':'content_list',
        'summaries':'summary_list',
        'url':'url_list',
        'source_url':'source_url_list',
        'initiating_countries':'normalized_initiating_countries',
        'benefiting_countries':'normalized_benefiting_countries',
        'receiving_countries':'normalized_receiving_countries',
        'receiving_economic_sectors':'normalized_receiving_economic_sectors'
    })

    incidents_for_json['incident_summary'] = incidents_for_json['incident_summary'].str.split('\n').str[1:].apply(lambda x: '\n'.join(x)) #removing the date from the incident summary

    clean_for_api_and_write_as_json(base_url='databases/global_geopolitical_events_database_incidents.json',bucket=bucket,data=incidents_for_json)

    embeddings = merge_embeddings(embeddings_datasets)
    incidents = merge_incidents_and_embeddings(incidents,embeddings)

    write_file_path = 'cross-analyses/all_incidents.parquet'

    write_parquet_data(incidents,write_file_path,bucket)

    return write_file_path


def join_datasets_reports(
        sanctions_file_path,
        cyber_file_path,
        military_aid_file_path,
        summits_file_path,
        military_offensive_file_path
    ):

    bucket = get_bucket()

    sanctions = get_csv_data(sanctions_file_path,bucket)
    cyber = get_csv_data(cyber_file_path,bucket)
    military_aid = get_csv_data(military_aid_file_path,bucket)
    summits = get_csv_data(summits_file_path,bucket)
    military_offensive = get_csv_data(military_offensive_file_path,bucket)

    sanctions = process_sanctions_reports(sanctions)
    cyber = process_cyber_reports(cyber)
    military_aid = process_military_aid_reports(military_aid)
    summits = process_summits_reports(summits)
    military_offensive = process_military_offensive_reports(military_offensive)

    reports = merge_datasets_reports(sanctions,cyber,military_aid,summits,military_offensive)

    clean_for_api_and_write_as_json(base_url='databases/global_geopolitical_events_database_reports.json',bucket=bucket,data=reports)

    return 'databases/global_geopolitical_events_database_reports.json'