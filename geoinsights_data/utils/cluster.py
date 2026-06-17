import hdbscan
import torch
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from scipy.sparse.csgraph import connected_components
from geoinsights_data.utils.llm import compute_embeddings
import numpy as np
from sklearn.neighbors import KNeighborsClassifier


def cluster_data(docs,threshold,column,method='graph',min_samples=3,min_cluster_size=2):

  embeddings = compute_embeddings(docs)
  embeddings = torch.tensor(embeddings)

  embeddings_norm = embeddings / embeddings.norm(dim=1)[:, None]


  if method == 'graph':
    distance_matrix = torch.mm(embeddings_norm, embeddings_norm.transpose(0,1))
    distance_matrix = distance_matrix >= threshold
    _,labels = connected_components(csgraph=distance_matrix,directed=False,return_labels=True)

  elif method == 'hdb':
    hdb = hdbscan.HDBSCAN(min_samples=min_samples, min_cluster_size=min_cluster_size,cluster_selection_epsilon=threshold).fit(embeddings)
    labels = hdb.labels_
    m = max(labels) + 1
    labels = pd.Series(labels).reset_index()
    labels.loc[labels[0] == -1, 0] = labels.loc[labels[0] == -1, 'index'] + m
    labels = labels[0].values


  elif method == 'agglo':
    model = AgglomerativeClustering(n_clusters=None,metric='precomputed',distance_threshold=threshold,linkage='average')
    model.fit(distance_matrix)
    labels = model.labels_
    m = max(labels) + 1
    labels = pd.Series(labels).reset_index()
    labels.loc[labels[0] == -1, 0] = labels.loc[labels[0] == -1, 'index'] + m
    labels = labels[0].values

  labels = list(labels)

  clusters = pd.DataFrame([docs,labels],index=[column,'label']).T

  return clusters


def cluster_all(all_summaries,method,threshold,column):

  list_dates = list(all_summaries['week_end_date'].drop_duplicates().sort_values())

  docs = list(all_summaries[all_summaries['week_end_date'].isin([list_dates[0],list_dates[1]])][column])

  all_data = cluster_data(docs,threshold=threshold,column=column,method=method)

  for i in range(1,len(list_dates)-1):

    try:

      new_docs = list(all_summaries[all_summaries['week_end_date'].isin([list_dates[i],list_dates[i+1]])][column])

      all_data2 = cluster_data(new_docs,threshold=threshold,column=column,method=method)

      all_data2 = all_data2.rename(columns={'label':'new_label'})

      max_label = all_data['label'].max() + 1
      all_data2['new_label'] = all_data2['new_label'] + max_label

      mapping = pd.merge(all_data,all_data2,how='inner',on=column)[['label','new_label']].drop_duplicates()

      all_labels = list(mapping['label'].unique()) + list(mapping['new_label'].unique())

      adjacency_matrix = np.zeros((len(all_labels),len(all_labels)))

      mapping['label'] = mapping['label'].apply(lambda x: all_labels.index(x))
      mapping['new_label'] = mapping['new_label'].apply(lambda x: all_labels.index(x))

      indices = mapping.astype(int).values
      adjacency_matrix[indices[:,0],indices[:,1]] = 1
      adjacency_matrix[indices[:,1],indices[:,0]] = 1

      _,intermediate_labels = connected_components(csgraph=adjacency_matrix,directed=False,return_labels=True)

      mapping = pd.DataFrame([all_labels,intermediate_labels],index=['new_label','intermediate_label']).T

      mapping = pd.merge(
          mapping,
          mapping.groupby('intermediate_label',as_index=False).agg({'new_label':'max'}).rename(columns={'new_label':'new_label_max'}),
          how='left',
          on='intermediate_label'
      ).drop(columns=['intermediate_label']).drop_duplicates()

      all_data2 = pd.merge(
          all_data2,
          mapping,
          how='left',
          on='new_label'
      )

      all_data2['new_label'] = all_data2['new_label_max'].combine_first(all_data2['new_label'])
      all_data2 = all_data2.drop(columns=['new_label_max']).rename(columns={'new_label':'label'})

      mapping = mapping.rename(columns={'new_label':'label'})

      all_data = pd.merge(all_data,mapping,how='left',on='label')
      all_data['label'] = all_data['new_label_max'].combine_first(all_data['label'])
      all_data = all_data.drop(columns=['new_label_max'])

      all_data = pd.concat([all_data,all_data2]).drop_duplicates()

      del all_data2

    except Exception:
      continue

  return all_data


