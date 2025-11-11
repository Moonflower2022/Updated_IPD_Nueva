# NOTE: ITS REALLY IMPORTANT THAT THESE CODE SNIPPETS ARE RUN ON THE SAME VERSION OF PYTHON

import marshal
import base64
import types

def encode_function(filepath):
    with open(filepath, 'r') as f:
        code = f.read()

    compiled = compile(code, filepath, 'exec')
    marshaled = marshal.dumps(compiled)
    encoded = base64.b64encode(marshaled).decode('ascii')

    return encoded

def encode_function_obj(func):
    marshaled = marshal.dumps(func.__code__)
    encoded = base64.b64encode(marshaled).decode('ascii')
    return encoded

def decode_and_load(encoded_string, strategy_name):
    decoded = base64.b64decode(encoded_string.encode('ascii'))
    code_obj = marshal.loads(decoded)
    func = types.FunctionType(code_obj, globals(), strategy_name)
    return func

# Generate encoded versions
harrison_encoded = encode_function('harrison.py')
jackson_encoded = encode_function('jackson.py')

print("# Paste this into the notebook cell:")
print()
print("# Obfuscated strategies")
print(f"_harrison_encoded = '{harrison_encoded}'")
print()
print(f"_jackson_encoded = '{jackson_encoded}'")
