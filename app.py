from flask import Flask, request, send_file
from google.cloud import translate_v2 as translate
import polib
import io
import chardet  # Import chardet
# git test
app = Flask(__name__)
translate_client = translate.Client()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['po_file']
        if file:
            raw_data = file.stream.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['encoding'] is not None else 'utf-8'  # Default to utf-8 if chardet returns None
            po = polib.pofile(raw_data.decode(encoding))  # Use detected or default encoding
            for entry in po.untranslated_entries():
                result = translate_client.translate(entry.msgid, target_language='es')
                entry.msgstr = result['translatedText']
            buffer = io.BytesIO()
            buffer.write(str(po).encode('utf-8'))
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name='translated.po',
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
            margin: 20px 100px; /* Adjust margin as needed */
            padding: 0; 
        }
        h1 { 
            color: #0d6efd; /* Bootstrap primary blue for a bit of contrast */
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
            padding: 10px 20px; /* Larger padding */
            margin-top: 10px; 
            cursor: pointer; 
            font-size: 16px; /* Larger font size */
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
