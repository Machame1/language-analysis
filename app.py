import os
import re
from flask import Flask, render_template, request, redirect, url_for
import PyPDF2
import docx
from textblob import TextBlob
import nltk
from googletrans import Translator

# Download NLTK data files
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
translator = Translator()

def read_text_from_pdf(file_path):
    text = ''
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def read_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

def read_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def remove_noise(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def analyze_sentiment(text):
    sentences = nltk.sent_tokenize(text)
    results = []
    for sentence in sentences:
        cleaned_sentence = remove_noise(sentence)
        analysis = TextBlob(cleaned_sentence)
        results.append((sentence, analysis.sentiment.polarity))
    return results

def summarize_text(text):
    sentences = nltk.sent_tokenize(text)
    summary = " ".join(sentences[:2])  # Basic summary (first 2 sentences)
    return summary

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        return redirect(url_for('process_file', filename=file.filename))

@app.route('/process/<filename>')
def process_file(filename):
    file_path = os.path.join('uploads', filename)
    
    if filename.endswith('.pdf'):
        text = read_text_from_pdf(file_path)
    elif filename.endswith('.docx'):
        text = read_text_from_docx(file_path)
    elif filename.endswith('.txt'):
        text = read_text_from_txt(file_path)
    else:
        return "Unsupported file format"

    return render_template('process.html', text=text, filename=filename)

@app.route('/analyze/<filename>')
def analyze_sentiment_route(filename):
    file_path = os.path.join('uploads', filename)
    text = read_text_from_pdf(file_path) if filename.endswith('.pdf') else read_text_from_docx(file_path) if filename.endswith('.docx') else read_text_from_txt(file_path)

    results = analyze_sentiment(text)
    return render_template('result.html', results=results, filename=filename)

@app.route('/remove_noise/<filename>')
def remove_noise_route(filename):
    file_path = os.path.join('uploads', filename)
    text = read_text_from_pdf(file_path) if filename.endswith('.pdf') else read_text_from_docx(file_path) if filename.endswith('.docx') else read_text_from_txt(file_path)

    cleaned_text = remove_noise(text)
    return render_template('result.html', results=[("Cleaned Text", cleaned_text)], filename=filename)

@app.route('/summary/<filename>', methods=['GET', 'POST'])
def summarize_route(filename):
    file_path = os.path.join('uploads', filename)
    text = read_text_from_pdf(file_path) if filename.endswith('.pdf') else read_text_from_docx(file_path) if filename.endswith('.docx') else read_text_from_txt(file_path)

    summary = summarize_text(text)

    if request.method == 'POST':
        target_lang = request.form['language']
        translated_summary = translator.translate(summary, dest=target_lang).text
        return render_template('result.html', results=[("Translated Summary", translated_summary)], filename=filename)

    return render_template('summary.html', summary=summary, filename=filename)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
