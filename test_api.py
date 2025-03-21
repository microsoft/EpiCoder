from call_api_local.call_api import call_gpt4

prompt="Hello"

print(call_gpt4(prompt))

# ('Hi! How can I help you today?', {'choices': [{'content_filter_results': {'hate': {'filtered': False, 'severity': 'safe'}, 'self_harm': {'filtered': False, 'severity': 'safe'}, 'sexual': {'filtered': False, 'severity': 'safe'}, 'violence': {'filtered': False, 'severity': 'safe'}}, 'finish_reason': 'stop', 'index': 0, 'message': {'content': 'Hi! How can I help you today?', 'role': 'assistant'}}], 'created': 1732859173, 'id': 'chatcmpl-AYo7R69uSo1Kcfuvt9MFSsSfhIqjR', 'model': 'gpt-4o-2024-05-13', 'prompt_filter_results': [{'content_filter_results': {'hate': {'filtered': False, 'severity': 'safe'}, 'self_harm': {'filtered': False, 'severity': 'safe'}, 'sexual': {'filtered': False, 'severity': 'safe'}, 'violence': {'filtered': False, 'severity': 'safe'}}, 'prompt_index': 0}], 'system_fingerprint': 'fp_04751d0b65', 'usage': {'completion_tokens': 9, 'prompt_tokens': 8, 'total_tokens': 17}})