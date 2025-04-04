import random
import invbot

responses = {
    "hello":["Hello","Hi","Hey! How can i help you ?"],
    "hi":["Hello","Hi","Hey! How can i help you ?"],
    "how are you":["I am fine","I am fine , How are you ?"],
    "i am fine":["How can I help you ?","Good! How can I help you with ?"],
    "can you analyze the stock price ":["Sure! Please tell me the name of the company of which I want to analyze","Yes! Please provide me the company name for the stock prediction","Provide the company name for which you need the stock prediction"],
    "stock prediction":["Provide the company name for which you need the stock prediction"],
    "analyze":["Yes! Please provide me the company name for the stock prediction"]
}
def get_stock_predictions(company_name):
    return invbot.analyze_stock(company_name)

def chatbot_response(user_input):
    user_input=user_input.lower()
    if "analyze" in user_input or "stock" in user_input:
        words = user_input.split()
        ticker = words[-1].upper()
        return get_stock_predictions(ticker)
    return random.choice(responses.get(user_input))

while True:
    user_input=input("You : ")
    if user_input.lower()=="Exit":
        print("Goodbye,Have a nice day!")
        break
    print("Chatbot : ",chatbot_response(user_input))

                         
