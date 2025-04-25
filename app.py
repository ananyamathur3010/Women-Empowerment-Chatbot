import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.tools import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import time
import random
import os
from datetime import datetime
import html

# Load environment variables
load_dotenv()

# Set page config to dark theme
st.set_page_config(
    page_title="Women's Empowerment Chat",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Apply dark theme with minimal CSS
st.markdown("""
<style>
/* Force dark theme */
body {
    background-color: #0E1117 !important;
    color: white !important;
}

.stApp {
    background-color: #0E1117 !important;
}

/* Messages styling */
.user-message {
    background-color: #E91E63;
    color: white;
    padding: 10px 15px;
    border-radius: 15px 15px 0 15px;
    margin: 5px 0;
    display: inline-block;
    max-width: 80%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.bot-message {
    background-color: #333333;
    color: white;
    padding: 10px 15px;
    border-radius: 15px 15px 15px 0;
    margin: 5px 0;
    display: inline-block;
    max-width: 80%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.timestamp {
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 5px;
}

/* Chat container */
.chat-area {
    background-color: #1E1E1E;
    border-radius: 10px;
    padding: 20px;
    height: 500px;
    overflow-y: auto;
    margin-bottom: 20px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #9C27B0;
    background-image: linear-gradient(135deg, #9C27B0 0%, #E91E63 100%);
}

/* Send button styling */
button[data-testid="baseButton-secondary"] {
    background-color: #E91E63 !important;
    color: white !important;
}

/* Prevent white backgrounds */
div.block-container {
    background-color: transparent !important;
}

[data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi there! I'm your women's empowerment chatbot. What would you like to chat about today?", "timestamp": get_timestamp()}
        ]
    if "llm" not in st.session_state:
        st.session_state.llm = None
    if "search" not in st.session_state:
        st.session_state.search = None
    if "regular_chain" not in st.session_state:
        st.session_state.regular_chain = None
    if "search_chain" not in st.session_state:
        st.session_state.search_chain = None
    if "thinking" not in st.session_state:
        st.session_state.thinking = False

def get_timestamp():
    """Get current timestamp for messages"""
    return datetime.now().strftime("%H:%M")

def get_api_keys():
    """Get API keys from environment variables, Streamlit secrets, or session state"""
    # Try to get keys from environment variables first
    groq_key = os.environ.get("GROQ_API_KEY")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    
    # If not in environment variables, try Streamlit secrets
    if not groq_key and hasattr(st, "secrets") and "groq_api_key" in st.secrets:
        groq_key = st.secrets["groq_api_key"]
    
    if not tavily_key and hasattr(st, "secrets") and "tavily_api_key" in st.secrets:
        tavily_key = st.secrets["tavily_api_key"]
    
    # If still not found, try session state
    if not groq_key and "groq_api_key" in st.session_state:
        groq_key = st.session_state.groq_api_key
    
    if not tavily_key and "tavily_api_key" in st.session_state:
        tavily_key = st.session_state.tavily_api_key
    
    return groq_key, tavily_key

def initialize_api_services():
    """Initialize API services with the provided keys"""
    try:
        # Get API keys
        groq_api_key = "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"
        tavily_api_key = "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"
        
        if not groq_api_key or not tavily_api_key:
            return False
        
        # Initialize LLM
        llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama3-8b-8192",
        )
        st.session_state.llm = llm
        
        # Initialize search
        search = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=3
        )
        st.session_state.search = search
        
        # Create chains
        st.session_state.regular_chain = create_regular_chain()
        st.session_state.search_chain = create_search_chain()
        
        return True
        
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        return False

# Define system prompt
system_template = """You are a friendly, casual chatbot focused on women's empowerment and feminism.

Your responses MUST be:
1. VERY SHORT - just 1-2 sentences
2. Casual and conversational like texting a friend
3. Helpful without being academic
4. Empowering and positive

DO NOT use formal language, citations, or academic tone.
DO NOT use bullet points or numbered lists.
NEVER provide long explanations or history lessons.
NO introductory phrases like "In feminism..." or "When it comes to..."

Just give a simple, direct answer as if texting a friend.
"""

def create_regular_chain():
    """Create a chain that processes regular questions without search"""
    template = """
    You are a friendly, casual chatbot focused on women's empowerment and feminism.

    Your responses MUST be:
    1. VERY SHORT - just 1-2 sentences
    2. Casual and conversational like texting a friend
    3. Helpful without being academic
    4. Empowering and positive

    User question: {question}

    Helpful answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def process_with_llm(input_dict):
        try:
            query = input_dict["question"]
            
            response = st.session_state.llm.invoke(prompt.format_messages(question=query))
            return StrOutputParser().invoke(response)
            
        except Exception as e:
            print(f"Error in regular chain: {str(e)}")
            return "Sorry, I couldn't process that. How about asking something else about women's empowerment?"
    
    return process_with_llm

def create_search_chain():
    """Create a chain that uses search to answer questions"""
    template = """
    You are a friendly, casual chatbot focused on women's empowerment and feminism.

    Your responses MUST be:
    1. VERY SHORT - just 1-2 sentences
    2. Casual and conversational like texting a friend
    3. Helpful without being academic
    4. Empowering and positive

    Here is some information that might help you answer: {search_result}

    Remember to keep your response to 1-2 sentences maximum.

    User question: {question}

    Helpful answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def process_with_search_and_llm(input_dict):
        try:
            query = input_dict["question"]
            
            # Get search results
            search_results = st.session_state.search.invoke(query)
            
            if search_results and isinstance(search_results, list) and len(search_results) > 0:
                search_content = search_results[0]["content"][:250]
            else:
                search_content = "No results found."
            
            # Format with search results
            input_with_search = {
                "question": query,
                "search_result": search_content
            }
            
            # Process through prompt and LLM
            response = st.session_state.llm.invoke(prompt.format_messages(**input_with_search))
            return StrOutputParser().invoke(response)
            
        except Exception as e:
            print(f"Error in search chain: {str(e)}")
            # Return a fallback response
            return "Sorry, I couldn't find information on that. How about asking something else about women's empowerment?"
    
    return process_with_search_and_llm

def process_input(user_input=None):
    """Process user input and add it to chat history"""
    # Get input from session state if not provided
    if user_input is None:
        user_input = st.session_state.user_input
        if not user_input:
            return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": get_timestamp()})
    
    # Clear input field
    st.session_state.user_input = ""
    
    # Set thinking state to show indicator
    st.session_state.thinking = True
    
    # Force rerun to update UI with the new message
    st.rerun()

def generate_response():
    """Generate and display response from the AI"""
    if not st.session_state.thinking:
        return
    
    try:
        # Get the last user message
        last_user_message = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
        
        if not last_user_message:
            st.session_state.thinking = False
            return
        
        # Determine if search is needed based on the question
        needs_search = any(term in last_user_message.lower() for term in 
                          ['what is', 'who is', 'when did', 'where is', 'how to', 
                           'why do', 'explain', 'define', 'find', 'search', 'learn about'])
        
        # Use the appropriate chain - call the function directly
        if needs_search:
            response = st.session_state.search_chain({"question": last_user_message})
        else:
            response = st.session_state.regular_chain({"question": last_user_message})
        
        # Add response to chat
        st.session_state.messages.append({"role": "assistant", "content": response, "timestamp": get_timestamp()})
        
    except Exception as e:
        # Handle errors
        error_message = f"I'm sorry, I encountered an error: {str(e)[:100]}..."
        st.session_state.messages.append({"role": "assistant", "content": error_message, "timestamp": get_timestamp()})
    
    # Set thinking to false
    st.session_state.thinking = False
    
    # Force rerun to update UI with the new message
    st.rerun()

def escape_html(text):
    """Escape HTML special characters and convert newlines to <br> tags"""
    if not text:
        return ""
    # First escape HTML special characters
    escaped = html.escape(str(text))
    # Then convert newlines to <br> tags
    return escaped.replace("\n", "<br>")

def main():
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4128/4128276.png", width=80)
    st.sidebar.title("Women's Empowerment Chat")
    
    # Topic buttons in sidebar
    st.sidebar.subheader("Popular Topics")
    topics = [
        "What is feminism?",
        "Gender equality",
        "Women in STEM",
        "Equal pay"
    ]
    
    for topic in topics:
        if st.sidebar.button(topic, key=f"topic_{topic}", use_container_width=True):
            st.session_state.user_input = topic
            process_input()
    
    # Reset button
    if st.sidebar.button("Reset Chat", type="primary", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi there! I'm your women's empowerment chatbot. What would you like to chat about today?", "timestamp": get_timestamp()}
        ]
        st.rerun()
    
    # Main title
    st.title("Women's Empowerment Chat")
    
    # Initialize API services
    initialize_api_services()
    
    # Create all message HTML at once
    messages_html = ""
    for message in st.session_state.messages:
        content = escape_html(message["content"])
        timestamp = escape_html(message.get("timestamp", ""))
        
        if message["role"] == "user":
            messages_html += '<div style="display: flex; justify-content: flex-end; margin: 10px 0;">'
            messages_html += f'<div class="user-message">{content}'
            messages_html += f'<div class="timestamp">{timestamp}</div></div></div>'
        else:
            messages_html += '<div style="display: flex; justify-content: flex-start; margin: 10px 0;">'
            messages_html += f'<div class="bot-message">{content}'
            messages_html += f'<div class="timestamp">{timestamp}</div></div></div>'
    
    # Add typing indicator if needed
    if st.session_state.thinking:
        messages_html += '<div style="display: flex; justify-content: flex-start; margin: 10px 0;">'
        messages_html += '<div class="bot-message" style="background-color:#333333; border-left: 3px solid #E91E63;">Typing...</div></div>'
    
    # Render the complete chat container with all messages
    container_html = '<div id="chat-container" style="background-color: #1E1E1E; border-radius: 10px; padding: 20px;'
    container_html += ' height: 500px; overflow-y: auto; margin-bottom: 20px; border: 1px solid #333;">'
    container_html += messages_html
    container_html += '</div>'
    
    script_html = """
    <script>
    // Auto-scroll to the bottom of the chat container
    function scrollToBottom() {
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    // Scroll when page loads
    window.onload = function() {
        scrollToBottom();
    };
    
    // Also set up a small delay to make sure content is loaded
    setTimeout(scrollToBottom, 100);
    </script>
    """
    
    st.markdown(container_html + script_html, unsafe_allow_html=True)
    
    # Generate response if thinking
    if st.session_state.thinking:
        generate_response()
    
    # Input area and send button
    input_col, button_col = st.columns([5, 1])
    
    with input_col:
        user_input = st.text_input(
            "Message",
            key="user_input",
            placeholder="Type your message here...",
            label_visibility="collapsed",
            on_change=process_input
        )
    
    with button_col:
        if st.button("💬", help="Send message"):
            process_input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Application error: {str(e)}")
        # Try to show error in streamlit if possible
        try:
            st.error(f"Application error: {str(e)}")
        except:
            pass 
