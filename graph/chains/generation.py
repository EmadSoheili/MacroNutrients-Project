# Here I have defined a generation chain that uses the LLM to answer nutrition-related questions based on provided context.


from dotenv import load_dotenv          # To load environment variables from a .env file
load_dotenv()                           # Load environment variables from .env file

from pydantic import BaseModel, Field                           # To define a Pydantic model for the output of the generation chain
from langchain_core.prompts import ChatPromptTemplate           # To create a chat prompt template for the LLM
from langchain_google_genai import ChatGoogleGenerativeAI       # To use the Google Generative AI LLM


# Initialize the LLM with the specified model and temperature
MODEL = "gemini-3.5-flash-lite"
llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0.0)


# Define a Pydantic model for the output of the generation chain
class GenerationOutput(BaseModel):
    answer: str = Field(description="Detailed markdown breakdown and summed total of the meal.")
    calories: float = Field(default=0.0, description="Total summed calories for this meal.")
    protein_g: float = Field(default=0.0, description="Total summed protein in grams.")
    carbs_g: float = Field(default=0.0, description="Total summed carbs in grams.")
    fat_g: float = Field(default=0.0, description="Total summed fat in grams.")
    fiber_g: float = Field(default=0.0, description="Total summed fiber in grams.")


# Create a structured LLM that uses the defined Pydantic model for output
structured_llm = llm.with_structured_output(GenerationOutput)


# Define the system message for the LLM
system = """You are a decisive, helpful nutritionist assistant. Use the retrieved context to calculate macronutrients (Calories, Protein, Carbs, Fat, Fiber).

Follow these rules in strict order:
1. **Non-Food / Zero Data Guard (STOP HERE IF APPLICABLE):** If the user's input is nonsense, not an edible food/drink item (e.g., "spaceship", "car"), or the retrieved context contains zero relevant nutritional data for any requested item, DO NOT output the nutritional breakdown template. Simply state clearly in 1-2 sentences that you can only calculate nutritional values for food and beverage items, and no nutritional data was found for the request.
2. **Handle Missing Minor Values:** If valid food data is found, calculate and provide the numbers using the best matching item(s). Treat missing minor values (like fiber) as 0g and note it briefly.
3. **Resolve Ambiguity:** If multiple matching food options exist in the context, pick the single most standard/common option, calculate the macros for it, and explicitly list which option you chose and what alternatives were available.
4. **Formatting (For Valid Food Queries Only):** Format the `answer` field strictly using Markdown headers, bullet points, and line breaks following this exact structure:

### Selected Options
- **[Requested Food]**: Chose **[Chosen Item]** (Available options: [Other Options])

### Breakdown per Item
- **[Item Name]** (Portion: [Size], Source: [Source]):
  - Calories: [X] kcal
  - Protein: [X] g
  - Carbs: [X] g
  - Fat: [X] g
  - Fiber: [X] g

### Summed Total
- **Calories:** [Total] kcal
- **Protein:** [Total] g
- **Carbs:** [Total] g
- **Fat:** [Total] g
- **Fiber:** [Total] g"""


# Define the chat prompt template for the LLM
# It includes the system message and the human message with placeholders for the question and context
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Question: {question} \n\n Context: {context} \n\n Answer:"),
    ]
)


# Create the generation chain by piping the prompt, LLM, and output parser
generation_chain = prompt | structured_llm