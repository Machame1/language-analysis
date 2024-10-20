import os
import re
from flask import Flask, render_template, request, redirect, url_for
import PyPDF2
import docx
from textblob import TextBlob
import nltk
from googletrans import Translator
from pptx import Presentation

# Download NLTK data files
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
translator = Translator()

# Function to read text from different file formats
def read_text_from_pdf(file_path):
    text = ''
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ''  # Handle None case
    return text

def read_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

def read_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def read_text_from_pptx(file_path):
    text = ''
    presentation = Presentation(file_path)
    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_text = f"Slide {slide_number}:\n"
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                slide_text += shape.text + "\n"
        text += slide_text + "\n"
    return text

# Function to remove noise from text
def remove_noise(text):
    return re.sub(r'[^\w\s]', '', text.lower())

# Function to calculate overall sentiment
def overall_sentiment(text):
    cleaned_text = remove_noise(text)
    analysis = TextBlob(cleaned_text)
    polarity = analysis.sentiment.polarity
    
    # Classify based on overall polarity
    if polarity > 0:
        sentiment_label = 'Positive'
    elif polarity < 0:
        sentiment_label = 'Negative'
    else:
        sentiment_label = 'Neutral'
    
    return sentiment_label

# Function to classify the document into relevant categories
def classify_document(text):
    categories = {
        'health': ['health', 'doctor', 'hospital', 'disease', 'medicine'],
        'crime': ['crime', 'police', 'robbery', 'assault', 'murder'],
        'finance': ['bank', 'finance', 'loan', 'investment', 'stock'],
        'legal': ['court', 'law', 'judge', 'legal', 'contract'],
        'education': ['school', 'university', 'education', 'teacher', 'student'],
        # Add more categories as needed
    }

    for category, keywords in categories.items():
        if any(keyword in text.lower() for keyword in keywords):
            return category

    return None  # If no category matched, the document is irrelevant

# Function to summarize text into 10 lines
def summarize_text_to_10_lines(text):
    sentences = nltk.sent_tokenize(text)
    document_category = classify_document(text)
    if document_category:
        summary = f"The document is related to {document_category}.\n"
    else:
        summary = "The document does not belong to a recognized category.\n"
    
    summary += " ".join(sentences[:10])  # Limit to first 10 sentences
    
    return summary

# Routes
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
    elif filename.endswith('.pptx'):
        text = read_text_from_pptx(file_path)
    else:
        return "Unsupported file format"
    
    return redirect(url_for('upload_success', filename=filename))

@app.route('/upload_success/<filename>')
def upload_success(filename):
    return render_template('success.html', filename=filename)

@app.route('/analyze/<filename>')
def analyze_sentiment_route(filename):
    file_path = os.path.join('uploads', filename)
    text = read_text_from_pdf(file_path) if filename.endswith('.pdf') else read_text_from_docx(file_path) if filename.endswith('.docx') else read_text_from_txt(file_path) if filename.endswith('.txt') else read_text_from_pptx(file_path)

    document_category = classify_document(text)
    if not document_category:
        return "Access Denied: Document not related to any relevant categories (e.g., health, crime, finance, legal, education)."

    sentiment_label = overall_sentiment(text)

    return render_template('result.html', results=[("Overall Sentiment", sentiment_label)], filename=filename)

@app.route('/remove_noise/<filename>')
def remove_noise_route(filename):
    file_path = os.path.join('uploads', filename)
    text = read_text_from_pdf(file_path) if filename.endswith('.pdf') else read_text_from_docx(file_path) if filename.endswith('.docx') else read_text_from_txt(file_path) if filename.endswith('.txt') else read_text_from_pptx(file_path)

    cleaned_text = remove_noise(text)
    sentiment_label = overall_sentiment(cleaned_text)
    return render_template('result.html', results=[("Cleaned Text Sentiment", sentiment_label)], filename=filename)

@app.route('/summary/<filename>', methods=['GET', 'POST'])
def summarize_route(filename):
    file_path = os.path.join('uploads', filename)
    text = read_text_from_pdf(file_path) if filename.endswith('.pdf') else read_text_from_docx(file_path) if filename.endswith('.docx') else read_text_from_txt(file_path) if filename.endswith('.txt') else read_text_from_pptx(file_path)

    document_category = classify_document(text)
    if not document_category:
        return "Access Denied: Document not related to any relevant categories (e.g., health, crime, finance, legal, education)."

    summary = summarize_text_to_10_lines(text)

    if request.method == 'POST':
        target_lang = request.form['language']
        translated_summary = translator.translate(summary, dest=target_lang).text
        return render_template('result.html', results=[("Translated Summary", translated_summary)], filename=filename)

    return render_template('summary.html', summary=summary, filename=filename)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
