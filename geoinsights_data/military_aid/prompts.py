from geoinsights_data.utils.collect import get_countries


def compute_llm_classify_article_system_prompt():
  system_prompt = '''
Your goal is to determine whether press articles describe one country providing military aid to another country or not.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    filter_value: string // True if the article is describing one country providing military aid to another country, False otherwise
}
'''

  return system_prompt


def compute_summarize_article_system_prompt():

  system_prompt = """
Your goal is to extract a 1-sentence summary in English from articles countries providing military aid to other countries.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    summary: string // 1-sentence summary of the articles
}

Make sure to include in your summary any mention of the countries providing the military aid and the countries receiving the military aid.

You may already have prior knowledge of that military aid from your training data. You will refrain from using that knowledge and base your only answer on the article's content.
All your answers MUST be in English.
"""

  return system_prompt



def compute_label_countries_in_article_system_prompt():

  countries = get_countries()

  system_prompt = f"""
<role>
Your goal is to identify the countries providing military aid and the countries receiving military aid from articles describing countries providing military aid to other countries.
</role>

<format>
You will be provided with a list of articles, and you will output a json object containing the following information:

{{
    providing_countries: string[] // the list of countries providing the military aid,
    receiving_countries: string[] // the list of countries receiving the military aid
}}
</format>

<instructions>
You may already have prior knowledge of that event from your training data. You will refrain from using that knowledge and base your only answer on the articles' contents.

providing_countries must take values in the following list: {countries}
receiving_countries must take values in the following list: {countries}
</instructions>
"""

  return system_prompt


def compute_incident_summary_system_prompt():

  system_prompt = f"""
<role>
Your goal is to extract a 1-sentence summary in English from articles describing countries providing military aid to other countries.
</role>

<format>
You will be provided with a list of articles, and you will output a json object containing the following information:

{{
    summary: string // 1-sentence summary of in the articles
}}
</format>

<instructions>
Make sure to include in your summary any mention of the countries providing the military aid, the countries receiving the military aid and the type of military aid provided (equipment, aircrafts, missiles, money, etc...).
If there is a mention of a money amount, make sure to mention it.

There could be mentions of multiple amounts of financial aid provided. If that's the case, mention the amount that's mentioned most often.

You may already have prior knowledge of that event from your training data. You will refrain from using that knowledge and base your only answer on the articles' contents.

Each article contains the date when it was published. Articles published at a later date will have more accurate information on the event. Favor content from articles published at a later date.
All the articles should talk about the same event, however, there may be some articles talking about different events. For example, the US has been provided military aid to Ukraine in its war against Russia in the form of financial aid. There have been multiple rounds of financial aid over the years, each with different amounts. While very similar, if the financial aid amount mentioned is different, then articles are talking about different events. When that's the case, make sure to only report information from the main discussed in most of the articles.
</instructions>
"""
  
  return system_prompt