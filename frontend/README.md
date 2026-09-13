# Stream RAG Agent frontend

This is a dependency-free static frontend for the Go query API. Deploy the
`frontend` directory as the Vercel project root. After deployment, enter the
public Go API URL in the **Agent endpoint** field; it is persisted in the
browser for the next visit.

For local development, serve this directory with any static server and run the
Go agent on `http://localhost:8080`.