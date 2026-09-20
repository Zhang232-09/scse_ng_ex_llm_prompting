import json
from ollama import chat
from parse_data import load_items, get_unclaimed_items, save_result

## Import the necessary modules
## Import the function from the module parse_data
## Build your prompt based on the description the user provides
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.
def build_prompt(description, available_items):
    system_prompt = """
You are a campus lost-and-found matching assistant.
Rules:
1. Only use the provided lost-and-found item list.
2. Not all details need to match for an item to be a possible match.
3. Your output MUST ONLY be JSON, strictly following this structure:
{
    "matches": ["ITEM_ID"],
    "confidence": "LOW"
}
4. The value of confidence must be exactly one of: LOW, MEDIUM, HIGH.
5. If no possible matches found, set matches to an empty list.
6. Do not add any extra text, explanation, markdown outside the JSON output.
"""
    item_json_str = json.dumps(available_items, indent=2)
    user_prompt = f"""
Lost item description from user: {description}
Available lost and found items:
{item_json_str}

Find all possible matching item IDs. Return only JSON as required.
"""
    return system_prompt, user_prompt


## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    response = chat(
        model="qwen3:8b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.message.content


## Logic to parse the response from Qwen and return the result.
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    result = json.loads(response_text.strip())
    return result


## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    required_keys = {"matches", "confidence"}
    if not required_keys.issubset(result.keys()):
        return False
    if not isinstance(result["matches"], list):
        return False
    valid_confidence = {"LOW", "MEDIUM", "HIGH"}
    if result["confidence"] not in valid_confidence:
        return False
    valid_ids = [item["id"] for item in available_items]
    for match_id in result["matches"]:
        if match_id not in valid_ids:
            return False
    return True


## Logic to display the matches found by Qwen in a user-friendly format.
## It should look something like this:
"""
CAMPUS LOST-AND-FOUND ASSISTANT
==================================================
Describe the item you lost: I lost a black bag somewhere
Searching for possible matches...
MATCH RESULT
--------------------------------------------------
Confidence: MEDIUM
Possible matches:
ID: F101
Item: backpack
Color: black
Location: Library 2nd floor
Date found: 2026-09-15
Result saved to output/match_result.json
"""
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("==================================================")
    print(f"Describe the item you lost: {user_description}")
    print("Searching for possible matches...")
    print("MATCH RESULT")
    print("--------------------------------------------------")
    print(f"Confidence: {result['confidence']}")
    print("Possible matches:")

    match_ids = result["matches"]
    if len(match_ids) == 0:
        print("No matches found. matches = []")
        return

    item_map = {item["id"]: item for item in available_items}
    for mid in match_ids:
        item = item_map[mid]
        print(f"ID: {item['id']}")
        print(f"Item: {item['item']}")
        print(f"Color: {item['color']}")
        print(f"Location: {item['location']}")
        print(f"Date found: {item['date']}")
    print("Result saved to output/match_result.json")


## Control center for the entire program.
def main():
    global user_description
    all_items = load_items("found_items.json")
    available_items = get_unclaimed_items(all_items)

    user_description = input("Please describe your lost item: ")

    sys_prompt, usr_prompt = build_prompt(user_description, available_items)

    raw_response = ask_qwen(sys_prompt, usr_prompt)

    match_result = parse_response(raw_response)

    if not validate_result(match_result, available_items):
        raise ValueError("Invalid result returned from Qwen")

    save_result(match_result, "output/match_result.json")

    display_matches(match_result, available_items)


if __name__ == "__main__":
    main()