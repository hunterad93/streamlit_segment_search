### audience_processing prompts

BASIC_SYSTEM_PROMPT = "Be concise and precise."

COMPANY_RESEARCH_PROMPT = "Describe the target audience for {company_name}, focusing on their target customers and market niche."

AUDIENCE_BUILD_PROMPT = """
I am setting up an advertising campaign for {company_name} whose target audience is described as: {company_description}. When I set up my audiences, which audience segments should I exclude and which should I include? Let's focus on behavioral targeting. Describe a list of audience segments to include and exclude. Make sure to include basic obvious segments that could easily be taken for granted, as well as more nuanced and specific behavioral segments. Don't include the reasoning for why you chose the segments in your response, just the segments. Each segment should be a distinct audience that would be possible to target.
"""

JSON_AUDIENCE_BUILD_PROMPT = """Excellent, could you now reformat this into a structured JSON output, in this form:
{
  "Audience": {
    "included": {
      "Audience Group 1": [
        {
          "description": ""
        },
        {
          "description": ""
        }
      ],
      "Audience Group 2": [
        {
          "description": ""
        },
        {
          "description": ""
        }
      ]
    },
    "excluded": {
      "Audience Group 3": [
        {
          "description": ""
        },
        {
          "description": ""
        }
      ],
      "Audience Group 4": [
        {
          "description": ""
        },
        {
          "description": ""
        }
      ]
    }
  }
}
"""

INCLUDED_IMPROVING_PROMPT = """Please improve the included segments to better target the intended customers. The best inclusion strategy will target a set of less specific groups who compose the target audience when combined. Provide the updated JSON structure with the improved segments."""

EXCLUDED_IMPROVING_PROMPT = """Refine the excluded segments for optimal customer targeting. An effective exclusion strategy excludes groups whose intersection represents low-conversion prospects. Avoid describing segments through negation, for example instead of writing 'People who did not show interest in luxury products' write 'Budget shoppers'. Return the updated JSON structure with enhanced exclusion segments."""

REPHRASAL_PROMPT= """Rephrase the following segment descriptions to align with common audience segments discoverable in major data marketplaces (e.g., Facebook Audience Insights, Google Ads Audience Manager). If they are too complex to rephrase, split them into two simpler segments. Provide the updated JSON structure with the improved segments.
"""


UPDATE_SEGMENTS_PROMPT = """
Please update the audience segments based on the following instructions:

1. Remove the segments listed below:
{segments_to_remove}

2. Consider the user's intent behind these deletions.
3. Add new segments to replace the deleted ones, maintaining a similar total number of segments.
4. Ensure the new segments align with the overall audience profile and the user's apparent preferences.

Please provide the updated audience in the same JSON format as the current audience.
"""

FEEDBACK_PROMPT = """
    User feedback: {user_feedback}

    Please update the audience JSON based on the user's feedback. Describe a plan for implementing the changes, then provide the updated JSON.
    """

DELETE_SEGMENTS_PROMPT = """

Please delete the following segments

{deleted_segments}

Please respond with only the updated JSON.

"""

DECOMPOSE_PROMPT = """
Decompose the given specific audience segment into two broader, less specific segments. The intersection (overlap) of these two segments should closely match the original segment.

Original segment: {segment_description}

Please provide a numbered list of the two less specific segments.

Example:
Original segment: "Christian families with young children"
1. "Christians"
2. "Families with young children"

When you respond please only include the numbered list and nothing else.
"""

### Search prompts

RERANK_PROMPT = """On a scale of 0 to 100, how effective would the data segment be for targeting the user's desired audience?

Desired audience: "{query}"

Data segment: "{doc}"

Provide only a numeric score between 0 and 100, where 0 is not effective at all and 100 is extremely effective.
"""

### researcher prompts

INITIAL_RESEARCH_PROMPT = "Answer this question: how does {domain} collect {data_type} data that it sells to advertisers?"

ONLINE_SYSTEM_PROMPT = """Act as an advocate for the company you are asked about. Conclude your response with a list of URLS used from your search."""

OFFLINE_SYSTEM_PROMPT = """You are an AI assistant who is trying to get specific information about data brokers 
from a conversation partner who is connected to the internet. Your **ONLY** concern is the accuracy of the data, because 
you are investigating on behalf of advertisers who are paying for the data."""

CATEGORIZE_SEGMENT_PROMPT = """In short phrase categorize this data marketplace offering {segment}. Please provide only the brief categorization without any addditional explanation. Example categorizations would include: behavioral, demographic, financial, purchase behavior, value based, needs based etc."""

