from geoinsights_data.utils.collect import (
    get_countries,
    get_sectors,
    get_cyber_incident_types,
    get_threat_actors,
    get_bucket,
    get_csv_data
)
from geoinsights_data.utils.pipeline_func import run_pipeline
from geoinsights_data.utils.collect import clean_for_api_and_write_as_json
import os

def main():
    task_index = int(os.environ.get("CLOUD_RUN_TASK_INDEX", 0))

    if task_index == 0:

        from geoinsights_data.cyber.prompts import (
            compute_llm_classify_article_system_prompt,
            compute_summarize_article_system_prompt,
            compute_label_countries_in_article_system_prompt,
            compute_label_sectors_in_article_system_prompt,
            compute_label_other_labels_in_article_system_prompt,
            compute_incident_summary_system_prompt,
            compute_clean_victims_system_prompt
        )

        columns_countries = {
            "attacking_countries": {
                "column_type":"list",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.7
            },
            "targeted_countries": {
                "column_type":"list",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.7
            }
        }

        columns_sectors = {
            "targeted_economic_sectors": {
                "column_type":"list",
                "reference_labels":get_sectors(),
                "matching_type":"fuzzy",
                "threshold":0.7
            }
        }

        columns_other_labels = {
            "attackers": {
                "column_type":"list",
                "reference_labels":get_threat_actors(),
                "matching_type":"exact",
                "threshold":1
            },
            "victims": {
                "column_type":"",
                "reference_labels":[],
                "matching_type":"no matching",
                "threshold":None
            },
            "cyber_incident_type": {
                "column_type":"string",
                "reference_labels":get_cyber_incident_types(),
                "matching_type":"fuzzy",
                "threshold":0.7
            },
        }

        incident_columns_list_to_list = [
            'cleaned_attacking_countries',
            'cleaned_targeted_countries',
            'cleaned_targeted_economic_sectors',
            'cleaned_attackers',
            'victims'
        ]

        incident_columns_string_to_list = [
            'cleaned_cyber_incident_type'
        ]

        incident_columns_added = [
            'cleaned_victims',
            'number_of_victims'
        ]

        labels = [
            {
                'system_prompt':compute_label_countries_in_article_system_prompt(),
                'columns':columns_countries,
                'path_to_add':'countries'
            },
            {
                'system_prompt':compute_label_sectors_in_article_system_prompt(),
                'columns':columns_sectors,
                'path_to_add':'sectors'
            },
            {
                'system_prompt':compute_label_other_labels_in_article_system_prompt(),
                'columns':columns_other_labels,
                'path_to_add':'other_labels'
            }
        ]

        run_pipeline(
            file_path='cyber/events/collected.csv',
            yaml_path='cyber/keywords.yaml',
            model_path='cyber/models/linear-classifier/cyber_classification_model.pkl',
            threshold='CYBER_CLASSIFICATION_THRESHOLD',
            llm_classify_system_prompt=compute_llm_classify_article_system_prompt(),
            summarize_system_prompt=compute_summarize_article_system_prompt(),
            labels=labels,
            threshold_cluster_all=0.7,
            threshold_recluster=0.85,
            incident_write_file_path='cyber/incidents/incidents.csv',
            incident_summarize_system_prompt=compute_incident_summary_system_prompt(),
            incident_columns_list_to_list=incident_columns_list_to_list,
            incident_columns_string_to_list=incident_columns_string_to_list,
            incident_columns_added=incident_columns_added,
            incident_clean_victims=True,
            incident_clean_victims_system_prompt=compute_clean_victims_system_prompt()
        )

        bucket = get_bucket()

        data = get_csv_data('cyber/events/collected_translated_classified_with_content_reclassified_summarized_countries_sectors_other_labels_clustered_with_source_info.csv',bucket)

        data = data[[
            'url',
            'source_url',
            'report_id',
            'date',
            'incident_id',
            'incident_start_date',
            'num_reports',
            'content',
            'summary',
            'cleaned_attacking_countries',
            'cleaned_targeted_countries',
            'cleaned_targeted_economic_sectors',
            'cleaned_attackers',
            'victims',
            'cleaned_cyber_incident_type',
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]].rename(columns={
            'date':'report_start_date',
            'num_reports':'number_of_reports_in_incident',
            'cleaned_attacking_countries':'normalized_attacking_countries',
            'cleaned_targeted_countries':'normalized_targeted_countries',
            'cleaned_targeted_economic_sectors':'normalized_targeted_sectors',
            'cleaned_attackers':'normalized_attackers',
            'cleaned_cyber_incident_type':'normalized_cyber_incident_type'
        })

        for column in [
            'normalized_attacking_countries',
            'normalized_targeted_countries',
            'normalized_targeted_sectors',
            'normalized_attackers',
            'victims'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        for column in [
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]:
            data.loc[data[column] == 'nan',column] = ''
            data[column] = data[column].fillna('')

        data['report_start_date'] = data['report_start_date'].astype(str).str[:10]

        clean_for_api_and_write_as_json(base_url='databases/global_cyberattacks_database_reports.json',bucket=bucket,data=data)

        data = get_csv_data('cyber/incidents/incidents.csv',bucket)

        data = data[[
            'incident_id',
            'incident_start_date',
            'incident_summary',
            'number_of_reports',
            'content_with_date',
            'summaries',
            'url',
            'source_url',
            'cleaned_attacking_countries',
            'cleaned_targeted_countries',
            'cleaned_targeted_economic_sectors',
            'cleaned_attackers',
            'cleaned_cyber_incident_type',
            'cleaned_victims',
        ]].rename(columns={
            'number_of_reports':'number_of_reports_in_incident',
            'content_with_date':'content_list',
            'summaries':'summary_list',
            'url':'url_list',
            'source_url':'source_url_list',
            'cleaned_attacking_countries':'normalized_attacking_countries',
            'cleaned_targeted_countries':'normalized_targeted_countries',
            'cleaned_targeted_economic_sectors':'normalized_targeted_sectors',
            'cleaned_attackers':'normalized_attackers',
            'cleaned_cyber_incident_type':'normalized_cyber_incident_type',
            'cleaned_victims':'normalized_victims'
        })

        for column in [
            'normalized_attacking_countries',
            'normalized_targeted_countries',
            'normalized_targeted_sectors',
            'normalized_attackers',
            'normalized_victims'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        data['incident_summary'] = data['incident_summary'].str.split('\n').str[1:].apply(lambda x: '\n'.join(x)) #removing the date from the incident summary

        clean_for_api_and_write_as_json(base_url='databases/global_cyberattacks_database_incidents.json',bucket=bucket,data=data)


    elif task_index == 1:

        from geoinsights_data.military_aid.prompts import (
            compute_llm_classify_article_system_prompt,
            compute_summarize_article_system_prompt,
            compute_label_countries_in_article_system_prompt,
            compute_incident_summary_system_prompt
        )

        columns_countries = {
            "providing_countries": {
                "column_type":"list",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.7
            },
            "receiving_countries": {
                "column_type":"list",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.7
            }
        }

        incident_columns_list_to_list = [
            'cleaned_providing_countries',
            'cleaned_receiving_countries'
        ]

        incident_columns_string_to_list = []

        incident_columns_added = []

        labels = [
            {
                'system_prompt':compute_label_countries_in_article_system_prompt(),
                'columns':columns_countries,
                'path_to_add':'countries'
            }
        ]

        run_pipeline(
            file_path='geopolitics/military-aid/collected.csv',
            yaml_path='geopolitics/military-aid/keywords.yaml',
            model_path='geopolitics/military-aid/models/military-aid_classification_model.pkl',
            threshold='MILITARY_AID_CLASSIFICATION_THRESHOLD',
            llm_classify_system_prompt=compute_llm_classify_article_system_prompt(),
            summarize_system_prompt=compute_summarize_article_system_prompt(),
            labels=labels,
            threshold_cluster_all=0.9,
            threshold_recluster=0.91,
            incident_write_file_path='geopolitics/military-aid/incidents_summarized.csv',
            incident_summarize_system_prompt=compute_incident_summary_system_prompt(),
            incident_columns_list_to_list=incident_columns_list_to_list,
            incident_columns_string_to_list=incident_columns_string_to_list,
            incident_columns_added=incident_columns_added,
            incident_clean_victims=False,
            incident_clean_victims_system_prompt=None
        )

        bucket = get_bucket()

        data = get_csv_data('geopolitics/military-aid/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',bucket)

        data = data[[
            'url',
            'source_url',
            'report_id',
            'date',
            'incident_id',
            'incident_start_date',
            'num_reports',
            'content',
            'summary',
            'cleaned_providing_countries',
            'cleaned_receiving_countries',
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]].rename(columns={
            'date':'report_start_date',
            'num_reports':'number_of_reports_in_incident',
            'cleaned_providing_countries':'normalized_providing_countries',
            'cleaned_receiving_countries':'normalized_receiving_countries'
        })

        for column in [
            'normalized_providing_countries',
            'normalized_receiving_countries'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        for column in [
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]:
            data.loc[data[column] == 'nan',column] = ''
            data[column] = data[column].fillna('')

        data['report_start_date'] = data['report_start_date'].astype(str).str[:10]

        clean_for_api_and_write_as_json(base_url='databases/military_aid_announcements_database_reports.json',bucket=bucket,data=data)

        data = get_csv_data('geopolitics/military-aid/incidents_summarized.csv',bucket)

        data = data[[
            'incident_id',
            'incident_start_date',
            'incident_summary',
            'number_of_reports',
            'content_with_date',
            'summaries',
            'url',
            'source_url',
            'cleaned_providing_countries',
            'cleaned_receiving_countries',
        ]].rename(columns={
            'number_of_reports':'number_of_reports_in_incident',
            'content_with_date':'content_list',
            'summaries':'summary_list',
            'url':'url_list',
            'source_url':'source_url_list',
            'cleaned_providing_countries':'normalized_providing_countries',
            'cleaned_receiving_countries':'normalized_receiving_countries'
        })

        for column in [
            'normalized_providing_countries',
            'normalized_receiving_countries'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        data['incident_summary'] = data['incident_summary'].str.split('\n').str[1:].apply(lambda x: '\n'.join(x)) #removing the date from the incident summary

        clean_for_api_and_write_as_json(base_url='databases/military_aid_announcements_database_incidents.json',bucket=bucket,data=data)

    elif task_index == 2:

        from geoinsights_data.military_offensive.prompts import (
            compute_llm_classify_article_system_prompt,
            compute_summarize_article_system_prompt,
            compute_label_countries_in_article_system_prompt,
            compute_incident_summary_system_prompt
        )

        columns_countries = {
            "attacking_countries": {
                "column_type":"list",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.7
            },
            "targeted_countries": {
                "column_type":"list",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.7
            }
        }

        incident_columns_list_to_list = [
            'cleaned_attacking_countries',
            'cleaned_targeted_countries'
        ]

        incident_columns_string_to_list = []

        incident_columns_added = []

        labels = [
            {
                'system_prompt':compute_label_countries_in_article_system_prompt(),
                'columns':columns_countries,
                'path_to_add':'countries'
            }
        ]

        run_pipeline(
            file_path='geopolitics/military-offensive/collected.csv',
            yaml_path='geopolitics/military-offensive/keywords.yaml',
            model_path='geopolitics/military-offensive/models/military_offensive_classification_model.pkl',
            threshold='MILITARY_OFFENSIVE_CLASSIFICATION_THRESHOLD',
            llm_classify_system_prompt=compute_llm_classify_article_system_prompt(),
            summarize_system_prompt=compute_summarize_article_system_prompt(),
            labels=labels,
            threshold_cluster_all=0.7,
            threshold_recluster=0.85,
            incident_write_file_path='geopolitics/military-offensive/incidents_summarized.csv',
            incident_summarize_system_prompt=compute_incident_summary_system_prompt(),
            incident_columns_list_to_list=incident_columns_list_to_list,
            incident_columns_string_to_list=incident_columns_string_to_list,
            incident_columns_added=incident_columns_added,
            incident_clean_victims=False,
            incident_clean_victims_system_prompt=None
        )

        bucket = get_bucket()

        data = get_csv_data('geopolitics/military-offensive/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',bucket)

        data = data[[
            'url',
            'source_url',
            'report_id',
            'date',
            'incident_id',
            'incident_start_date',
            'num_reports',
            'content',
            'summary',
            'cleaned_attacking_countries',
            'cleaned_targeted_countries',
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]].rename(columns={
            'date':'report_start_date',
            'num_reports':'number_of_reports_in_incident',
            'cleaned_attacking_countries':'normalized_attacking_countries',
            'cleaned_targeted_countries':'normalized_targeted_countries'
        })

        for column in [
            'normalized_attacking_countries',
            'normalized_targeted_countries'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        for column in [
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]:
            data.loc[data[column] == 'nan',column] = ''
            data[column] = data[column].fillna('')

        data['report_start_date'] = data['report_start_date'].astype(str).str[:10]

        clean_for_api_and_write_as_json(base_url='databases/military_offensive_database_reports.json',bucket=bucket,data=data)

        data = get_csv_data('geopolitics/military-offensive/incidents_summarized.csv',bucket)

        data = data[[
            'incident_id',
            'incident_start_date',
            'incident_summary',
            'number_of_reports',
            'content_with_date',
            'summaries',
            'url',
            'source_url',
            'cleaned_attacking_countries',
            'cleaned_targeted_countries'
        ]].rename(columns={
            'number_of_reports':'number_of_reports_in_incident',
            'content_with_date':'content_list',
            'summaries':'summary_list',
            'url':'url_list',
            'source_url':'source_url_list',
            'cleaned_attacking_countries':'normalized_attacking_countries',
            'cleaned_targeted_countries':'normalized_targeted_countries'
        })

        for column in [
            'normalized_attacking_countries',
            'normalized_targeted_countries'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        data['incident_summary'] = data['incident_summary'].str.split('\n').str[1:].apply(lambda x: '\n'.join(x)) #removing the date from the incident summary

        clean_for_api_and_write_as_json(base_url='databases/military_offensive_database_incidents.json',bucket=bucket,data=data)

    elif task_index == 3:

        from geoinsights_data.sanctions.prompts import (
            compute_llm_classify_article_system_prompt,
            compute_summarize_article_system_prompt,
            compute_label_countries_in_article_system_prompt,
            compute_incident_summary_system_prompt
        )

        columns_countries = {
            "imposing_country": {
                "column_type":"string",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.9
            },
            "targeted_country": {
                "column_type":"string",
                "reference_labels":get_countries(),
                "matching_type":"fuzzy",
                "threshold":0.81
            }
        }

        incident_columns_list_to_list = [
        ]

        incident_columns_string_to_list = [
            'cleaned_imposing_country',
            'cleaned_targeted_country'
        ]

        incident_columns_added = []

        labels = [
            {
                'system_prompt':compute_label_countries_in_article_system_prompt(),
                'columns':columns_countries,
                'path_to_add':'countries'
            }
        ]

        run_pipeline(
            file_path='geopolitics/sanctions/collected.csv',
            yaml_path='geopolitics/sanctions/keywords.yaml',
            model_path='geopolitics/sanctions/models/openai_sanction_classification_model.pkl',
            threshold='SANCTION_CLASSIFICATION_THRESHOLD',
            llm_classify_system_prompt=compute_llm_classify_article_system_prompt(),
            summarize_system_prompt=compute_summarize_article_system_prompt(),
            labels=labels,
            threshold_cluster_all=0.7,
            threshold_recluster=0.85,
            incident_write_file_path='geopolitics/sanctions/incidents_summarized.csv',
            incident_summarize_system_prompt=compute_incident_summary_system_prompt(),
            incident_columns_list_to_list=incident_columns_list_to_list,
            incident_columns_string_to_list=incident_columns_string_to_list,
            incident_columns_added=incident_columns_added,
            incident_clean_victims=False,
            incident_clean_victims_system_prompt=None
        )

        bucket = get_bucket()

        data = get_csv_data('geopolitics/sanctions/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',bucket)

        data = data[[
            'url',
            'source_url',
            'report_id',
            'date',
            'incident_id',
            'incident_start_date',
            'num_reports',
            'content',
            'summary',
            'cleaned_imposing_country',
            'cleaned_targeted_country',
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]].rename(columns={
            'date':'report_start_date',
            'num_reports':'number_of_reports_in_incident',
            'cleaned_imposing_country':'normalized_imposing_country',
            'cleaned_targeted_country':'normalized_targeted_country'
        })

        for column in [
            'normalized_imposing_country',
            'normalized_targeted_country'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        for column in [
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]:
            data.loc[data[column] == 'nan',column] = ''
            data[column] = data[column].fillna('')

        data['report_start_date'] = data['report_start_date'].astype(str).str[:10]

        clean_for_api_and_write_as_json(base_url='databases/sanction_announcements_database_reports.json',bucket=bucket,data=data)

        data = get_csv_data('geopolitics/sanctions/incidents_summarized.csv',bucket)

        data = data[[
            'incident_id',
            'incident_start_date',
            'incident_summary',
            'number_of_reports',
            'content_with_date',
            'summaries',
            'url',
            'source_url',
            'cleaned_imposing_country',
            'cleaned_targeted_country',
        ]].rename(columns={
            'number_of_reports':'number_of_reports_in_incident',
            'content_with_date':'content_list',
            'summaries':'summary_list',
            'url':'url_list',
            'source_url':'source_url_list',
            'cleaned_imposing_country':'normalized_imposing_countries',
            'cleaned_targeted_country':'normalized_targeted_countries'
        })

        for column in [
            'normalized_imposing_countries',
            'normalized_targeted_countries'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        data['incident_summary'] = data['incident_summary'].str.split('\n').str[1:].apply(lambda x: '\n'.join(x)) #removing the date from the incident summary

        clean_for_api_and_write_as_json(base_url='databases/sanction_announcements_database_incidents.json',bucket=bucket,data=data)

    elif task_index == 4:

        from geoinsights_data.summits.prompts import (
            compute_llm_classify_article_system_prompt,
            compute_summarize_article_system_prompt,
            compute_label_countries_and_summit_names_in_article_system_prompt,
            compute_incident_summary_system_prompt
        )
        from geoinsights_data.utils.rules import clean_summit_names_rules

        columns_countries = {
            'participating_countries':{
                'column_type':'list',
                'reference_labels':get_countries(),
                'matching_type':'fuzzy',
                'threshold':0.7
            },
            'summit_name':{
                'column_type':'string',
                'reference_labels':[],
                'matching_type':'rules',
                'rule':clean_summit_names_rules,
                'threshold':None
            }
        }

        incident_columns_list_to_list = [
            'cleaned_participating_countries'
        ]

        incident_columns_string_to_list = [
            'cleaned_summit_name'
        ]

        incident_columns_added = []

        labels = [
            {
                'system_prompt':compute_label_countries_and_summit_names_in_article_system_prompt(),
                'columns':columns_countries,
                'path_to_add':'countries'
            }
        ]

        run_pipeline(
            file_path='geopolitics/summits/collected.csv',
            yaml_path='geopolitics/summits/keywords.yaml',
            model_path='geopolitics/summits/models/summits_classification_model.pkl',
            threshold='SUMMITS_CLASSIFICATION_THRESHOLD',
            llm_classify_system_prompt=compute_llm_classify_article_system_prompt(),
            summarize_system_prompt=compute_summarize_article_system_prompt(),
            labels=labels,
            threshold_cluster_all=0.8,
            threshold_recluster=0.85,
            incident_write_file_path='geopolitics/summits/incidents_summarized.csv',
            incident_summarize_system_prompt=compute_incident_summary_system_prompt(),
            incident_columns_list_to_list=incident_columns_list_to_list,
            incident_columns_string_to_list=incident_columns_string_to_list,
            incident_columns_added=incident_columns_added,
            incident_clean_victims=False,
            incident_clean_victims_system_prompt=None
        )

        bucket = get_bucket()

        data = get_csv_data('geopolitics/summits/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',bucket)

        data = data[[
            'url',
            'source_url',
            'report_id',
            'date',
            'incident_id',
            'incident_start_date',
            'num_reports',
            'content',
            'summary',
            'cleaned_participating_countries',
            'cleaned_summit_name',
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]].rename(columns={
            'date':'report_start_date',
            'num_reports':'number_of_reports_in_incident',
            'cleaned_participating_countries':'normalized_participating_countries',
            'cleaned_summit_name':'normalized_summit_name'
        })

        for column in [
            'normalized_participating_countries',
            'normalized_summit_name'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        for column in [
            'source_country',
            'source_ownership_structure',
            'source_political_ideological_affiliation',
            'source_geographic_focus',
            'source_target_audience',
            'source_journalistic_style',
            'source_source_reliability'
        ]:
            data.loc[data[column] == 'nan',column] = ''
            data[column] = data[column].fillna('')

        data['report_start_date'] = data['report_start_date'].astype(str).str[:10]

        clean_for_api_and_write_as_json(base_url='databases/international_summits_database_reports.json',bucket=bucket,data=data)

        data = get_csv_data('geopolitics/summits/incidents_summarized.csv',bucket)

        data = data[[
            'incident_id',
            'incident_start_date',
            'incident_summary',
            'number_of_reports',
            'content_with_date',
            'summaries',
            'url',
            'source_url',
            'cleaned_participating_countries',
            'cleaned_summit_name',
        ]].rename(columns={
            'number_of_reports':'number_of_reports_in_incident',
            'content_with_date':'content_list',
            'summaries':'summary_list',
            'url':'url_list',
            'source_url':'source_url_list',
            'cleaned_participating_countries':'normalized_participating_countries',
            'cleaned_summit_name':'normalized_summit_names'
        })

        for column in [
            'normalized_participating_countries',
            'normalized_summit_names'
        ]:

            data.loc[data[column] == '[nan]',column] = '[]'
            data[column] = data[column].fillna('[]')

        data['incident_summary'] = data['incident_summary'].str.split('\n').str[1:].apply(lambda x: '\n'.join(x)) #removing the date from the incident summary

        clean_for_api_and_write_as_json(base_url='databases/international_summits_database_incidents.json',bucket=bucket,data=data)

if __name__ == "__main__":
    main()