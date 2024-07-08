### audience_processing prompts

BASIC_SYSTEM_PROMPT = "Be concise and precise."

COMPANY_RESEARCH_PROMPT = "Describe the company {company_name}, focusing on their target customers and market niche."

AUDIENCE_BUILD_PROMPT = """
I am setting up an advertising campaign for {company_name} which is described as {company_description}. When I set up my audiences, which audience segments should I exclude and which should I include? Let's focus on behavioral and demographic targeting. Describe a list of audience segments to include and exclude. Make sure to include basic obvious segments that could easily be taken for granted, as well as more nuanced and specific behavioral segments. Don't include the reasoning for why you chose the segments in your response, just the segments. Each segment should be a distinct audience that would be possible to target.
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

INCLUDED_IMPROVING_PROMPT = """Please improve the included segments to better target the intended customers. The best inclusion strategy will target a set of less specific groups whose overlap matches the target audience. Provide the updated JSON structure with the improved segments."""

EXCLUDED_IMPROVING_PROMPT = """Refine the excluded segments for optimal customer targeting. An effective exclusion strategy excludes many generic groups whose intersection represents low-conversion prospects. Return the updated JSON structure with enhanced exclusion segments."""

### Search prompts

RERANK_PROMPT = """On a scale of 0 to 10, how similar is the actual segment to the desired segment?

Desired segment: "{query}"

Actual segment: "{doc}"

Provide only a numeric score between 0 and 10, where 0 is not relevant at all and 10 is extremely relevant.
If an actual segment has a non-us location mentioned in it, give it a 0.
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

Summary:"""

### report_generation prompts

REPORT_SYSTEM_PROMPT = "You are an expert data analyst specializing in audience segmentation and marketing strategy."

REPORT_PROMPT = """
Given the following summarized audience segment data, create an executive summary:

{summary_json}

Please summarize the audience targeting strategy in our {company_name} campaign, briefly
explaining who is being included and who is being excluded from the audience.
"""


