import pandas as pd
from google.cloud import storage, bigquery
import os
import pycountry
import re
import yaml
import json
from attackcti import attack_client
import requests
import ast


def get_bucket():
    
    bucket_name = os.environ.get("BUCKET_NAME")
    
    # Use Application Default Credentials (service account will be automatically detected)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    return bucket


def get_csv_data(file_path,bucket):

  blob = bucket.blob(file_path)

  with blob.open("r") as f:
    data = pd.read_csv(f)

  return data


def get_yaml_data(file_path,bucket):

  blob = bucket.blob(file_path)

  with blob.open("r") as f:
    data = yaml.safe_load(f)

  return data


def write_csv_data(data,file_path,bucket):

    blob = bucket.blob(file_path)

    with blob.open("w") as f:
        data.to_csv(f, index=False)


def write_parquet_data(data,file_path,bucket):

    blob = bucket.blob(file_path)

    with blob.open("wb") as f:
        data.to_parquet(f, index=False)


def write_json_data(data,file_path,bucket):

    for col in data.columns:
        data[col] = data[col].astype(str)

    data_json = data.to_dict(orient='records')

    blob = bucket.blob(file_path)

    with blob.open("w",encoding='utf-8') as f:
        json.dump(data_json, f, indent=2, ensure_ascii=False)


def transfer_csv_data(source_file_path,target_file_path,bucket):

    data = get_csv_data(source_file_path,bucket)

    write_csv_data(data,target_file_path,bucket)


