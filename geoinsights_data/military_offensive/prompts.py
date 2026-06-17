from geoinsights_data.utils.collect import get_countries


def compute_llm_classify_article_system_prompt():
  system_prompt = '''
Your goal is to determine whether press articles describe one nation attacking another nation or not.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    filter_value: string // True if the article is describing a military offensive from one nation against another nation, False otherwise
}
'''

  return system_prompt


def compute_summarize_article_system_prompt():

  system_prompt = """
Your goal is to extract a 1-sentence summary in English from articles describing military offensives.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    summary: string // 1-sentence summary of the articles
}

Make sure to include in your summary any mention of the country that is behind the military offensive and the country that is being attacked.
Only summarize the main topic of the article.

You may already have prior knowledge of the military offensives from your training data. You will refrain from using that knowledge and base your only answer on the article's content.
All your answers MUST be in English.
"""

  return system_prompt


def compute_label_countries_in_article_system_prompt():

  countries = get_countries()

  system_prompt = """
<role>
Your goal is to extract information from articles describing military offensives.
</role>

<format>
You will be provided with a list of articles, and you will output a json object containing the following information:

{{
    attacking_countries: string[] // the list of countries behind the military offensive based on the article's content,
    targeted_countries: string[] // the list of countries targeted by the military offensive based on the article's content
}}
</format>

<instructions>
You may already have prior knowledge of that event from your training data. You will refrain from using that knowledge and base your only answer on the articles' contents.

attacking_countries must take values in the following list: {countries}
targeted_countries must take values in the following list: {countries}
</instructions>
""".format(
    countries=';'.join(countries)
  )

  return system_prompt


def compute_incident_summary_system_prompt():

  system_prompt = f"""
<role>
Your goal is to extract a 1-sentence summary in English from articles describing military offensives.
</role>

<format>
You will be provided with a list of articles, and you will output a json object containing the following information:

{{
    summary: string // 1-sentence summary of in the articles
}}
</format>

<instructions>
Make sure to include in your summary any mention of the countries behind the military offensive and the countries targeted by the military offensive.
If there is a mention of a money amount, make sure to mention it.

There could be mentions of multiple numbers of casualties. If that's the case, mention the number of casualties that's mentioned most often.

You may already have prior knowledge of that event from your training data. You will refrain from using that knowledge and base your only answer on the articles' contents.

Each article contains the date when it was published. Articles published at a later date will have more accurate information on the event. Favor content from articles published at a later date.
All the articles should talk about the same event, however, in case there are multiple events, make sure to only report information from the main event discussed in most of the articles.
</instructions>
"""
  
  return system_prompt