# Here we define a generation chain that uses the LLM to answer nutrition-related questions based on provided context.


from langchain_core.output_parsers import StrOutputParser       # To parse the output of the LLM as a string
from langchain_core.prompts import ChatPromptTemplate           # To create a chat prompt template for the LLM
from langchain_google_genai import ChatGoogleGenerativeAI       # To use the Google Generative AI LLM


# Initialize the LLM with the specified model and temperature
MODEL = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)


# Define the system message for the LLM
system = """You are an expert nutritionist assistant. Use the following pieces of retrieved context to answer the user's question and calculate macronutrients (Calories, Protein, Carbs, Fat, Fiber).
Always base your numbers strictly on the provided context and clearly state the portion sizes and sources used.
If multiple foods, a full recipe, or custom portions are requested, show the breakdown per item and the summed total.
If the context does not contain the nutritional information needed, state that you do not have enough information."""


# Define the chat prompt template for the LLM
# It includes the system message and the human message with placeholders for the question and context
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Question: {question} \n\n Context: {context} \n\n Answer:"),
    ]
)


# Create the generation chain by piping the prompt, LLM, and output parser
generation_chain = prompt | llm | StrOutputParser()