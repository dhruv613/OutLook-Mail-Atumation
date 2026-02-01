import os
import random
import docx

class ContentManager:
    def __init__(self, base_dir):
        # base_dir should be 'c:/Users/ASUS/Desktop/Mail_AutoMation'
        self.data_dir = os.path.join(base_dir, "data")
        self.subjects_file = os.path.join(self.data_dir, "sub bingo.txt")
        self.templates_dir = os.path.join(self.data_dir, "word_templates")
        
        self.subjects = []
        self.templates = []
        
        self._load_subjects()
        self._load_templates()

    def _load_subjects(self):
        """Read subjects from sub bingo.txt"""
        if os.path.exists(self.subjects_file):
            try:
                with open(self.subjects_file, 'r', encoding='utf-8') as f:
                    # Filter empty lines
                    self.subjects = [line.strip() for line in f.readlines() if line.strip()]
                # print(f"📖 Loaded {len(self.subjects)} subjects.")
            except Exception as e:
                print(f"⚠️ Error reading subjects: {e}")
        else:
            print(f"⚠️ Subjects file not found: {self.subjects_file}")

    def _load_templates(self):
        """Read .docx bodies from word_templates folder"""
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith(".docx") and not file.startswith("~$"):
                    path = os.path.join(self.templates_dir, file)
                    try:
                        doc = docx.Document(path)
                        full_text = []
                        for para in doc.paragraphs:
                            full_text.append(para.text)
                        
                        body_content = "\n".join(full_text)
                        if body_content.strip():
                           self.templates.append(body_content)
                    except Exception as e:
                        print(f"⚠️ Error reading template {file}: {e}")
            # print(f"📖 Loaded {len(self.templates)} message templates.")
        else:
            print(f"⚠️ Templates dir not found: {self.templates_dir}")

    def get_random_subject(self):
        if self.subjects:
            return random.choice(self.subjects)
        return "Invoice Update" # Fallback

    def get_random_body(self):
        if self.templates:
            return random.choice(self.templates)
        return "Please find attached the invoice." # Fallback
