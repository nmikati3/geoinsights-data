from geoinsights_data.utils.collect import get_countries, get_bucket, get_csv_data, write_csv_data
from geoinsights_data.utils.llm import clean_labels
import pandas as pd
import os
from openai import OpenAI
from pydantic import BaseModel
import ast
import numpy as np

def process_sources(sources):

    ownership_structures = ['independent', 'state-owned', 'corporate conglomerate', 'unknown']
    political_ideological_affiliations = ['far-left', 'left wing', 'center-left', 'centrist', 'center-right', 'right-wing', 'far-right', 'unknown']
    geographic_focuses = ['regional', 'national', 'international', 'unknown']
    target_audiences = ['general public', 'business', 'specialized', 'unknown']
    journalistic_styles = ['investigative', 'tabloid', 'wire service', 'academic', 'unknown']
    source_reliabilities = ['high', 'medium', 'low', 'unknown']

    system_prompt = f"""
You are an investigator. Your role is to study newspaper sources and identify key information.
You will be provided with the url of a newspaper website and you will output an object following the schema provided.

Here is a description of the parameters:
- outlet_name: the name of the outlet publishing the article
- country: the country of origin of the newspaper, must be one of: {get_countries()}
- owning_company: the company that owns the newpaper
- year_founded: the year the newspaper was founded
- ownership_structure: must be one of: {ownership_structures}
- political_ideological_affiliation: must be one of: {political_ideological_affiliations}
- geographic_focus: must be one of: {geographic_focuses}
- target_audience: must be one of: {target_audiences}
- journalistic_style: must be one: {journalistic_styles}
- source_reliability: the reliability of the newspaper as it is generally seen, must be one of: {source_reliabilities}
"""

    class Source(BaseModel):
        outlet_name:str
        country: str
        owning_company: str
        year_founded: str
        ownership_structure: str
        political_ideological_affiliation: str
        geographic_focus: str
        target_audience: str
        journalistic_style: str
        source_reliability: str

    CLIENT = OpenAI(
        api_key = os.environ.get('OPENAI_API_KEY')
    )

    def assess_source(source,system_prompt):

        completion = CLIENT.chat.completions.parse(
            model="gpt-4o-mini-search-preview",
            web_search_options={},
            response_format=Source,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": source,
                }
            ],
        ).choices[0].message.parsed

        return completion


    sources = list(sources['source_url'].unique())

    sources_seen = []
    labels = []

    for source in sources:
        try:
            labels.append(assess_source(source,system_prompt))
            sources_seen.append(source)
        except Exception:
            continue

    labeled = pd.DataFrame([sources,labels],index=['source_url','label']).T

    labeled['outlet_name'] = labeled['label'].apply(lambda x: getattr(x, 'outlet_name', np.nan))
    labeled['country'] = labeled['label'].apply(lambda x: getattr(x, 'country', np.nan))
    labeled['owning_company'] = labeled['label'].apply(lambda x: getattr(x, 'owning_company', np.nan))
    labeled['year_founded'] = labeled['label'].apply(lambda x: getattr(x, 'year_founded', np.nan))
    labeled['ownership_structure'] = labeled['label'].apply(lambda x: getattr(x, 'ownership_structure', np.nan))
    labeled['political_ideological_affiliation'] = labeled['label'].apply(lambda x: getattr(x, 'political_ideological_affiliation', np.nan))
    labeled['geographic_focus'] = labeled['label'].apply(lambda x: getattr(x, 'geographic_focus', np.nan))
    labeled['target_audience'] = labeled['label'].apply(lambda x: getattr(x, 'target_audience', np.nan))
    labeled['journalistic_style'] = labeled['label'].apply(lambda x: getattr(x, 'journalistic_style', np.nan))
    labeled['source_reliability'] = labeled['label'].apply(lambda x: getattr(x, 'source_reliability', np.nan))

    labeled = labeled.drop(columns=['label']).drop_duplicates(subset=['source_url'])

    labeled = clean_labels(labeled,'source_url','country',get_countries(),'string','fuzzy',0.7,fill_missing_with='unknown')
    labeled = clean_labels(labeled,'source_url','ownership_structure',ownership_structures,'string','fuzzy',0.7,fill_missing_with='unknown')
    labeled = clean_labels(labeled,'source_url','political_ideological_affiliation',political_ideological_affiliations,'string','fuzzy',0.7,fill_missing_with='unknown')
    labeled = clean_labels(labeled,'source_url','geographic_focus',geographic_focuses,'string','fuzzy',0.7,fill_missing_with='unknown')
    labeled = clean_labels(labeled,'source_url','target_audience',target_audiences,'string','fuzzy',0.7,fill_missing_with='unknown')
    labeled = clean_labels(labeled,'source_url','journalistic_style',journalistic_styles,'string','fuzzy',0.7,fill_missing_with='unknown')
    labeled = clean_labels(labeled,'source_url','source_reliability',source_reliabilities,'string','fuzzy',0.7,fill_missing_with='unknown')

    return labeled


def main():
    
    bucket = get_bucket()

    existing_sources = get_csv_data('sources/sources_analyzed.csv',bucket)

    datasets = []

    file_paths = [
        'cyber/events/collected_translated_classified_with_content_reclassified_summarized_countries_sectors_other_labels_clustered.csv',
        'geopolitics/military-aid/collected_translated_classified_with_content_reclassified_summarized_countries_clustered.csv',
        'geopolitics/sanctions/collected_translated_classified_with_content_reclassified_summarized_countries_clustered.csv',
        'geopolitics/military-offensive/collected_translated_classified_with_content_reclassified_summarized_countries_clustered.csv',
        'geopolitics/summits/collected_translated_classified_with_content_reclassified_summarized_countries_clustered.csv'
    ]

    for file_path in file_paths:
        datasets.append(get_csv_data(file_path,bucket))

    sources = pd.concat([data[['source_url']] for data in datasets])
    sources['source_url'] = sources['source_url'].apply(lambda x: ast.literal_eval(x))
    sources = sources.explode('source_url').dropna().drop_duplicates()

    sources = pd.merge(sources,existing_sources[['source_url']].dropna().drop_duplicates(),how='left',on='source_url',indicator=True)
    sources = sources[sources['_merge'] == 'left_only']
    sources = sources.drop(columns=['_merge'])

    if len(sources) > 0:
        sources = process_sources(sources)

        sources = pd.concat([existing_sources, sources]).reset_index(drop=True)

        write_csv_data(sources,'sources/sources_analyzed.csv',bucket)

if __name__ == "__main__":
    main()