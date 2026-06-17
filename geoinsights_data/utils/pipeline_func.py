from geoinsights_data.utils.collect import (
    get_csv_data,
    get_bucket,
    concatenate_data,
    write_csv_data,
    write_json_data,
    get_to_be_processed_data,
    query_gdelt,
    preprocess_gdelt,
)
from geoinsights_data.utils.translate import translate_dataset
from geoinsights_data.utils.classify import classify_data
from geoinsights_data.utils.add_content import get_content
from geoinsights_data.utils.llm import (
    llm_classify_data,
    summarize_data,  
    label
)
from geoinsights_data.utils.cluster import run_clustering
from geoinsights_data.utils.incident_summarize import incident_summarize_data, compute_incident_embeddings_data
import pandas as pd
import ast


def execute_task(
        read_file_path,
        task_function,
        path_to_add,
        column_to_join_on,
        *args,
        **kwargs
    ):

    write_file_path = read_file_path.replace('.csv',f'_{path_to_add}.csv')

    bucket = get_bucket()
    new_data = get_csv_data(read_file_path,bucket)

    try:
        already_collected = get_csv_data(write_file_path,bucket)
    except Exception:
        already_collected = pd.DataFrame([])

    new_data = get_to_be_processed_data(already_collected,new_data,column_to_join_on)

    new_data = task_function(new_data, *args, **kwargs)

    data = concatenate_data(already_collected,new_data)

    write_csv_data(data,write_file_path,bucket)

    return write_file_path


def collect(file_path,yaml_path):

    bucket = get_bucket()
    already_collected = get_csv_data(file_path,bucket)

    start_date = pd.to_datetime(already_collected['date'],format='ISO8601').max()

    #new_data = query_data(yaml_path,start_date) #commented out for now since scraping is stopped
    #new_data = preprocess(new_data)

    gdelt_data = query_gdelt(yaml_path,start_date)
    gdelt_data = preprocess_gdelt(gdelt_data)

    #new_data = pd.concat([new_data,gdelt_data]).sort_values('date').drop_duplicates(subset=['url'],keep='first').reset_index(drop=True)

    #data = concatenate_data(already_collected,new_data)
    data = concatenate_data(already_collected,gdelt_data)

    write_csv_data(data,file_path,bucket)

    return file_path


def translate(read_file_path):

    write_file_path = execute_task(
        read_file_path=read_file_path,
        task_function=translate_dataset,
        path_to_add="translated",
        column_to_join_on="preprocessed_url"
    )

    return write_file_path


def classify(read_file_path,model_path,threshold):

    write_file_path = execute_task(
        read_file_path=read_file_path,
        task_function=classify_data,
        path_to_add="classified",
        column_to_join_on="translated_url",
        model_path=model_path,
        threshold=threshold
    )

    return write_file_path


def add_content(read_file_path):

    write_file_path = execute_task(
        read_file_path=read_file_path,
        task_function=get_content,
        path_to_add="with_content",
        column_to_join_on="url"
    )

    return write_file_path


def llm_classify(read_file_path,system_prompt):

    write_file_path = execute_task(
        read_file_path=read_file_path,
        task_function=llm_classify_data,
        path_to_add="reclassified",
        column_to_join_on="content",
        system_prompt=system_prompt
    )

    return write_file_path


def summarize(read_file_path,system_prompt):

    write_file_path = execute_task(
        read_file_path=read_file_path,
        task_function=summarize_data,
        path_to_add="summarized",
        column_to_join_on="content",
        system_prompt=system_prompt,
        column_to_summarize="content"
    )

    return write_file_path


def label_summary(read_file_path,system_prompt,columns,path_to_add):

    write_file_path = execute_task(
        read_file_path=read_file_path,
        task_function=label,
        path_to_add=path_to_add,
        column_to_join_on="summary",
        system_prompt=system_prompt,
        columns=columns
    )

    return write_file_path


def cluster(read_file_path,threshold_cluster_all,threshold_recluster):

    bucket = get_bucket()
    data = get_csv_data(read_file_path,bucket)

    data = run_clustering(data,threshold_cluster_all,threshold_recluster)

    write_file_path = read_file_path.replace('.csv','_clustered.csv')

    write_csv_data(data,write_file_path,bucket)

    return write_file_path