def clean_for_api_and_write_as_json(base_url,bucket,data):

    write_json_data(data,base_url,bucket)

    data['incident_start_date'] = pd.to_datetime(data['incident_start_date'].astype(str).str[:10])

    if 'report_start_date' in data.columns:
        data['report_start_date'] = pd.to_datetime(data['report_start_date'].astype(str).str[:10])

        past_14_days_data = data[data['report_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=14)]
        past_1_year_data = data[data['report_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=1*365)]
        past_2_years_data = data[data['report_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=2*365)]
        past_5_years_data = data[data['report_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=5*365)]

    else:
        past_14_days_data = data[data['incident_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=14)]
        past_1_year_data = data[data['incident_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=1*365)]
        past_2_years_data = data[data['incident_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=2*365)]
        past_5_years_data = data[data['incident_start_date'] >= pd.Timestamp.now() - pd.Timedelta(days=5*365)]

    write_json_data(past_14_days_data,base_url.replace('.json','_past_14_days.json'),bucket)
    write_json_data(past_1_year_data,base_url.replace('.json','_past_1_year.json'),bucket)
    write_json_data(past_2_years_data,base_url.replace('.json','_past_2_years.json'),bucket)
    write_json_data(past_5_years_data,base_url.replace('.json','_past_5_years.json'),bucket)



def generate_keyword_filters(keywords):

    filters = [
        f"""REGEXP_CONTAINS(LOWER(DocumentIdentifier), r'({'|'.join(keywords[language])})')""" for language in list(keywords.keys())
    ]

    return filters


def query_gdelt(yaml_path,start_date):

    bucket = get_bucket()
    data = get_yaml_data(yaml_path,bucket)

    # Access the keywords
    keywords = data.get('keywords', {})
    filters = generate_keyword_filters(keywords)

    query = f"""
SELECT
    DATE AS date
    , GKGRECORDID AS record_id
    , LOWER(DocumentIdentifier) AS url
    , SourceCommonName AS source_url
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE
    (
      {' OR '.join(filters)}
    )
   AND DocumentIdentifier != ''
   AND DocumentIdentifier IS NOT NULL
   AND TIMESTAMP_TRUNC(_PARTITIONTIME, DAY) >= TIMESTAMP("{str(start_date)[:10]}")
""" #+ additional_filters
    
    # Use Application Default Credentials (service account will be automatically detected)
    project_id = os.environ.get("PROJECT_ID")
    bq_client = bigquery.Client(project=project_id)

    query_job = bq_client.query(query)

    return query_job.to_dataframe()


def query_data(yaml_path,start_date):

    bucket = get_bucket()
    
    keywords = get_yaml_data(yaml_path,bucket)

    keywords = sum(list(keywords['keywords'].values()),[])

    urls1 = get_csv_data('sources/urls1.csv',bucket)
    urls2 = get_csv_data('sources/urls2.csv',bucket)
    urls3 = get_csv_data('sources/urls3.csv',bucket)
    urls4 = get_csv_data('sources/urls4.csv',bucket)
    urls5 = get_csv_data('sources/urls5.csv',bucket)
    urls6 = get_csv_data('sources/urls6.csv',bucket)
    urls7 = get_csv_data('sources/urls7.csv',bucket)
    urls8 = get_csv_data('sources/urls8.csv',bucket)
    urls9 = get_csv_data('sources/urls9.csv',bucket)
    urls10 = get_csv_data('sources/urls10.csv',bucket)

    data = pd.concat(
        [urls1,urls2,urls3,urls4,urls5,urls6,urls7,urls8,urls9,urls10]
    )
    
    data['collection_date'] = pd.to_datetime(data['collection_date'])

    data = data.sort_values('collection_date').drop_duplicates(subset=['url'],keep='first').reset_index(drop=True)

    data = data[data['collection_date'] >= pd.to_datetime(start_date)]
    data = data[data['url'].apply(lambda x: any([keyword in x for keyword in keywords]))].reset_index(drop=True)

    data['record_id'] = ''

    data = data.rename(columns={
        'collection_date':'date',
        'source':'source_url'
    })

    data = data[['date','record_id','url','source_url']]

    return data


def preprocess(data):

    data['preprocessed_url'] = data['url'].apply(lambda x: ' '.join(re.split(r'[!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~]', max(x.split('/'), key=len))))
    data = data.drop_duplicates(subset=['url']).reset_index(drop=True)

    return data


def preprocess_gdelt(data):

    data['date'] = pd.to_datetime(data['date'].astype(str).str[:4] + '-' + data['date'].astype(str).str[4:6] + '-' + data['date'].astype(str).str[6:8])
    data['preprocessed_url'] = data['url'].apply(lambda x: ' '.join(re.split(r'[!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~]', max(x.split('/'), key=len))))

    data = data[data['date'] <= pd.Timestamp.now()]
    data = data.drop_duplicates(subset=['url']).reset_index(drop=True)

    return data


def concatenate_data(data_1,data_2):

  return pd.concat([data_1,data_2]).reset_index(drop=True)


def get_to_be_processed_data(already_collected,new_data,column_to_join_on):

    new_data['date'] = pd.to_datetime(new_data['date'],format='ISO8601')
    already_collected['date'] = pd.to_datetime(already_collected['date'],format='ISO8601')

    if len(already_collected) > 0:
        to_be_processed_df = pd.merge(new_data,already_collected[[column_to_join_on]].drop_duplicates(),how='outer',on=column_to_join_on,indicator=True)
        to_be_processed_df = to_be_processed_df[to_be_processed_df['_merge'] == 'left_only'].drop(columns=['_merge']).reset_index(drop=True)
        to_be_processed_df = to_be_processed_df[to_be_processed_df['date'] >= already_collected['date'].max() - pd.Timedelta(days=7)].reset_index(drop=True)
    else:
        to_be_processed_df = new_data.copy(deep=True)

    return to_be_processed_df


def get_countries():

    countries = [country.name for country in pycountry.countries]

    to_replace = {
        'Åland Islands':'Finland',
        'American Samoa':'United States',
        'French Southern Territories':'France',
        'Bonaire, Sint Eustatius and Saba':'Netherlands',
        'Saint Barthélemy':'France',
        'Bolivia, Plurinational State of':'Bolivia',
        'Brunei Darussalam':'Brunei',
        'Bouvet Island':'Norway',
        'Cocos (Keeling) Islands':'Australia',
        'Curaçao':'Netherlands',
        'Christmas Island':'Australia',
        'Cayman Islands':'United Kingdom',
        'Falkland Islands (Malvinas)':'United Kingdom',
        'Micronesia, Federated States of':'Micronesia',
        'Guernsey':'United Kingdom',
        'Gibraltar':'United Kingdom',
        'Guadeloupe':'France',
        'French Guiana':'France',
        'Guam':'United States',
        'Hong Kong':'China',
        'Heard Island and McDonald Islands':'Australia',
        'Isle of Man':'United Kingdom',
        'British Indian Ocean Territory':'United Kingdom',
        'Iran, Islamic Republic of':'Iran',
        'Jersey':'United Kingdom',
        'Korea, Republic of':'South Korea',
        "Lao People's Democratic Republic":'Lao',
        'Saint Martin (French part)':'France',
        'Moldova, Republic of':'Moldova',
        'Northern Mariana Islands':'United States',
        'Montserrat':'United Kingdom',
        'Martinique':'France',
        'Mayotte':'France',
        'New Caledonia':'France',
        'Norfolk Island':'Australia',
        'Niue':'New Zealand',
        'Pitcairn':'United Kingdom',
        "Korea, Democratic People's Republic of":'North Korea',
        'Palestine, State of':'Palestine',
        'French Polynesia':'France',
        'Réunion':'France',
        'Russian Federation':'Russia',
        'South Georgia and the South Sandwich Islands':'United Kingdom',
        'Saint Helena, Ascension and Tristan da Cunha':'United Kingdom',
        'Svalbard and Jan Mayen':'Norway',
        'Saint Pierre and Miquelon':'France',
        'Sint Maarten (Dutch part)':'Netherlands',
        'Syrian Arab Republic':'Syria',
        'Tokelau':'New Zealand',
        'Türkiye':'Turkey',
        'Taiwan, Province of China':'Taiwan',
        'Tanzania, United Republic of':'Tanzania',
        'United States Minor Outlying Islands':'United States',
        'Holy See (Vatican City State)':'Vatican',
        'Venezuela, Bolivarian Republic of':'Venezuela',
        'Virgin Islands, British':'United Kingdom',
        'Virgin Islands, U.S.':'United States',
        'Turks and Caicos Islands':'United Kingdom',
        'Cook Islands':'New Zealand',
    }

    countries = list(set([to_replace[country] if country in to_replace.keys() else country for country in countries])) + ['European Union', 'NATO']

    return countries


def get_european_union_countries():

    eu_countries = [
        'Austria',
        'Belgium',
        'Bulgaria',
        'Croatia',
        'Cyprus',
        'Czechia',
        'Denmark',
        'Estonia',
        'Finland',
        'France',
        'Germany',
        'Greece',
        'Hungary',
        'Ireland',
        'Italy',
        'Latvia',
        'Lithuania',
        'Luxembourg',
        'Malta',
        'Netherlands',
        'Poland',
        'Portugal',
        'Romania',
        'Slovakia',
        'Slovenia',
        'Spain',
        'Sweden'
    ]

    return eu_countries


def get_sectors():

    sectors = [
        'Public Administration',
        'Healthcare',
        'Education',
        'Finance and Insurance',
        'Manufacturing',
        'Retail',
        'Transportation and Warehousing',
        'Media, Arts, Entertainment and Recreation',
        'Energy',
        'Technology',
        'Hospitality and Food Services',
        'Agriculture, Forestry, and Fishing',
        'Construction',
        'Wholesale Trade',
        'Professional, Scientific, and Technical Services',
        'Real Estate, Rental, and Leasing',
        'Utilities',
        'Telecommunications'
    ]

    return sectors


def get_subsectors():

    sectors_with_subsectors = {
        'Public Administration':[
            'Executive Offices and Agencies',
            'Public Finance and Revenue Administration',
            'Judicial and Legal Services',
            'Public Safety and Law Enforcement',
            'Social Services Administration'
        ],
        'Healthcare':[
            'Hospitals',
            'Outpatient Care Centers',
            'Medical and Diagnostic Laboratories',
            'Home Healthcare Services',
            'Nursing and Residential Care Facilities'
        ],
        'Education':[
            'Primary and Secondary Schools',
            'Higher Education (Colleges and Universities)',
            'Vocational and Technical Training',
            'Educational Support Services',
            'Adult and Continuing Education'
        ],
        'Finance and Insurance':[
            'Banking',
            'Insurance Carriers',
            'Securities, Commodities, and Investments',
            'Financial Planning and Advisory Services',
            'Credit Intermediation'
        ],
        'Manufacturing':[
            'Food and Beverage Manufacturing',
            'Chemical Manufacturing',
            'Machinery Manufacturing',
            'Electronics and Computer Manufacturing',
            'Transportation Equipment Manufacturing'
        ],
        'Retail':[
            'Grocery Stores',
            'Clothing and Apparel Stores',
            'Electronics and Appliance Stores',
            'Automobile Dealers',
            'Home and Garden Supply Stores'
        ],
        'Transportation and Warehousing':[
            'Air Transportation',
            'Rail Transportation',
            'Trucking and Freight Services',
            'Warehousing and Storage',
            'Urban Transit Systems'
        ],
        'Media, Arts, Entertainment and Recreation':[
            'Motion Picture and Video Production',
            'Broadcasting (Television, Radio)',
            'Performing Arts Companies',
            'Amusement Parks and Arcades',
            'Sports Teams and Clubs'
        ],
        'Energy':[
            'Oil and Gas Extraction',
            'Renewable Energy Production',
            'Electric Power Generation',
            'Natural Gas Distribution',
            'Petroleum Refining'
        ],
        'Technology':[
            'Software Development',
            'IT Services and Consulting',
            'Computer Systems Design',
            'Data Processing and Hosting',
            'Semiconductor Manufacturing'
        ],
        'Hospitality and Food Services':[
            'Hotels and Motels',
            'Restaurants',
            'Catering Services',
            'Bars and Nightclubs',
            'Event Planning and Management'
        ],
        'Agriculture, Forestry, and Fishing':[
            'Crop Production',
            'Animal Husbandry',
            'Forestry and Logging',
            'Commercial Fishing',
            'Agricultural Support Services'
        ],
        'Construction':[
            'Residential Building Construction',
            'Nonresidential Building Construction',
            'Specialty Trade Contractors',
            'Heavy and Civil Engineering Construction',
            'Land Subdivision and Site Preparation'
        ],
        'Wholesale Trade':[
            'Wholesale of Durable Goods',
            'Wholesale of Nondurable Goods',
            'Wholesale of Agricultural Products',
            'Wholesale Trade Agents and Brokers',
            'Motor Vehicle and Motor Vehicle Parts Wholesale'
        ],
        'Professional, Scientific, and Technical Services':[
            'Legal Services',
            'Accounting and Bookkeeping',
            'Architectural and Engineering Services',
            'Scientific Research and Development',
            'Management Consulting'
        ],
        'Real Estate, Rental, and Leasing':[
            'Residential Property Leasing and Management',
            'Commercial Property Leasing and Management',
            'Real Estate Brokerage Services',
            'Car and Equipment Rental',
            'Self-Storage Facilities'
        ],
        'Utilities':[
            'Electric Power Distribution',
            'Water Supply and Irrigation Systems',
            'Natural Gas Distribution',
            'Sewage Treatment Facilities',
            'Waste Management and Remediation Services'
        ],
        'Telecommunications':[
            'Wireless Telecommunications',
            'Wired Telecommunications',
            'Satellite Communications',
            'Cable and Other Subscription Services',
            'Internet Service Providers'
                ]
    }

    return sectors_with_subsectors


def get_cyber_incident_types():

    cyber_incident_types = [
        'Data Theft',
        'Data Theft and Doxing',
        'Disruption',
        'Hijacking',
            'Ransomware'
    ]

    return cyber_incident_types


def get_threat_actors():

    bucket = get_bucket()

    file_path = 'cyber/threats/tgc-actors.json'

    blob = bucket.blob(file_path)

    # Open and read blob content as JSON
    with blob.open("r") as f:
        tgc = json.load(f)

    tgc = [i['value'] for i in tgc['values'] if i != '']
    tgc = [i for i in tgc if i[0] != '[']

    tgc = pd.DataFrame(tgc,columns=['associated_groups'])
    tgc['name_tgc'] = tgc['associated_groups']

    try:

        client = attack_client()

        groups = client.get_groups()

        group_references = []
        group_aliases = []

        for group in groups:
            group_references.append(group.get('name'))
            group_aliases.append(group.get('aliases', []))

        groups_cti = pd.DataFrame([group_references,group_aliases],index=['name_cti','associated_groups']).T

        url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
        response = requests.get(url)
        bundle = response.json()

        intrusion_sets = [
            obj for obj in bundle["objects"]
            if obj.get("type") == "intrusion-set"
        ]

        group_references = []
        group_aliases = []

        for i in intrusion_sets:
            group_references.append(i["name"])
            aliases = i.get("aliases")
            if aliases:
                group_aliases.append(list(set(aliases) | set([i["name"]])))
            else:
                group_aliases.append([i['name']])

        groups_stix = pd.DataFrame([group_references,group_aliases],index=['name_stix','associated_groups']).T

        groups = pd.merge(groups_cti.explode('associated_groups'),groups_stix.explode('associated_groups'),how='outer',on='associated_groups')
        groups['name'] = groups['name_cti'].combine_first(groups['name_stix'])

        groups = pd.merge(groups,tgc,how='outer',on='associated_groups')
        groups['name'] = groups['name'].combine_first(groups['name_tgc'])

        groups = groups.groupby('name',as_index=False).agg({'associated_groups':list})

        all_groups = list(set(groups['associated_groups'].explode()))

        return all_groups

    except:

        groups = get_csv_data('cyber/threats/groups.csv',bucket)

        groups = groups['Associated Groups'].apply(lambda x: ast.literal_eval(x)).explode().drop_duplicates()

        all_groups = list(set(tgc['associated_groups']) | set(groups))
        all_groups = [i.strip() for i in all_groups]

        return all_groups