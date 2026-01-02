"""
Test script for the research agent.
Run this to verify the agent works before deploying.
"""

from agent import ResearchAgent
import config


def print_event(event):
    """Print events in a readable format"""
    event_type = event['type']

    if event_type == 'thinking':
        print(f"\n💭 THINKING:")
        print(f"   {event['content'][:200]}...")

    elif event_type == 'tool_use':
        print(f"\n🔧 TOOL USE: {event['tool']}")
        print(f"   Input: {event['input']}")

    elif event_type == 'tool_result':
        print(f"\n✅ TOOL RESULT: {event['summary']}")


def main():
    """Test the agent with a sample question"""

    print("=" * 60)
    print("RESEARCH AGENT TEST")
    print("=" * 60)

    # Initialize agent
    agent = ResearchAgent(api_key=config.ANTHROPIC_API_KEY)

    # Test questions
    questions = [
        "What are the latest developments in quantum computing?",
        "Who won the most recent Nobel Prize in Physics?"
    ]

    for question in questions:
        print(f"\n\nQUESTION: {question}")
        print("-" * 60)

        try:
            # Run research
            result = agent.research(question, stream_callback=print_event)

            # Print results
            print("\n" + "=" * 60)
            print(f"COMPLETED IN {result['iterations']} ITERATIONS")
            print("=" * 60)

            print(f"\n📝 ANSWER:")
            print(result['answer'])

            print(f"\n🔗 SOURCES ({len(result['sources'])}):")
            for source in result['sources']:
                print(f"   - {source['url']}")

            print(f"\n✅ SUCCESS: {result['success']}")

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