def recluster(docs,column,threshold):

  embeddings = compute_embeddings(docs)

  hdb = hdbscan.HDBSCAN(min_samples=1, min_cluster_size=max(3,len(docs)//500)).fit(embeddings)

  clusters = pd.DataFrame([docs,hdb.labels_],index=[column,'label']).T

  clusters = pd.concat([clusters,pd.DataFrame(embeddings)],axis=1)

  #assign a cluster to the noise points (points not labeled during the clustering using KNN)
  if (-1 in clusters['label'].unique()) & (clusters['label'].nunique() > 1):

    noise_mask = clusters['label'] == -1
    non_noise_mask = clusters['label'] != -1

    # Get non-noise points and their labels
    clean_data = clusters[non_noise_mask]

    # Train a kNN classifier on the clustered points
    knn = KNeighborsClassifier(n_neighbors=max(3,len(docs)//500))
    knn.fit(clean_data[list(range(len(embeddings[0])))], clean_data['label'].astype(str))

    clusters.loc[noise_mask,'pred_label'] = knn.predict(clusters[noise_mask][list(range(len(embeddings[0])))])

    clusters['pred_label'] = clusters['pred_label'].combine_first(clusters['label'])

  else:

    clusters = clusters.rename(columns={'label':'pred_label'})

  clusters_grouped = clusters.groupby('pred_label',as_index=False).agg({i: np.mean for i in range(len(embeddings[0]))})

  embeddings = torch.tensor(clusters_grouped.drop(columns=['pred_label']).values)

  embeddings_norm = embeddings / embeddings.norm(dim=1)[:, None]

  distance_matrix = torch.mm(embeddings_norm, embeddings_norm.transpose(0,1))
  distance_matrix = distance_matrix >= threshold
  _,labels = connected_components(csgraph=distance_matrix,directed=False,return_labels=True)

  clusters_grouped['new_label'] = labels

  clusters = pd.merge(clusters[[column,'pred_label']],clusters_grouped[['pred_label','new_label']],how='left',on='pred_label')

  return clusters.drop(columns=['pred_label'])


def run_clustering(to_cluster_df,threshold_cluster_all,threshold_recluster):

  #add week_end_date
  to_cluster_df['date'] = pd.to_datetime(to_cluster_df['date'],format='ISO8601')
  to_cluster_df['week_end_date'] = to_cluster_df['date'].apply(lambda x: (x + pd.offsets.Week(weekday=6)).date())

  #cluster summaries
  all_summaries = to_cluster_df[['summary','week_end_date']].drop_duplicates()
  all_data = cluster_all(all_summaries,method='graph',threshold=threshold_cluster_all,column='summary')

  #recluster summaries for clusters with more than 30 reports
  cluster_counts = all_data.label.value_counts().reset_index()
  new_data = pd.DataFrame([])

  for c in cluster_counts[cluster_counts['count'] >= 30]['label'].unique():
    docs = list(all_data[all_data['label'] == c]['summary'])
    clusters = recluster(docs,'summary',threshold_recluster)
    clusters['label'] = c
    new_data = pd.concat([new_data,clusters.drop_duplicates()])

  #merge new labels with old labels
  all_data = pd.merge(all_data,new_data.drop(columns=['label']),how='left',on='summary')
  all_data['label'] = all_data['label'].astype(int).astype(str) + '-' + all_data['new_label'].astype(str).str.replace('nan','nnn')

  #add incident id, num_reports, and incident_start_date
  to_cluster_df = pd.merge(to_cluster_df,all_data,how='left',on='summary')

  incidents = to_cluster_df.groupby(['label'],as_index=False).agg({
      'date':'min'
  })

  incidents['incident_id'] = incidents['date'].astype(str).str[:10].str.replace('-','') + '-' + incidents['label']

  to_cluster_df = pd.merge(to_cluster_df,incidents[['label','incident_id']],how='left',on='label').drop(columns=['week_end_date','label','new_label'])

  to_cluster_df = to_cluster_df.reset_index()
  to_cluster_df['report_id'] = to_cluster_df['date'].astype(str).str[:10].str.replace('-','') + '-' + to_cluster_df['index'].astype(str)
  to_cluster_df = to_cluster_df.drop(columns=['index'])

  to_cluster_df = to_cluster_df.set_index('incident_id')
  to_cluster_df['num_reports'] = to_cluster_df.groupby('incident_id')['report_id'].nunique()
  to_cluster_df['incident_start_date'] = to_cluster_df.groupby('incident_id')['date'].min()
  to_cluster_df['incident_start_date'] = to_cluster_df['incident_start_date'].astype(str).str[:10]
  to_cluster_df = to_cluster_df.reset_index()

  return to_cluster_df