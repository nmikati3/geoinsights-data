from geoinsights_data.utils.collect import get_countries


def compute_llm_classify_article_system_prompt():

  system_prompt = '''
Your goal is to determine whether press articles describe sanctions imposed by a country on another country or not.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    filter_value: string // True if the article is describing sanctions imposed by a country on another country, False otherwise
}
'''

  return system_prompt


def compute_summarize_article_system_prompt():

  system_prompt = """
Your goal is to extract a 1-sentence summary in English from articles describing geopolitical sanctions.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    summary: string // 1-sentence summary of the articles
}

Make sure to include in your summary any mention of the country that is imposing the sanctions and the country that is targeted by the sanctons.
Only summarize the main topic of the article.

You may already have prior knowledge of the sanctions from your training data. You will refrain from using that knowledge and base your only answer on the article's content.
All your answers MUST be in English.
"""

  return system_prompt


def compute_label_countries_in_article_system_prompt():

  countries = get_countries()

  system_prompt = """
Your goal is to extract information from articles describing geopolitical sanctions.
You will be provided with an article, and you will output a json object containing the following information:

{{
    imposing_country: string // Country that is imposing the sanctions based on the article's content,
    targeted_country: string // Country that is targeted by the sanctions based on the article's content
}}


The imposing_country refers to the country that is imposing the sanctions discussed in the article. It must be one of these: {countries}.
The targeted_country refers to the country that is targeted by sanctions cyberattack discussed in the article. It must be one of these: {countries}.

If you are not sure about the imposing_country or targeted_country, replace it with 'Unknown'.

""".format(
    countries=';'.join(countries)
  )

  return system_prompt


def compute_incident_summary_system_prompt():

  system_prompt = """
Your goal is to extract a 1-sentence summary in English from articles describing geopolitical sanctions.
You will be provided with a list of articles, and you will output a json object containing the following information:

{
    summary: string // 1-sentence summary of the articles
}

Make sure to include in your summary any mention of the country that is imposing the sanctions and the country that is targeted by the sanctons.
Only summarize the main topic from the list of articles.

You may already have prior knowledge of the sanctions from your training data. You will refrain from using that knowledge and base your only answer on the articles' contents.
All your answers MUST be in English.
"""

  return system_prompt
