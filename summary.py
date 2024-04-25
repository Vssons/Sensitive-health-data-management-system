import fitz  # PyMuPDF
from transformers import pipeline, BartTokenizer, BartForConditionalGeneration
from io import BytesIO
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(stream=pdf_path, filetype="pdf") as pdf_document:
        for page_number in range(pdf_document.page_count):
            page = pdf_document[page_number]
            text += page.get_text()
    return text
def generate_summary(text):
    # Load pre-trained BART model and tokenizer
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    inputs = tokenizer(text, return_tensors="pt", truncation=True)

    summary_ids = model.generate(inputs["input_ids"], max_length=100, num_beams=4, length_penalty=2.0,
                                 early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary
def main1(file1):
    pdf_path = BytesIO(file1.read())
    # pdf_path = file1
    print("pdf_path", pdf_path)
    extracted_text = extract_text_from_pdf(pdf_path)
    # print("Original Text:")
    # print(extracted_text)

    summary = generate_summary(extracted_text)

    print("\nGenerated Summary:")
    print(summary)
    return summary


if __name__ == "__main__":
    main()

