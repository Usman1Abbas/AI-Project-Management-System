import os
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content('Say OK in one word')

print(f'Response type: {type(response)}')
print(f'Has text attr: {hasattr(response, "text")}')
print(f'Has candidates: {hasattr(response, "candidates")}')

try:
    text = response.text
    print(f'response.text works: "{text}"')
except Exception as e:
    print(f'response.text error: {type(e).__name__}: {e}')

print(f'\nCandidates length: {len(response.candidates)}')
print(f'Candidate[0].content type: {type(response.candidates[0].content)}')
print(f'Candidate[0].content.parts length: {len(response.candidates[0].content.parts)}')

part = response.candidates[0].content.parts[0]
print(f'Part type: {type(part)}')
print(f'Part attributes: {dir(part)}')
print(f'Has text in part: {hasattr(part, "text")}')

if hasattr(part, 'text'):
    print(f'Part text: "{part.text}"')
