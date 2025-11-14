from flask import Response

@app.server.route('/healthz')
def health_check():
    """Health check endpoint for Render.com"""
    return Response("OK", status=200)
