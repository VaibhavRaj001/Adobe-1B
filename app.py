import os
import json
import fitz
import re
from datetime import datetime
from collections import defaultdict
import math

class PersonaDrivenAnalyzer:
    def __init__(self):
        self.keyword_weights = {
            # Academic/Research keywords
            'research': ['methodology', 'experiment', 'analysis', 'results', 'conclusion', 'literature', 'study', 'findings', 'data', 'statistical', 'hypothesis', 'validation', 'benchmarks', 'performance', 'evaluation', 'metrics'],
            
            # Business/Financial keywords
            'business': ['revenue', 'profit', 'investment', 'market', 'strategy', 'growth', 'financial', 'roi', 'competitive', 'analysis', 'trends', 'positioning', 'r&d', 'operations', 'management'],
            
            # Educational keywords
            'education': ['concept', 'theory', 'principle', 'definition', 'example', 'mechanism', 'process', 'formula', 'reaction', 'kinetics', 'properties', 'structure', 'function', 'application'],
            
            # Technical keywords
            'technical': ['algorithm', 'model', 'system', 'framework', 'architecture', 'implementation', 'optimization', 'parameters', 'configuration', 'performance', 'scalability']
        }
    
    def identify_persona_type(self, persona):
        """Identify the general category of persona"""
        persona_lower = persona.lower()
        
        if any(word in persona_lower for word in ['researcher', 'phd', 'scientist', 'academic']):
            return 'research'
        elif any(word in persona_lower for word in ['analyst', 'investment', 'business', 'financial']):
            return 'business'
        elif any(word in persona_lower for word in ['student', 'undergraduate', 'learner']):
            return 'education'
        else:
            return 'technical'
    
    def extract_keywords_from_job(self, job_description):
        """Extract important keywords from job description"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', job_description.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Extract quoted phrases as high-priority keywords
        quoted_phrases = re.findall(r'"([^"]*)"', job_description.lower())
        for phrase in quoted_phrases:
            keywords.extend(phrase.split())
        
        return list(set(keywords))
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text with page information from PDF"""
        doc = fitz.open(pdf_path)
        pages_content = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages_content[page_num + 1] = text
        
        doc.close()
        return pages_content
    
    def identify_sections(self, text_content, outline_data=None):
        """Identify sections in the document"""
        sections = []
        
        # If we have outline data from Round 1A, use it
        if outline_data and 'outline' in outline_data:
            for heading in outline_data['outline']:
                sections.append({
                    'title': heading['text'],
                    'page': heading['page'],
                    'level': heading['level'],
                    'content': ''
                })
        
        # Fallback: identify sections using common patterns
        if not sections:
            for page_num, content in text_content.items():
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    # Look for potential section headers
                    if (len(line) > 0 and len(line) < 100 and 
                        (line.isupper() or line.istitle()) and
                        not line.endswith('.') and
                        len(line.split()) <= 10):
                        sections.append({
                            'title': line,
                            'page': page_num,
                            'level': 'H1',  # Default level
                            'content': ''
                        })
        
        return sections
    
    def calculate_relevance_score(self, text, persona_type, job_keywords):
        """Calculate relevance score for a text section"""
        text_lower = text.lower()
        score = 0
        
        # Score based on persona-specific keywords
        persona_keywords = self.keyword_weights.get(persona_type, [])
        for keyword in persona_keywords:
            count = text_lower.count(keyword)
            score += count * 2
        
        # Score based on job-specific keywords
        for keyword in job_keywords:
            count = text_lower.count(keyword)
            score += count * 3  # Higher weight for job-specific terms
        
        # Bonus for longer, more substantial content
        word_count = len(text.split())
        if word_count > 50:
            score += math.log(word_count) * 0.5
        
        return score
    
    def extract_subsections(self, content, max_subsections=5):
        """Extract relevant subsections from content"""
        paragraphs = content.split('\n\n')
        subsections = []
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 100:  # Only consider substantial paragraphs
                # Take first 200 characters as refined text
                refined_text = para[:200] + "..." if len(para) > 200 else para
                subsections.append(refined_text)
        
        return subsections[:max_subsections]
    
    def process_documents(self, input_data):
        """Main processing function"""
        documents = input_data['documents']
        persona = input_data['persona']
        job_to_be_done = input_data['job_to_be_done']
        
        persona_type = self.identify_persona_type(persona)
        job_keywords = self.extract_keywords_from_job(job_to_be_done)
        
        all_sections = []
        
        # Process each document
        for doc_path in documents:
            if not os.path.exists(doc_path):
                continue
                
            doc_name = os.path.basename(doc_path)
            text_content = self.extract_text_from_pdf(doc_path)
            
            # Try to load outline from Round 1A if available
            outline_data = None
            json_path = doc_path.replace('.pdf', '.json')
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        outline_data = json.load(f)
                except:
                    pass
            
            sections = self.identify_sections(text_content, outline_data)
            
            # Calculate relevance for each section
            for section in sections:
                page_num = section['page']
                if page_num in text_content:
                    # Get content around the section
                    page_content = text_content[page_num]
                    section_start = page_content.find(section['title'])
                    
                    if section_start != -1:
                        # Extract content after the section title
                        section_content = page_content[section_start:section_start + 1000]
                    else:
                        section_content = page_content[:1000]  # Fallback
                    
                    relevance_score = self.calculate_relevance_score(
                        section_content, persona_type, job_keywords
                    )
                    
                    if relevance_score > 0:  # Only include relevant sections
                        all_sections.append({
                            'document': doc_name,
                            'page_number': page_num,
                            'section_title': section['title'],
                            'relevance_score': relevance_score,
                            'content': section_content
                        })
        
        # Sort by relevance and assign importance ranks
        all_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Prepare output format to match expected structure
        extracted_sections = []
        subsection_analysis = []
        
        for rank, section in enumerate(all_sections[:10], 1):  # Top 10 sections
            extracted_sections.append({
                'document': section['document'],
                'section_title': section['section_title'],
                'importance_rank': rank,
                'page_number': section['page_number']
            })
            
            # Extract subsections
            subsections = self.extract_subsections(section['content'])
            for subsection_text in subsections:
                subsection_analysis.append({
                    'document': section['document'],
                    'refined_text': subsection_text,
                    'page_number': section['page_number']
                })
        
        # Extract just filenames for metadata (remove path)
        input_document_names = [os.path.basename(doc) for doc in documents if os.path.exists(doc)]
        
        return {
            'metadata': {
                'input_documents': input_document_names,
                'persona': persona,
                'job_to_be_done': job_to_be_done,
                'processing_timestamp': datetime.now().isoformat()
            },
            'extracted_sections': extracted_sections,
            'subsection_analysis': subsection_analysis
        }

