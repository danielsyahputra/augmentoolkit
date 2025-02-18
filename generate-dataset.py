import json

def convert_to_alpaca(input_file, output_file):
    alpaca_data = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue   
            try:
                conversation_json = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue

            conversations = conversation_json.get("conversations", [])
            system_prompt = "You are a helpful agent"

            for i in range(len(conversations)):
                msg = conversations[i]
                if msg.get("from") == "human":
                    human_message = msg.get("value", "")
 
                    if i + 1 < len(conversations):
                        next_msg = conversations[i + 1]
                        if next_msg.get("from") == "gpt":
                            gpt_response = next_msg.get("value", "")
                            alpaca_entry = {
                                "instruction": system_prompt,
                                "input": human_message,
                                "output": gpt_response
                            }
                            alpaca_data.append(alpaca_entry)
                        else:
                            print(f"Expected 'gpt' after 'human' but found '{next_msg.get('from')}'")
                    else:
                        print("No GPT response found for the last human message.")

 
    with open(output_file, 'w', encoding='utf-8') as f_out:
        json.dump(alpaca_data, f_out, ensure_ascii=False, indent=4)

    print(f"Conversion complete. Alpaca format data saved to '{output_file}'.")

if __name__ == "__main__":
    input_file = "original/output/plain_qa_list.jsonl" 
    output_file = "alpaca_output.json"
    convert_to_alpaca(input_file, output_file)