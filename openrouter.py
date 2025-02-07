import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

load_dotenv()  # Load .env file

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url=os.environ.get("OPENROUTER_BASE_URL"),
)

def chat_with_model(model_name="mistralai/mistral-medium"):
    """
    Starts an interactive chat session with the specified model.

    Args:
        model_name: The name of the model to use.  Defaults to mistral-medium.
    """
    messages = []  # Initialize an empty conversation history

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == "exit":  # Allow the user to exit
                print("Exiting chat.")
                break

            messages.append({"role": "user", "content": user_input})

            try:
                chat_completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7,
                    top_p=1,
                    seed=12345,
                    user="my-test-user",  #  Use a consistent user ID
                    # headers={
                    #     "HTTP-Referer": "https://your-website.com", #  Your website
                    #     "X-Title": "Your-App-Name", # Your app's name
                    # },
                )

                response = chat_completion.choices[0].message.content
                print(f"Model: {response}")

                # Add the model's response to the conversation history
                messages.append({"role": "assistant", "content": response})

            except APIError as e:
                print(f"OpenAI API Error: {e}")
                # Consider adding retry logic here, or handling specific error codes
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                #  Log the error for debugging

        except KeyboardInterrupt:  # Handle Ctrl+C gracefully
            print("\nExiting chat.")
            break

if __name__ == "__main__":
    chat_with_model("openai/gpt-4o-mini")
