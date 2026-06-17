from geoinsights_data.utils.collect import get_countries, get_sectors, get_cyber_incident_types


def compute_llm_classify_article_system_prompt():
  system_prompt = '''
Your goal is to determine whether press articles describe a cyberattack or not.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    filter_value: string // True if the article is describing a cyberattack, False otherwise
}
'''

  return system_prompt


def compute_summarize_article_system_prompt():

  system_prompt = """
Your goal is to extract a 1-sentence summary in English from articles describing cyberattacks.
You will be provided with an article's content, and you will output a json object containing the following information:

{
    summary: string // 1-sentence summary of the articles
}

Make sure to include in your summary any mention of the countries behind the attack or the countries targeted by the attack.

You may already have prior knowledge of that cyberattack from your training data. You will refrain from using that knowledge and base your only answer on the article's content.
All your answers MUST be in English.
"""

  return system_prompt



def compute_label_countries_in_article_system_prompt():

  countries = get_countries()

  system_prompt = """
Your goal is to extract information from articles describing cyberattacks.
You will be provided with an article, and you will output a json object containing the following information:

{{
    attacking_countries: string[] // List of attacking countries based on the article's content,
    targeted_countries: string[] // List of targeted countries based on the article's content
}}


The attacking_countries refer to the countries that are behind the main cyberattack discussed in the article. It must be one of these: {countries}.
The targeted_countries refer to the countries that are targeted by the main cyberattack discussed in the article. It must be one of these: {countries}.

If you are not sure that a country should be included in the list of attacking countries or the list of targeted countries, it is better not to include it in the lists than to include it. In doubt, lean towards the most conservative option.

When extracting information follow these examples:
Article: "Suspected hackers from North Korea attempted to infiltrate the systems of British pharmaceutical company AstraZeneca, which is working on COVID-19 vaccines, by posing as recruiters on LinkedIn and WhatsApp to send malicious code, although no successful attempts were reported. Cyberattacks have also been attributed to Iran, China, and Russia, targeting organizations like the WHO."
Answer: {{
  'attacking_countries': ['North Korea'],
  'targeted_countries': ['United Kingdom']
}}
// Iran, China and Russia should not be included in the list of attacking countries because they were not involved in the main cyberattack, but they were involved on other cyberattacks.

Article: "Cloudflare reported a record-breaking DDoS attack targeting one of their Free plan customers, with the attacker using a botnet of 5,067 devices from 121 countries including Indonesia, the United States, Brazil, and Russia, and the attack being conducted over HTTPS. The attack highlights the increasing sophistication of DDoS attacks, with threat actors leveraging poorly configured servers to amplify malicious traffic, and recent trends show cybercriminals combining ransomware attacks with DDoS attacks for cyberextortion."
Answer: {{
 'attacking_countries': [],
 'targeted_countries': ['Indonesia', 'United States', 'Brazil', 'Russia']
}}
// There is no mention of any attacking country, so the list should be empty.

Article: "Criminal proceedings were launched in Switzerland in connection to a cyber-attack against the World Anti-Doping Agency, with Russian involvement suspected, targeting organizations investigating doping of Russian athletes and nerve agent testing laboratories."
Answer: {{
 'attacking_countries': ['Russia'],
 'targeted_countries': []
}}
// Based on the article, it is not possible to know whether Switzerland was targeted by the cyberattack or not, so it should not be included in the list of targeted countries.

Article: "North Korean hacker group Lazarus targeted financial institutions in Poland, India, Taiwan, and several African countries, with stolen funds potentially intended for North Korea's nuclear program, following previous attacks including a $31 million theft from the Central Bank of Russia."
Answer: {{
 'attacking_countries': ['North Korea'],
 'targeted_countries': ['Poland','India','Taiwan']
}}
// Based on the article, it is not possible to know which African countries were targeted, so you should not include any.

Article: "The hacker group Network Battalion 65, affiliated with Anonymous, claimed to have hacked the Russian state television All-Russia State Television and Radio Broadcasting Company in support of Ukraine, following previous cyberattacks on the Central Bank of Russia by Anonymous amidst the ongoing conflict between Russia and Ukraine."
Answer: {{
  'attacking_countries': [],
  'targeted_countries': ['Russia']
}}
// The hacker group is acting in support of Ukraine, not against Ukraine, so Ukraine should not be included in the list of targeted countries. Also, even though the hacker group is acting in support of Ukraine, the article does not say that Ukraine is behind the attack, so Ukraine should not be included in the list of attacking countries.

""".format(
    countries=';'.join(countries)
  )

  return system_prompt


