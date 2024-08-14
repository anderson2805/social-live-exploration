import streamlit as st


st.markdown("""
# Language Model Feature Extraction Codebook

This codebook explains the features extracted by our Language Model from video comments. It's designed for non-technical analysts to understand the data without needing to know the technical details of how it was generated.

## 1. Comment Identifier (id)

**Description**: A unique identifier for each comment.

**Format**: Text string

## 2. Language Detection (lang)

**Description**: The primary language used in the comment.

**Possible Values**:
- English
- Chinese
- Malay
- Tamil
- Other: Any language not listed above

**Note**: If mixed languages are used, the majority language is selected.

## 3. Trolling Detection (troll)

**Description**: Indicates if the comment is intentionally provocative or disruptive.

**Possible Values**: 
- True: Comment is likely trolling
- False: Comment appears genuine

**Examples of trolling**:
- Deliberately misinterpreting the topic
- Using excessive sarcasm or mockery
- Presenting extreme viewpoints to provoke reactions
- Repeatedly posting irrelevant content

## 4. Sentiment Analysis (senti)

**Description**: The overall emotional tone of the comment.

**Possible Values**:
- Positive: Expresses approval, optimism, satisfaction, or support
- Negative: Expresses disapproval, pessimism, dissatisfaction, or criticism
- Neutral: Presents a balanced viewpoint, purely factual, or lacks clear emotional indicators

## 5. Toxicity Assessment (toxic)

**Description**: Indicates if the comment contains harmful or inappropriate content.

**Possible Values**:
- True: Comment contains toxic elements
- False: Comment is civil

**Examples of toxic content**:
- Personal attacks or insults
- Hate speech or discrimination
- Threats or incitement to violence
- Extremely vulgar language
- Deliberate misinformation

## 6. Singapore Governance Stance (sg)

**Description**: Stance on Singapore's governance, policies, or national issues.

**Possible Values**:
- Favor: Supports or praises Singapore's government, policies, or achievements
- Against: Criticizes or expresses dissatisfaction with Singapore's approach or situation
- Neutral: Presents balanced views or objective analysis without clear bias
- Not Applicable: Does not mention Singapore or discuss relevant issues

**Note**: Classify based on dominant tone if mixed views are present.

## 7. Military Matters Stance (mil)

**Description**: Stance on Singapore's military-related topics.

**Covers**: 
- Singapore Armed Forces (SAF)
- National Service (NS) policies
- Military technology and capabilities
- Defense spending and budget
- International military cooperation
- Ministry of Defence (MINDEF) policies

**Possible Values**:
- Favor: Supports military policies, expresses pride in SAF, or advocates for strong defense
- Against: Criticizes military approaches, questions necessity of current policies, or expresses dissatisfaction with aspects of service
- Neutral: Presents balanced views, discusses facts without clear bias, or acknowledges both positives and negatives
- Not Applicable: Military topics not addressed in the comment

**Note**: Classify personal anecdotes about military service based on their overall tone towards the institution or policies.

## 8. Race and Religion Stance (rnr)

**Description**: Stance on race and religion issues in Singapore.

**Covers**: Harmony policies, integration, discrimination, cultural practices, and religious freedom

**Possible Values**:
- Favor: Supports current policies or diversity
- Against: Criticizes approaches or highlights inequalities
- Neutral: Balanced view or factual discussion
- Not Applicable: Topic not addressed

**Note**: Classify based on overall tone if specific groups are mentioned without broader context.

## 9. Societal Impact Assessment (societal_impact)

**Description**: Assesses the comment's potential influence on significant social issues, norms, or public discourse.

**Possible Values**:
- Favor: The comment supports or advocates for a particular societal change or perspective
- Against: The comment opposes or criticizes a particular societal change or perspective
- Neutral: The comment discusses societal issues without taking a clear stance
- Not Applicable: The comment does not address societal issues

**Consider 'Favor', 'Against', or 'Neutral' if the comment**:
1. Addresses or proposes solutions to major societal issues (e.g., inequality, education, healthcare, climate change)
2. Challenges or reinforces existing social norms, cultural values, or institutional practices
3. Discusses or advocates for changes to laws, policies, or public behavior
4. Highlights or analyzes emerging social trends or phenomena
5. Offers new perspectives or insights that could shape public opinion on important matters
6. Calls for collective action or societal change

**Choose 'Not Applicable' if the comment**:
1. Focuses on personal experiences or specific topics without broader societal implications
2. Discusses trivial matters or expresses opinions unlikely to influence wider societal attitudes
3. Reiterates commonly known information without adding new insights or perspectives

**Note**: Evaluate the potential for societal impact regardless of the commenter's status or authority. Comments from any individual can have societal impact if they meet the above criteria.

## Using This Data

When analyzing this data:
1. Look for patterns across multiple comments rather than focusing on individual entries.
2. Consider the context of the video when interpreting comment stances and sentiments.
3. Be aware that the Language Model's interpretations, while generally accurate, may not be perfect in every case.
4. Use this data to gain insights into public opinion and discourse trends, not to make judgments about individual commenters.
""")