def add_source_info(read_file_path):

    bucket = get_bucket()
    existing_sources = get_csv_data('sources/sources_analyzed.csv',bucket)

    data = get_csv_data(read_file_path,bucket)

    existing_sources = existing_sources[['source_url'] + [column_name for column_name in list(existing_sources) if column_name.startswith('cleaned')]]
    existing_sources.columns = existing_sources.columns.str.replace('cleaned_','source_')

    data['url'] = data['url'].apply(lambda x: ast.literal_eval(x))
    data['source_url'] = data['source_url'].apply(lambda x: ast.literal_eval(x))

    single_urls_df = data[data['url'].apply(lambda x: len(x) == 1)].reset_index(drop=True)
    multiple_urls_df = data[data['url'].apply(lambda x: len(x) > 1)].reset_index(drop=True)

    single_urls_df['url'] = single_urls_df['url'].apply(lambda x: list(x)[0])
    single_urls_df['source_url'] = single_urls_df['source_url'].apply(lambda x: list(x)[0])

    single_urls_df = pd.merge(single_urls_df,existing_sources,how='left',on='source_url')

    multiple_urls_df = multiple_urls_df.explode('url').reset_index(drop=True)
    multiple_urls_df['source_url'] = multiple_urls_df.apply(lambda x: [i for i in x['source_url'] if i in x['url']],axis=1)
    multiple_urls_df['source_url'] = multiple_urls_df['source_url'].str[0]

    multiple_urls_df = pd.merge(multiple_urls_df,existing_sources,how='left',on='source_url')

    df = pd.concat([multiple_urls_df,single_urls_df]).reset_index(drop=True)

    write_file_path = read_file_path.replace('.csv','_with_source_info.csv')

    write_csv_data(df,write_file_path,bucket)

    return write_file_path


def incident_summarize(
        read_file_path,
        write_file_path,
        system_prompt,
        columns_list_to_list,
        columns_string_to_list,
        columns_added,
        clean_victims=False,
        clean_victims_system_prompt=None
    ):

    bucket = get_bucket()
    new_data = get_csv_data(read_file_path,bucket)

    already_calculated_incidents = get_csv_data(write_file_path,bucket)

    data = incident_summarize_data(
        new_data,
        already_calculated_incidents,
        system_prompt,
        columns_list_to_list,
        columns_string_to_list,
        columns_added,
        clean_victims=clean_victims,
        clean_victims_system_prompt=clean_victims_system_prompt
    )

    write_csv_data(data,write_file_path,bucket)

    return write_file_path


def compute_incident_embeddings(read_file_path):

    bucket = get_bucket()
    incidents = get_csv_data(read_file_path,bucket)

    embeddings = compute_incident_embeddings_data(incidents)

    write_file_path = read_file_path.replace('.csv','_embeddings.csv')

    write_csv_data(embeddings,write_file_path,bucket)

    return write_file_path


def run_pipeline(
    file_path,
    yaml_path,
    model_path,
    threshold,
    llm_classify_system_prompt,
    summarize_system_prompt,
    labels,
    threshold_cluster_all,
    threshold_recluster,
    incident_write_file_path,
    incident_summarize_system_prompt,
    incident_columns_list_to_list,
    incident_columns_string_to_list,
    incident_columns_added,
    incident_clean_victims,
    incident_clean_victims_system_prompt
):

    file_path = collect(file_path,yaml_path)
    print('Finished collecting')
    file_path = translate(file_path)
    print('Finished translating')
    file_path = classify(file_path,model_path,threshold)
    print('Finished classifying')
    file_path = add_content(file_path)
    print('Finished adding content')
    file_path = llm_classify(file_path,llm_classify_system_prompt)
    print('Finished reclassifying')
    file_path = summarize(file_path,summarize_system_prompt)
    print('Finished summarizing')

    l = labels[0]
    label_system_prompt = l['system_prompt']
    labels_columns = l['columns']
    labels_path_to_add = l['path_to_add']

    file_path = label_summary(file_path,label_system_prompt,labels_columns,labels_path_to_add)

    for l in labels[1:]:
        label_system_prompt = l['system_prompt']
        labels_columns = l['columns']
        labels_path_to_add = l['path_to_add']

        file_path = label_summary(file_path,label_system_prompt,labels_columns,labels_path_to_add)

    print('Finished labeling')

    file_path = cluster(file_path,threshold_cluster_all,threshold_recluster)
    print('Finished clustering')

    file_path = add_source_info(file_path)
    print('Finished adding source info')

    file_path = incident_summarize(
        file_path,
        incident_write_file_path,
        incident_summarize_system_prompt,
        incident_columns_list_to_list,
        incident_columns_string_to_list,
        incident_columns_added,
        incident_clean_victims,
        incident_clean_victims_system_prompt
    )
    print('Finished creating incident table')

    file_path = compute_incident_embeddings(file_path)
    print('Finished getting embeddings')
