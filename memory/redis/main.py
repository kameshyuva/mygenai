from agent import create_agent

def main():
    print("Initializing agent and connecting to Redis...")
    agent = create_agent()
    
    print("\nAgent initialized. Ready for interaction.")
    
    # Simulating a user session
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            # The .run() method executes synchronously for the main LLM generation
            # and returns the response immediately. The threaded memory will handle
            # the facts and vectors in the background silently.
            response = agent.run(user_input)
            
            print(f"Agent: {response.response}")
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
