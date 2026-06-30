from openai import OpenAI
from dotenv import load_dotenv
import os
import json

response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "job_description_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "job_title": {
                    "type": "string",
                    "description": "Name of the role"
                },
                "required_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Technical of professional skills needed"
                },
                "experience_level":{
                    "type": "string",
                    "description": "Years of experience required"
                },
                "salary_range":{
                    "type": "string",
                    "description": "Minimum and maximum salary offered"
                }
            },
            "required": ["job_title", "required_skills", "experience_level", "salary_range"],
            "additionalProperties": False
        }
    }
}

load_dotenv()
api_key = os.getenv("Groq_API_Key")
client = OpenAI(
    api_key = api_key,
    base_url = "https://api.groq.com/openai/v1"
)
model = "openai/gpt-oss-120b"

def validate_job_posting_response(raw_response):
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON {str(e)}"
    
    required_keys = ["job_title", "required_skills", "experience_level", "salary_range"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        return None, f"Missing required fields {missing}"
    
    if not isinstance(data["job_title"], str):
        return None, f"'job_title' must be string , got {type(data["job_title"]).__name__}"
    
    if not isinstance(data["required_skills"], list):
        return None, f"'required_skills' must be array, got {type(data["required_skills"]).__name__}"
    if not all(isinstance(skill, str) for skill in data["required_skills"]):
        return None, f"'required_skills' must be array of strings"
    
    if not isinstance(data["experience_level"], str):
        return None, f"'experience_level' must be string, got {type(data["experience_level"]).__name__}"
    
    if not isinstance(data["salary_range"], str):
        return None, f"'salary_range' must be string, got {type(data["salary_range"]).__name__}"
    
    return data, None

def run_agent(job_description: str, max_attempts: int = 3):
    validated_response = None
    messages=[
        {
            "role": "system",
            "content": "You are a job posting parser. Extract structured information from the job posting text provided by the user."
        },
        {
            "role": "user",
            "content": job_description
        }
    ]
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=response_format,
            temperature=0.3
        )
        raw_response=response.choices[0].message.content

        parsed, error = validate_job_posting_response(raw_response)
        if parsed is not None:
            return parsed
        messages.append({"role": "assistant", "content": raw_response})
        messages.append({"role": "user", "content": f"Validation failed: {error}. Resend a corrected JSON object"})
    raise RuntimeError(f"Failed to get valid JSON after {max_attempts} attempts")

if __name__ == "__main__":

    print("================Job Posting Parser================")
    print("Type 'exit' to quit\n")
    while True:
        jd = input("You: ")
        if jd.lower()=="exit":
            print("Agent: Goodbye!")
            break
        if not jd.strip():
            continue
        try:
            result = run_agent(jd)
        except RuntimeError as e:
            print(f"Agent: {e}")
            continue
        print(f"Agent: {json.dumps(result, indent=2)}")
        print("\n\n")