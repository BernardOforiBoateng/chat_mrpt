with open('app/core/arena_manager.py', 'r') as f:
    lines = f.readlines()

# Find the get_model_response function and add explicit gpt-4o handling
for i, line in enumerate(lines):
    if 'def get_model_response(model_name: str):' in line:
        # Add explicit check for gpt-4o right at the start
        insert_line = i + 2
        lines.insert(insert_line, '                # EXPLICIT CHECK FOR GPT-4O\n')
        lines.insert(insert_line + 1, '                if model_name == "gpt-4o":\n')
        lines.insert(insert_line + 2, '                    logger.info("FORCING gpt-4o to use OpenAI provider")\n')
        lines.insert(insert_line + 3, '                    provider = "openai"\n')
        lines.insert(insert_line + 4, '                else:\n')
        lines.insert(insert_line + 5, '                    model_info = self.available_models.get(model_name, {})\n')
        lines.insert(insert_line + 6, '                    provider = model_info.get("type", "ollama")\n')
        
        # Remove the original lines that get model_info
        for j in range(i + 10, i + 20):
            if 'model_info = self.available_models.get' in lines[j]:
                lines[j] = ''
            if 'provider = model_info.get' in lines[j]:
                lines[j] = ''
        break

with open('app/core/arena_manager.py', 'w') as f:
    f.writelines(lines)
