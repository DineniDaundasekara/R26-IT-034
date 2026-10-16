import json
import requests


API_URL = "http://127.0.0.1:5000/predict"

sample_payload = {
    "role": "Quality Assurance / Testing",
    "years_experience": "3-5 years",
    "tech_stack_change": 2,
    "weekly_learning_time": "1-3 hours",
    "stability_indicators": "None of Above",
    "ai_replaceability": 4,
    "domain_stability": 2,
    "job_market_trend": "Slight decrease",
    "switch_confidence": 2,
    "career_strategy": "No clear strategy",
    "skill_update_frequency": "Occasionally",
}


def main():
    try:
        response = requests.post(API_URL, json=sample_payload, timeout=15)
        print("=== API Test Result ===")
        print(f"URL: {API_URL}")
        print(f"Status Code: {response.status_code}")
        print("\nRequest Payload:")
        print(json.dumps(sample_payload, indent=2))
        print("\nResponse Body:")

        try:
            print(json.dumps(response.json(), indent=2))
        except ValueError:
            print(response.text)
    except requests.exceptions.RequestException as exc:
        print("Request failed:")
        print(str(exc))


if __name__ == "__main__":
    main()
