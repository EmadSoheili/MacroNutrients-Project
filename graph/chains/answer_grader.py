# Here I have defined a chain that grades an LLM generated answer to a user's question. 


from dotenv import load_dotenv          # To load environment variables from a .env file
load_dotenv()                           # Load environment variables from .env file

from langchain_core.prompts import ChatPromptTemplate           # To create a chat prompt template for the LLM
from langchain_google_genai import ChatGoogleGenerativeAI       # To use the Google Generative AI LLM
from pydantic import BaseModel, Field                           # To create pydantic models for LLM output


# Initialize the LLM with the specified model and temperature
MODEL = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)


# Define GradeAnswer class to assess answer's relevance to the question
class GradeAnswer(BaseModel):
    """Binary score to assess answer's relevance to the question."""

    binary_score: bool = Field(
        description="Answer adresses the question, 'True' or 'False'",
    )


# Create a structured LLM grader that uses the GradeAnswer model for output
structured_llm_grader = llm.with_structured_output(GradeAnswer)


# Define the system message for the LLM
system = """You are a grader assessing whether an answer addresses / resolves a user's nutrition question.
Give a binary score True or False. True means that the answer adresses the question completely."""


# Define the chat prompt template for the answer grader
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generated answer: {generation}",),
    ]
)

# Create the answer grader chain by piping the prompt and structured LLM grader
answer_grader = answer_prompt | structured_llm_grader