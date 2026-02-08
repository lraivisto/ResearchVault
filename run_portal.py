
import sys
import os
import uvicorn

if __name__ == "__main__":
    # Add the current directory to sys.path so we can import 'scripts' and 'portal'
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the uvicorn server
    uvicorn.run("portal.backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