FOLLOW_UP_PROMPT = "Based on the previous conversation, generate a follow-up question to get more specific information. Phrase it as if you're the original user seeking clarification. Only provide the question, without any additional context or explanation."

SUMMARY_PROMPT = """Based on the following conversation about '{initial_prompt}', provide a concise summary for a non-technical advertiser. 
Focus on answering the initial question and find a single answer to satisfy the question. Keep it brief and easy to understand.

Conversation:
{conversation_history}

Your response should contain the summary alone, without providing a preamble or additional context.
"""

### report_generation prompts

REPORT_SYSTEM_PROMPT = "You are an expert data analyst specializing in audience segmentation and marketing strategy."

REPORT_PROMPT = """
Given the following summarized audience segment data, create an executive summary:

{summary_json}

Please summarize the audience targeting strategy in our {company_name} campaign, briefly
explaining who is being included and who is being excluded from the audience.
"""


### Deprecated prompts

AND_OR_PROMPT = """Now that we have a good set of segment descriptions to work with, we need to add AND/OR groupings. Let's do this in the JSON structure by including a JSON level with key = 'operator' and value = 'AND' or 'OR'. Use your best judgment about how to rearrange the targeting strategy under these operators although the outer level should always be OR. Return valid JSON without reasoning."""

INCLUDED_RESTRUCTURE_PROMPT ="""Given this set of audiences we are targeting in our advertising campaign for this company: {company_description}, how should we group them using and/or operators? {included_json}. And operators mean only the segments overlap will be targeted while or operators mean the individual segments are targeted separately. The outer level should always be OR, with inner levels of individual segments or AND groups. Please return valid JSON by maintaining the current JSON structure but adding a new level of JSON nesting where operator is the key and AND/OR is the value."""

EXCLUDED_RESTRUCTURE_PROMPT ="""Given this set of audiences we are excluding in our advertising campaign for this company: {company_description}, how should we group them using and/or operators? {excluded_json}. And operators mean only the segments overlap will be excluded while or operators mean the individual segments are excluded separately. The outer level should always be OR, with inner levels of individual segments or AND groups. Please return valid JSON by maintaining the current JSON structure but adding a new level of JSON nesting where operator is the key and AND/OR is the value."""

EXPANSION_PROMPT = """I have added AND/OR operators to better target my audience. AND operators indicate that only the overlap of segments will be targeted, while OR operators allow for targeting separately. Here is the updated JSON: {audience_with_operators}.
Please find ways to creatively improve my plan to better target {company_name} customers, you have license to rearrange, remove redundancies, and add new segments. Please return only valid JSON of the same structure without explanations or reasoning.
"""


CRITIQUE_PROMPT = """
Analyze the the segments we have so far. Identify specific segments to add, remove or rephrase.
Respond with a numbered list of changes that should be made to better target {company_name}'s customers,
while also being discoverable on a data marketplace.
"""

IMPLEMENTATION_PROMPT = """
Please implement the changes suggest above, returning the updated JSON structure.
"""

PAIRING_PROMPT = """
Look through the segments that we have generated so far. Some of these will need to be paired up in order to effectively
target the intended customers. Please pair up the segments into groups that are likely to convert only when a consumer is in both segments.
Respond with your set of suggestions for which segments should be paired.
"""

PAIRING_IMPLEMENTATION_PROMPT = """
Please implement the changes suggest above. You will need to create subgroups within included and excluded using "operator":"and"[] to group pairs suggested above.
For any segments that are not paired, please return them in the included or excluded groups as appropriate. Please return the updated JSON structure without explanations or reasoning.
"""

COMPARISON_DESCRIPTION="""
Target Customers
Texas Oncology primarily serves cancer patients and those with blood disorders. Their target customers include:
Cancer Patients: The organization caters to individuals diagnosed with various types of cancer, offering treatment and care throughout their cancer journey.
Blood Disorder Patients: Texas Oncology also provides care for patients with blood disorders.
Local Communities: With over 280 locations across Texas and southeastern Oklahoma, Texas Oncology aims to serve patients in their local communities, allowing them to receive treatment close to home.
Newly Diagnosed Patients: The organization offers resources and support for those who have recently received a cancer diagnosis.
Cancer Survivors: Texas Oncology provides ongoing care and support for cancer survivors, recognizing that survivorship begins at the time of diagnosis and continues throughout life.
Families and Caregivers: The organization acknowledges the importance of support from family and friends, considering them part of the cancer care journey
"""