def compute_label_sectors_in_article_system_prompt():

  sectors = get_sectors()

  system_prompt = """
Your goal is to extract information from articles describing cyberattacks.
You will be provided with an article, and you will output a json object containing the following information:

{{
    targeted_economic_sectors: string[] // List of targeted economic sectors based on the article's content
}}

If you are not sure that a sector should be included in the list of targeted economic sectors, it is better not to include it in the lists than to include it. In doubt, lean towards the most conservative option.

The targeted_economic_sectors refer to the economic sectors that are targeted by the cyberattack. It must be one of these: {sectors}.

When extracting information follow these examples:
Article: "Suspected hackers from North Korea attempted to infiltrate the systems of British pharmaceutical company AstraZeneca, which is working on COVID-19 vaccines, by posing as recruiters on LinkedIn and WhatsApp to send malicious code, although no successful attempts were reported. Cyberattacks have also been attributed to Iran, China, and Russia, targeting organizations like the WHO."
Answer: {{
  'targeted_economic_sectors': ['Healthcare']
}}
// The Technology sector should not be included as WhatsApp and LinkedIn are not the direct targets of the cyberattack. The Public Administration sector should not be included as the WHO is not the main target of the cyberattack.

Article: "The hacker group Network Battalion 65, affiliated with Anonymous, claimed to have hacked the Russian state television All-Russia State Television and Radio Broadcasting Company in support of Ukraine, following previous cyberattacks on the Central Bank of Russia by Anonymous amidst the ongoing conflict between Russia and Ukraine."
Answer: {{
  'targeted_economic_sectors': ['Media, Arts, Entertainment and Recreation']
}}
// The Finance and Insurance sector should not be included, because the previous cyberattacks on the Central Bank of Russia are not the main cyberattack discussed in the article.

""".format(
    sectors=';'.join(sectors)
  )

  return system_prompt

  
