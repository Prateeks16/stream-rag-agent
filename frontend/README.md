# Stream RAG Agent frontend

This is a dependency-free static frontend for the Go query API. Deploy the
`frontend` directory as the Vercel project root. After deployment, enter the
public Go API URL in the **Agent endpoint** field; it is persisted in the
browser for the next visit.

The frontend starts in **Use demo data** mode, which returns representative
financial transaction and sensor answers without requiring Kafka, Elasticsearch,
Ollama, or the Go API. Turn the toggle off to use the live `/query` endpoint.

The visible demo events are listed below the query panel. To generate real
Kafka messages instead, start the infrastructure and run from `python/`:

```bash
strag-producer --topic financial --rate 1 --count 10
strag-producer --topic sensor --rate 1 --count 10
```

The Go agent consumes those topics, creates windows, embeds them, and makes them
available through the live API.

For local development, serve this directory with any static server and run the
Go agent on `http://localhost:8080`.