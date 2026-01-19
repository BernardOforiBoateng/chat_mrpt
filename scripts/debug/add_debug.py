with open('app/core/arena_manager.py', 'r') as f:
    lines = f.readlines()

# Find line 1013 and add debug after line 1014
for i, line in enumerate(lines):
    if i == 1013 and 'model_info = self.available_models.get' in line:
        # Insert debug log after getting provider
        lines.insert(i + 2, '                logger.info(f"DEBUG Arena: Model={model_name}, Provider={provider}, Info={model_info}")\n')
        break

with open('app/core/arena_manager.py', 'w') as f:
    f.writelines(lines)