def compute_label_other_labels_in_article_system_prompt():

  cyber_incident_types = get_cyber_incident_types()

  system_prompt = """
Your goal is to extract information from articles describing cyberattacks.
You will be provided with an article, and you will output a json object containing the following information:

{{
    attackers: string[] // List of the threat actors behind the cyberattack based on the article's content,
    victims: string[] // List of actors targeted by the cyberattack based on the article's content,
    cyber_incident_type: string // Type of cyber incident
}}

The attackers refer to the threat actors that are behind the cyberattack.
The victims refer to the victims that are targeted by the cyberattack.
The cyber_incident_type refers to the type among {cyber_incident_types}.

If you are not sure about a cyber incident type, it is better not to include than to include it. In doubt, lean towards the most conservative option.

You may already have prior knowledge of that cyberattack from your training data. You will refrain from using that knowledge and base your only answer on the article's content.

When extracting information follow these examples:
Article: "Suspected hackers from North Korea attempted to infiltrate the systems of British pharmaceutical company AstraZeneca, which is working on COVID-19 vaccines, by posing as recruiters on LinkedIn and WhatsApp to send malicious code, although no successful attempts were reported. Cyberattacks have also been attributed to Iran, China, and Russia, targeting organizations like the WHO."
Answer: {{
  'attackers': ['North Korea'],
  'victims': ['AstraZeneca'],
  'cyber_incident_type': ''
}}
// Iran, China, and Russia should not be included in the list of attackers as they are not responsible for the main cyberattack discussed in the article. Similarly, WHO should not be included in the list of targets as it is not the main target of the cyberattack. The cyber incident type field should be left empty as there is no information on the type of cyber incident in the article.

Article: "Cloudflare reported a record-breaking DDoS attack targeting one of their Free plan customers, with the attacker using a botnet of 5,067 devices from 121 countries including Indonesia, the United States, Brazil, and Russia, and the attack being conducted over HTTPS. The attack highlights the increasing sophistication of DDoS attacks, with threat actors leveraging poorly configured servers to amplify malicious traffic, and recent trends show cybercriminals combining ransomware attacks with DDoS attacks for cyberextortion."
Answer: {{
  'attackers': [],
  'victims': ['Cloudflare'],
  'cyber_incident_type': 'Disruption'
 }}
 // The cyber_incident_type should be Disruption as a DDoS attack constitutes a Disruption.

 Article: "A group of hackers retaliated by hacking over 250 Pakistani websites after the official website of the Kerala government in India and the Pakistani President's official website were hacked, leading to a digital war between India and Pakistan."
 Answer: {{
  'attackers': [A group of hackers],
  'victims': ['250 Pakistani websites'],
  'cyber_incident_type': 'Hijacking'
 }}
 // The 'Kerala government', and the 'Pakistani President' should not be included in the list of targets are they are not the targets of the main cyberattack discussed in the article.

Article: "Yahoo, now owned by American telecom operator Verizon, reveals that a cyberattack in 2013 affected all three billion user accounts, not just one billion as initially reported, with no passwords, banking data, or payment information stolen, and continues to work closely with law enforcement to ensure user security."
Answer: {{
  'attackers': [],
  'victims': ['Yahoo'],
  'cyber_incident_type': ''
}}
// The cyber_incident_type field should not be Data Theft, since the article mentions no passwords, banking data, or payment information stolen.

Article: "North Korean hacker group Lazarus targeted financial institutions in Poland, India, Taiwan, and several African countries, with stolen funds potentially intended for North Korea's nuclear program, following previous attacks including a $31 million theft from the Central Bank of Russia."
Answer: {{
  'attackers': ['Lazarus'],
  'victims': ['financial institutions in Poland, India, Taiwan, and several African countries'],
  'cyber_incident_type': ''
}}
// The cyber_incident_type is not Data Theft, funds were stolen, not data!

""".format(
    cyber_incident_types=';'.join(cyber_incident_types)
  )

  return system_prompt


def compute_incident_summary_system_prompt():

  system_prompt = system_prompt = """
Your goal is to extract a 1-sentence summary in English from articles describing cyberattacks.
You will be provided with a list of articles that discuss the same cyberattack, and you will output a json object containing the following information:

{
    summary: string // 1-sentence summary of the main cyberattack described in the articles
}

Make sure to only include in your summary information pertaining to the main cyberattack discussed in the articles. Also, make sure to include in your summary any mention of the countries behind the attack, the countries targeted by the attack, information on the victim as well as information on the tactics used to perform the attack.

You may already have prior knowledge of that cyberattack from your training data. You will refrain from using that knowledge and base your only answer on the article's content.

Each article contains the date when it was published. Articles published at a later date will have more accurate information on the cyberattack. Favor content from articles published at a later date.
"""

  return system_prompt


def compute_clean_victims_system_prompt():

  system_prompt = """
You are an AI assistant extracting information from lists of victims of cyberattacks. Your goal is to extract from a list of victims of cyberattacks, the list of distinct victims from the attack as some victim names might be repeated under different spelling.
You will be provided with a list of victims of a cyberattack, and you will output an object following the schema provided.
Here is a description of the parameters:
- victims: the list of distinct victims of the attack
"""

  return system_prompt