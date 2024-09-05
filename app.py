import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMMathChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.agents.agent_types import AgentType
from langchain.agents import Tool, initialize_agent
from langchain.callbacks import StreamlitCallbackHandler

# Set up the Streamlit app with title and page icon
st.set_page_config(page_title="Aditya Math AI Chatbot", page_icon="🧮")
st.title("Aditya Math AI Chatbot")

# Display a welcome message
st.write("Hi, I'm a Math chatbot who can answer all your simple math questions!")

groq_api_key = st.sidebar.text_input(label="Groq API Key", type="password")

if not groq_api_key:
    st.info("Please add your Groq API key to continue")
    st.stop()

# Initialize the LLM using ChatGroq
llm = ChatGroq(model="Gemma2-9b-It", groq_api_key=groq_api_key)

## Initializing the tools
wikipedia_wrapper = WikipediaAPIWrapper()
wikipedia_tool = Tool(
    name="Wikipedia",
    func=wikipedia_wrapper.run,
    description="A tool for searching the Internet to find various information on the topics mentioned"
)

## Initialize the Math tool
math_chain = LLMMathChain.from_llm(llm=llm)
calculator = Tool(
    name="Calculator",
    func=math_chain.run,
    description="A tool for answering math-related questions. Only input mathematical expressions need to be provided"
)

# Create a prompt template for solving math problems
prompt = """
You are an agent tasked with solving users' mathematical questions. Logically arrive at the solution and provide a detailed explanation.
Display the answer stepwise for the question below.
Question: {question}
Answer:
"""

prompt_template = PromptTemplate(
    input_variables=["question"],
    template=prompt
)

## Combine all the tools into a chain for reasoning
chain = LLMChain(llm=llm, prompt=prompt_template)

reasoning_tool = Tool(
    name="Reasoning Tool",
    func=chain.run,
    description="A tool for answering logic-based and reasoning questions."
)

## Initialize the agents
assistant_agent = initialize_agent(
    tools=[wikipedia_tool, calculator, reasoning_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)

## Chat interaction
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "continue_chat" not in st.session_state:
    st.session_state["continue_chat"] = True

# Only show the input area if the user has chosen to continue the chat
if st.session_state["continue_chat"]:
    # User input for the math question
    question = st.text_area("Enter your math question:", "")

    if st.button("Find my answer"):
        if question:
            with st.spinner("Generating response..."):
                # Add user input to session state for conversation history
                st.session_state.messages.append({"role": "user", "content": question})
                st.chat_message("user").write(question)

                # Generate response
                try:
                    st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
                    
                    # Correct handling to avoid repetition and invalid responses
                    response = assistant_agent.run(st.session_state.messages, callbacks=[st_cb])
                    
                    # Ensure the response doesn't repeat "Complete!" unnecessarily
                    if "Complete!" not in response:
                        st.session_state.messages.append({'role': 'assistant', "content": response})
                        st.write('### Response:')
                        st.success(response)
                    else:
                        st.error("There was an issue processing your question. Please try again.")

                    # Ask if the user wants to continue asking more questions
                    continue_chat = st.radio("Would you like to ask another question?", ("Yes", "No"))
                    if continue_chat == "No":
                        st.session_state["continue_chat"] = False
                        st.write("Thanks for using Aditya Math AI Chatbot!")
                except ValueError as e:
                    st.error(f"Error processing the question: {e}")
        else:
            st.warning("Please enter a question")

# Display creator information
st.write("---")
st.write("Created by Aditya Raj")
