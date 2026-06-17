from geoinsights_data.join_datasets.join_func import join_datasets_incidents, join_datasets_reports

def main():
    join_datasets_incidents(
        'geopolitics/sanctions/incidents_summarized.csv',
        'cyber/incidents/incidents.csv',
        'geopolitics/military-aid/incidents_summarized.csv',
        'geopolitics/summits/incidents_summarized.csv',
        'geopolitics/military-offensive/incidents_summarized.csv',
        'geopolitics/sanctions/incidents_summarized_embeddings.csv',
        'cyber/incidents/incidents_embeddings.csv',
        'geopolitics/military-aid/incidents_summarized_embeddings.csv',
        'geopolitics/summits/incidents_summarized_embeddings.csv',
        'geopolitics/military-offensive/incidents_summarized_embeddings.csv'
    )

    join_datasets_reports(
        'geopolitics/sanctions/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',
        'cyber/events/collected_translated_classified_with_content_reclassified_summarized_countries_sectors_other_labels_clustered_with_source_info.csv',
        'geopolitics/military-aid/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',
        'geopolitics/summits/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv',
        'geopolitics/military-offensive/collected_translated_classified_with_content_reclassified_summarized_countries_clustered_with_source_info.csv'
    )

if __name__ == "__main__":
    main()