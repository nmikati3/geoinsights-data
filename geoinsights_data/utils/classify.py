import pickle
from geoinsights_data.utils.collect import get_bucket
from geoinsights_data.utils.llm import compute_embeddings
import numpy as np
import os
import torch
import torch.nn as nn
import pandas as pd


class LinearClassifier(nn.Module):

  def __init__(self,hidden_size):
    super(LinearClassifier, self).__init__()

    self.hidden_size = hidden_size
    self.linear = nn.Linear(hidden_size,1)

  def forward(self,inputs):
    return torch.sigmoid(self.linear(inputs))


def classify_data(to_classify_df, model_path, threshold):

  bucket = get_bucket()
  blob = bucket.blob(model_path)

  # Open the blob as a file-like object and read it directly into pandas
  with blob.open("rb") as f:
    Lr = pickle.load(f)
  
  threshold = float(os.environ.get(threshold))

  to_classify_df = to_classify_df.dropna(subset=['translated_url'])
  
  X = np.array(compute_embeddings(list(to_classify_df['translated_url'])))

  to_classify_df['openai_proba'] = Lr.predict_proba(X)[:,1]
  to_classify_df['openai_pred'] = Lr.predict(X)

  to_classify_df = to_classify_df[to_classify_df['openai_proba'] >= threshold].reset_index(drop=True)
  to_classify_df = to_classify_df.drop(columns=['openai_proba','openai_pred'])

  return to_classify_df

  
def cyber_classify(to_classify_df):

  bucket = get_bucket()
  file_path = 'cyber/models/linear-classifier/top_words.csv'
  blob = bucket.blob(file_path)

  with blob.open("r") as f:
    top_words = pd.read_csv(f)

  top_words = list(top_words['word'])

  Lc = LinearClassifier(len(top_words))

  file_path = 'cyber/models/linear-classifier/classification_model.pth'
  blob = bucket.blob(file_path)

  # Open the blob as a file-like object and read it directly into pandas
  with blob.open("rb") as f:
    Lc.load_state_dict(torch.load(f))

  Lc.eval()

  cyber_classification_threshold = os.environ.get("CYBER_CLASSIFICATION_THRESHOLD")

  for word in top_words:
    to_classify_df[word] = to_classify_df['url_words'].apply(lambda x: word in x).astype(float)

  to_classify_df['linear_pred'] = Lc(torch.tensor(to_classify_df[top_words].values).float()).detach().numpy()
  to_classify_df['linear_pred'] = round(to_classify_df['linear_pred'],2)
  to_classify_df['linear_pred'] = to_classify_df['linear_pred'] >= cyber_classification_threshold

  to_classify_df = to_classify_df[to_classify_df['linear_pred']][[
    'date','record_id','url','source_url','preprocessed_url','language','translated_url'
  ]].reset_index(drop=True)

  return to_classify_df

