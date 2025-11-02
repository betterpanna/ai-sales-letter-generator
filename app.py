import streamlit as st
import google.generativeai as genai
import yaml
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SalesLetterGenerator:
    def __init__(self):
        self.load_configs()
        self.setup_gemini()
        
    def load_configs(self):
        """Load all configuration files"""
        with open('config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)
        
        with open('prohibited_words.yaml', 'r') as file:
            self.prohibited_config = yaml.safe_load(file)
        
        with open('knowledge_base.yaml', 'r') as file:
            self.knowledge_base = yaml.safe_load(file)
    
    def setup_gemini(self):
        """Configure Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.error("❌ Gemini API key not found. Please set GEMINI_API_KEY in .env file")
            st.stop()
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def detect_prohibited_words(self, text):
        """Detect and replace prohibited words"""
        detected_words = []
        clean_text = text
        
        for word in self.prohibited_config['prohibited_words']:
            if word.lower() in text.lower():
                detected_words.append(word)
                replacement = self.prohibited_config['replacements'].get(word, word)
                clean_text = clean_text.replace(word, replacement)
                clean_text = clean_text.replace(word.capitalize(), replacement.capitalize())
        
        return clean_text, detected_words
    
    def search_knowledge(self, tags=None, query=None):
        """Search knowledge base by tags or query"""
        results = []
        
        for item in self.knowledge_base['knowledge_items']:
            if tags:
                if any(tag in item['tags'] for tag in tags):
                    results.append(item)
            elif query and query.lower() in item['title'].lower() or query.lower() in item['content'].lower():
                results.append(item)
        
        return results
    
    def generate_sales_letter(self, product_details, audience_details, customization, selected_knowledge):
        """Generate sales letter using Gemini API"""
        
        # Build knowledge context
        knowledge_context = ""
        if selected_knowledge:
            knowledge_context = "RELEVANT COPYWRITING KNOWLEDGE:\n"
            for knowledge_id in selected_knowledge:
                knowledge_item = next((item for item in self.knowledge_base['knowledge_items'] if item['id'] == knowledge_id), None)
                if knowledge_item:
                    knowledge_context += f"\n{knowledge_item['title']}:\n{knowledge_item['content']}\n"
        
        prompt = f"""
        Generate a high-converting sales letter with the following specifications:
        
        PRODUCT DETAILS:
        - Name: {product_details['name']}
        - Type: {product_details['type']}
        - Key Features: {product_details['features']}
        - Unique Value Proposition: {product_details['uvp']}
        
        TARGET AUDIENCE:
        - Primary Audience: {audience_details['primary']}
        - Pain Points: {audience_details['pain_points']}
        - Desired Outcomes: {audience_details['desired_outcomes']}
        
        CUSTOMIZATION:
        - Tone: {customization['tone']}
        - Length: {customization['length']}
        - Key Emphasis: {customization['emphasis']}
        
        {knowledge_context}
        
        REQUIREMENTS:
        1. Structure the letter with clear sections
        2. Use persuasive copywriting techniques
        3. Include emotional triggers
        4. Create a compelling narrative
        5. End with strong call-to-action
        6. Format in Markdown with clear headings
        
        IMPORTANT: Avoid using any marketing hype or exaggerated claims. Focus on genuine value and benefits.
        
        Generate the sales letter:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Generation failed: {str(e)}")

def main():
    # Initialize generator
    generator = SalesLetterGenerator()
    
    # Page configuration
    st.set_page_config(
        page_title=generator.config['app']['name'],
        page_icon="📝",
        layout="wide"
    )
    
    # Header
    st.title(f"🤖 {generator.config['app']['name']}")
    st.markdown(generator.config['app']['description'])
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'generated_letter' not in st.session_state:
        st.session_state.generated_letter = None
    if 'generation_time' not in st.session_state:
        st.session_state.generation_time = None
    
    # Progress bar
    steps = generator.config['ui']['steps']
    progress = st.session_state.current_step / len(steps)
    st.progress(progress)
    
    # Step navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.session_state.current_step > 0:
            if st.button("◀ Previous"):
                st.session_state.current_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.current_step < len(steps) - 1:
            if st.button("Next ▶"):
                st.session_state.current_step += 1
                st.rerun()
    
    # Step 1: Product Details
    if st.session_state.current_step == 0:
        st.header(f"Step 1: {steps[0]}")
        
        with st.form("product_details"):
            product_name = st.text_input("Product/Service Name*", 
                                       value=st.session_state.form_data.get('product_name', ''))
            
            product_type = st.selectbox("Product Type*",
                                      ["Digital Product", "Physical Product", "Service", "Software", "Course", "Other"],
                                      index=0)
            
            key_features = st.text_area("Key Features & Benefits*",
                                      placeholder="List the main features and benefits, one per line",
                                      value=st.session_state.form_data.get('key_features', ''))
            
            uvp = st.text_area("Unique Value Proposition*",
                             placeholder="What makes your product unique? Why should customers choose you?",
                             value=st.session_state.form_data.get('uvp', ''))
            
            if st.form_submit_button("Save & Continue"):
                if all([product_name, key_features, uvp]):
                    st.session_state.form_data.update({
                        'product_name': product_name,
                        'product_type': product_type,
                        'key_features': key_features,
                        'uvp': uvp
                    })
                    st.session_state.current_step = 1
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (*)")
    
    # Step 2: Target Audience
    elif st.session_state.current_step == 1:
        st.header(f"Step 2: {steps[1]}")
        
        with st.form("audience_details"):
            primary_audience = st.text_input("Primary Target Audience*",
                                           placeholder="e.g., Busy professionals, Small business owners, Parents",
                                           value=st.session_state.form_data.get('primary_audience', ''))
            
            pain_points = st.text_area("Customer Pain Points*",
                                     placeholder="What problems does your target audience face? What frustrations do they have?",
                                     value=st.session_state.form_data.get('pain_points', ''))
            
            desired_outcomes = st.text_area("Desired Outcomes*",
                                          placeholder="What results do they want to achieve? What are their goals?",
                                          value=st.session_state.form_data.get('desired_outcomes', ''))
            
            # Knowledge base search
            st.subheader("📚 Copywriting Knowledge")
            st.markdown("Select relevant copywriting frameworks to guide the generation:")
            
            available_tags = list(set(tag for item in generator.knowledge_base['knowledge_items'] for tag in item['tags']))
            selected_tags = st.multiselect("Search by tags:", available_tags)
            
            knowledge_results = generator.search_knowledge(tags=selected_tags)
            
            selected_knowledge = []
            for item in knowledge_results:
                if st.checkbox(f"{item['id']}: {item['title']}", key=item['id']):
                    selected_knowledge.append(item['id'])
                    with st.expander("View Details"):
                        st.markdown(item['content'])
            
            if st.form_submit_button("Save & Continue"):
                if all([primary_audience, pain_points, desired_outcomes]):
                    st.session_state.form_data.update({
                        'primary_audience': primary_audience,
                        'pain_points': pain_points,
                        'desired_outcomes': desired_outcomes,
                        'selected_knowledge': selected_knowledge
                    })
                    st.session_state.current_step = 2
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (*)")
    
    # Step 3: Customization & Generation
    elif st.session_state.current_step == 2:
        st.header(f"Step 3: {steps[2]}")
        
        with st.form("customization"):
            col1, col2 = st.columns(2)
            
            with col1:
                tone = st.selectbox("Tone of Voice*",
                                  generator.config['generation']['available_tones'],
                                  index=0)
                
                length = st.selectbox("Desired Length*",
                                   ["Short (200-300 words)", "Medium (400-500 words)", "Long (600-800 words)"])
            
            with col2:
                key_emphasis = st.selectbox("Key Emphasis*",
                                          ["Problem-Solution", "Benefits-Focused", "Social Proof", "Urgency", "Transformation"])
            
            st.session_state.form_data.update({
                'tone': tone,
                'length': length,
                'emphasis': key_emphasis
            })
            
            # Review section
            st.subheader("📋 Review Your Input")
            st.json({k: v for k, v in st.session_state.form_data.items() if k != 'selected_knowledge'})
            
            if st.session_state.form_data.get('selected_knowledge'):
                st.markdown("**Selected Knowledge IDs:**")
                st.code(", ".join(st.session_state.form_data['selected_knowledge']))
            
            if st.form_submit_button("🚀 Generate Sales Letter"):
                with st.spinner(f"Generating sales letter (max {generator.config['app']['max_generation_time']} seconds)..."):
                    start_time = time.time()
                    
                    try:
                        # Prepare data for generation
                        product_details = {
                            'name': st.session_state.form_data['product_name'],
                            'type': st.session_state.form_data['product_type'],
                            'features': st.session_state.form_data['key_features'],
                            'uvp': st.session_state.form_data['uvp']
                        }
                        
                        audience_details = {
                            'primary': st.session_state.form_data['primary_audience'],
                            'pain_points': st.session_state.form_data['pain_points'],
                            'desired_outcomes': st.session_state.form_data['desired_outcomes']
                        }
                        
                        customization = {
                            'tone': st.session_state.form_data['tone'],
                            'length': st.session_state.form_data['length'],
                            'emphasis': st.session_state.form_data['emphasis']
                        }
                        
                        selected_knowledge = st.session_state.form_data.get('selected_knowledge', [])
                        
                        # Generate sales letter
                        sales_letter = generator.generate_sales_letter(
                            product_details, audience_details, customization, selected_knowledge
                        )
                        
                        # Detect and replace prohibited words
                        clean_letter, detected_words = generator.detect_prohibited_words(sales_letter)
                        
                        end_time = time.time()
                        generation_time = end_time - start_time
                        
                        # Store results
                        st.session_state.generated_letter = clean_letter
                        st.session_state.generation_time = generation_time
                        st.session_state.detected_words = detected_words
                        st.session_state.selected_knowledge = selected_knowledge
                        
                    except Exception as e:
                        st.error(f"Generation failed: {str(e)}")
    
    # Display Results
    if st.session_state.generated_letter:
        st.header("🎉 Your Generated Sales Letter")
        
        # Generation metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Generation Time", f"{st.session_state.generation_time:.2f}s")
        
        with col2:
            status = "✅ Success" if st.session_state.generation_time <= generator.config['app']['max_generation_time'] else "⚠️ Slow"
            st.metric("Status", status)
        
        with col3:
            st.metric("Prohibited Words", f"{len(st.session_state.detected_words)} found")
        
        # Reference knowledge
        if st.session_state.selected_knowledge:
            st.info(f"**Reference Knowledge IDs:** {', '.join(st.session_state.selected_knowledge)}")
        
        # Prohibited words report
        if st.session_state.detected_words:
            st.warning(f"**Auto-replaced words:** {', '.join(st.session_state.detected_words)}")
        else:
            st.success("✅ No prohibited words detected!")
        
        # Sales letter display
        st.markdown("### Final Sales Letter")
        st.markdown(st.session_state.generated_letter)
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sales_letter_{timestamp}.md"
            
            st.download_button(
                label="📥 Download as Markdown",
                data=st.session_state.generated_letter,
                file_name=filename,
                mime="text/markdown"
            )
        
        with col2:
            st.download_button(
                label="📥 Download as Text",
                data=st.session_state.generated_letter,
                file_name=filename.replace('.md', '.txt'),
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
