from flask import Flask, request, send_file
from google.cloud import translate_v2 as translate
import polib
import io
import chardet
import json

app = Flask(__name__)
translate_client = translate.Client()

# Load custom translations
with open('custom_translations.json') as json_file:
    custom_translations = json.load(json_file)['replacements']

def apply_custom_translations(text, custom_translations):
    # This function can be enhanced to handle more complex scenarios
    for original, replacement in custom_translations.items():
        # Case-insensitive replacement, considering 'SOMBREROS' might appear in different cases
        text = text.replace(original.capitalize(), replacement.capitalize())
        text = text.replace(original.upper(), replacement.upper())
        text = text.replace(original.lower(), replacement.lower())
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['po_file']
        if file:
            raw_data = file.stream.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'
            po = polib.pofile(raw_data.decode(encoding))
            for entry in po.untranslated_entries():
                result = translate_client.translate(entry.msgid, target_language='es')
                translated_text = result['translatedText']
                # Apply custom translations
                translated_text = apply_custom_translations(translated_text, custom_translations)
                entry.msgstr = translated_text
            
            buffer = io.BytesIO()
            # Generate the modified PO file content directly
            buffer.write(str(po).encode('utf-8'))
            buffer.seek(0)

            original_filename = file.filename
            download_filename = "Translated-" + (original_filename[:10] + '.po' if len(original_filename) > 10 else original_filename)

            return send_file(
                buffer,
                as_attachment=True,
                download_name=download_filename,
                mimetype='application/octet-stream'
            )


    return '''<!doctype html>
<html lang="en">
<head>
    <title>Upload .po File</title>
    <style>
        body { 
            color: #fff; 
            background-color: #333; 
            font-family: Arial, sans-serif; 
            margin: 20px 100px;
            padding: 0; 
        }
        h1 { 
            color: #0d6efd;
        }
        form { 
            margin-top: 20px; 
            border: 2px solid #555; 
            padding: 10px; 
            background-color: #444; 
        }
        input[type="file"] {
            color: #fff;
        }
        input[type="submit"] { 
            background-color: #0d6efd; 
            color: white; 
            border: none; 
            padding: 10px 20px;
            margin-top: 10px; 
            cursor: pointer; 
            font-size: 16px;
        }
        input[type="submit"]:hover { 
            background-color: #0b5ed7; 
        }
    </style>
</head>
<body>
    <h1>Upload .po File for Translation</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="po_file">
      <input type="submit" value="Upload">
    </form>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)
