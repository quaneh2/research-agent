"""
Flask application with SSE streaming for real-time agent updates.
"""

from flask import Flask, render_template, request, Response, jsonify
import json
import config
from agent import ResearchAgent
import threading
import time

app = Flask(__name__)

# Initialize agent on startup
agent = ResearchAgent(api_key=config.ANTHROPIC_API_KEY)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/research', methods=['POST'])
def research():
    """
    Research endpoint with Server-Sent Events streaming.

    Streams agent progress in real-time:
    - thinking events: Claude's reasoning
    - tool_use events: When tools are called
    - tool_result events: Tool execution results
    - complete event: Final answer
    - error event: If something goes wrong
    """
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    def generate_with_streaming():
        """Generator that properly streams agent events"""

        events_queue = []

        def stream_callback(event):
            """Collect events to stream"""
            events_queue.append(event)

        result_container = {}

        def run_research():
            try:
                result = agent.research(question, stream_callback)
                result_container['result'] = result
                result_container['done'] = True
            except Exception as e:
                result_container['error'] = str(e)
                result_container['done'] = True

        # Start research in thread
        thread = threading.Thread(target=run_research)
        thread.start()

        # Stream events as they come
        while not result_container.get('done'):
            if events_queue:
                event = events_queue.pop(0)
                event_type = event['type']
                event_data = json.dumps(event)
                yield f"event: {event_type}\n"
                yield f"data: {event_data}\n\n"
            else:
                time.sleep(0.1)  # Small delay to avoid busy waiting

        # Send remaining events
        while events_queue:
            event = events_queue.pop(0)
            event_type = event['type']
            event_data = json.dumps(event)
            yield f"event: {event_type}\n"
            yield f"data: {event_data}\n\n"

        # Send final result or error
        if 'error' in result_container:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': result_container['error']})}\n\n"
        else:
            yield f"event: complete\n"
            yield f"data: {json.dumps(result_container['result'])}\n\n"

    return Response(
        generate_with_streaming(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
