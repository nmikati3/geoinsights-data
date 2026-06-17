import pandas as pd
import ast


def build_incidents_table(report_table):

    report_table['publish_date'] = pd.to_datetime(report_table['publish_date'])

    report_table['url'] = report_table['url'].apply(lambda x: ast.literal_eval(x))
    report_table['source_url'] = report_table['source_url'].apply(lambda x: ast.literal_eval(x))
    report_table['cleaned_targeted_economic_sectors'] = report_table['cleaned_targeted_economic_sectors'].apply(lambda x: ast.literal_eval(x))
    report_table['cleaned_attacking_countries'] = report_table['cleaned_attacking_countries'].apply(lambda x: ast.literal_eval(x))
    report_table['cleaned_targeted_countries'] = report_table['cleaned_targeted_countries'].apply(lambda x: ast.literal_eval(x))
    report_table['cleaned_attackers'] = report_table['cleaned_attackers'].fillna('[]').apply(lambda x: ast.literal_eval(x))
    report_table['victims'] = report_table['victims'].fillna('[]').apply(lambda x: ast.literal_eval(x))

    report_table['url'] = report_table['url'].apply(lambda x: list(x))
    report_table['source_url'] = report_table['source_url'].apply(lambda x: list(x))

    report_table['content_with_date'] = 'Date: ' + report_table['incident_start_date'].astype(str) + '/n' + report_table['content']

    incidents = report_table.groupby(['incident_id'],as_index=False).agg({
        'incident_start_date':'min',
        'report_id':pd.Series.nunique,
        'url':lambda x: sum(x, []),
        'source_url':lambda x: sum(x, []),
        'content_with_date':list,
        'summary':list,
        'cleaned_attacking_countries':lambda x: sum(x, []),
        'cleaned_targeted_countries':lambda x: sum(x, []),
        'cleaned_targeted_economic_sectors':lambda x: sum(x, []),
        'cleaned_attackers':lambda x: sum(x, []),
        'victims':lambda x: sum(x, []),
        'cleaned_cyber_incident_type':list
    }).rename(columns={
        'report_id':'number_of_reports'
    })

    incidents['url'] = incidents['url'].apply(lambda x: list(set(x)))
    incidents['source_url'] = incidents['source_url'].apply(lambda x: list(set(x)))
    incidents['content_with_date'] = incidents['content_with_date'].apply(lambda x: list(set(x)))
    incidents['summary'] = incidents['summary'].apply(lambda x: list(set(x)))
    incidents['cleaned_attacking_countries'] = incidents['cleaned_attacking_countries'].apply(lambda x: list(set(x)))
    incidents['cleaned_targeted_countries'] = incidents['cleaned_targeted_countries'].apply(lambda x: list(set(x)))
    incidents['cleaned_targeted_economic_sectors'] = incidents['cleaned_targeted_economic_sectors'].apply(lambda x: list(set(x)))
    incidents['cleaned_attackers'] = incidents['cleaned_attackers'].apply(lambda x: list(set(x)))
    incidents['cleaned_cyber_incident_type'] = incidents['cleaned_cyber_incident_type'].apply(lambda x: list(set(x)))

    incidents['url'] = incidents['url'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['source_url'] = incidents['source_url'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['content_with_date'] = incidents['content_with_date'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['summary'] = incidents['summary'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['cleaned_attacking_countries'] = incidents['cleaned_attacking_countries'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['cleaned_targeted_countries'] = incidents['cleaned_targeted_countries'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['cleaned_targeted_economic_sectors'] = incidents['cleaned_targeted_economic_sectors'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['cleaned_attackers'] = incidents['cleaned_attackers'].apply(lambda x: [i for i in x if i != 'Unknown'])
    incidents['cleaned_cyber_incident_type'] = incidents['cleaned_cyber_incident_type'].apply(lambda x: [i for i in x if i != 'Unknown'])

    return incidents




