content = open('src/decision_engine/decision_logic.py', 'r', encoding='utf-8').read()
if 'engine = SmartWasteDecisionEngine()' not in content:
    content += '\n\nengine = SmartWasteDecisionEngine()\n'
    open('src/decision_engine/decision_logic.py', 'w', encoding='utf-8').write(content)
    print('Fixed - engine singleton added')
else:
    print('Already OK - engine singleton exists')