def load_input_config(config_path):
    """Load input configuration from JSON file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_input_format(input_data):
    """Parse the new input format and convert to internal format"""
    # Extract documents - build full paths
    documents = []
    if 'documents' in input_data:
        for doc in input_data['documents']:
            if isinstance(doc, dict) and 'filename' in doc:
                # New format: {"filename": "doc.pdf", "title": "..."}
                documents.append(f"./pdfs/1b/{doc['filename']}")
            elif isinstance(doc, str):
                # Old format: "./pdfs/doc.pdf"
                documents.append(doc)
    
    # Extract persona
    persona = ""
    if 'persona' in input_data:
        if isinstance(input_data['persona'], dict) and 'role' in input_data['persona']:
            # New format: {"role": "Food Contractor"}
            persona = input_data['persona']['role']
        elif isinstance(input_data['persona'], str):
            # Old format: "Food Contractor"
            persona = input_data['persona']
    
    # Extract job to be done
    job_to_be_done = ""
    if 'job_to_be_done' in input_data:
        if isinstance(input_data['job_to_be_done'], dict) and 'task' in input_data['job_to_be_done']:
            # New format: {"task": "Prepare a vegetarian..."}
            job_to_be_done = input_data['job_to_be_done']['task']
        elif isinstance(input_data['job_to_be_done'], str):
            # Old format: "Prepare a vegetarian..."
            job_to_be_done = input_data['job_to_be_done']
    
    return {
        'documents': documents,
        'persona': persona,
        'job_to_be_done': job_to_be_done
    }

def main():
    # Check if input configuration exists
    config_path = './input_1b.json'
    
    if not os.path.exists(config_path):
        # Create a sample input configuration in the new format
        sample_config = {
            "challenge_info": {
                "challenge_id": "round_1b_001",
                "test_case_name": "sample_test",
                "description": "Sample test case"
            },
            "documents": [
                {
                    "filename": "sample1.pdf",
                    "title": "Sample Document 1"
                },
                {
                    "filename": "sample2.pdf", 
                    "title": "Sample Document 2"
                }
            ],
            "persona": {
                "role": "PhD Researcher in Computational Biology"
            },
            "job_to_be_done": {
                "task": "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Created sample input configuration at {config_path}")
        print("Please update it with your actual documents, persona, and job description.")
        return
    
    # Load configuration
    raw_input_data = load_input_config(config_path)
    
    # Parse the input format
    input_data = parse_input_format(raw_input_data)
    
    # Initialize analyzer
    analyzer = PersonaDrivenAnalyzer()
    
    # Process documents
    try:
        result = analyzer.process_documents(input_data)
        
        # Save output
        output_path = './outputs/challenge1b_output.json'
        os.makedirs('./outputs', exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Round 1B processing completed!")
        print(f"📄 Output saved to: {output_path}")
        print(f"📊 Extracted {len(result['extracted_sections'])} relevant sections")
        print(f"🔍 Generated {len(result['subsection_analysis'])} subsection analyses")
        
    except Exception as e:
        print(f"❌ Error processing documents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()