import numpy as np
import pandas as pd

def capitalize_first_letter(x):
    try:
        return ' '.join([i[0].capitalize() + i[1:] for i in x.split(' ')]) if pd.notna(x) else np.nan
    except:
        x

def clean_summit_names_rules(df):

    df['cleaned_summit_name'] = df['summit_name']
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('G-','G')
    #order matters
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('EU Summit','European Union')
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('European Council','European Union')
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('EU Leaders Summit','European Union')
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('EU','European Union')
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('European Union Summit','European Union')
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace('SCO','Shanghai Cooperation Organization')
    df['cleaned_summit_name'] = df['cleaned_summit_name'].str.replace("'","")
    df['cleaned_summit_name'] = df['cleaned_summit_name'].apply(capitalize_first_letter) #capitalize first letter of each word
    
    df = df[df['cleaned_summit_name'].apply(lambda x: x is not None)].reset_index(drop=True)
    df = df.dropna(subset=['cleaned_summit_name']).reset_index(drop=True)

    return df