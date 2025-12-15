# Context7 Usage

When working with code generation, setup/configuration, or library/API documentation:

1. Automatically use Context7 MCP tools without explicit request
2. Always call `resolve-library-id` first to get the correct library ID
3. Then use `get-library-docs` to fetch up-to-date documentation

Use Context7 for:
- Library/framework usage examples
- API reference and documentation
- Setup and configuration guides
- Best practices and patterns

## Preferred Library IDs

For commonly used libraries, use these IDs directly with `get-library-docs`:

### AI/LLM Framework
- LangGraph: `/langchain-ai/langgraph`
- LangChain: `/langchain-ai/langchain`
- Langfuse: `/langfuse/langfuse-docs`
- FastMCP: `/jlowin/fastmcp`

### Python
- FastAPI: `/fastapi/fastapi`
- Python 3.11: `/websites/python_3_11`
- Python 3.12: `/websites/python_3_12`
- Python 3.13: `/websites/python_3_13`
- Python 3.14: `/websites/python_3_14`
- Python 3.15: `/websites/python_3_15`

### Java/Spring
- Spring Framework: `/spring-projects/spring-framework`
- Spring Boot: `/spring-projects/spring-boot`
- Spring Batch: `/spring-projects/spring-batch`
- Guava: `/google/guava`

### JavaScript/Node.js
- Next.js: `/vercel/next.js`
- Node.js: `/nodejs/node`
- Deno: `/denoland/deno`
- Lodash: `/lodash/lodash`
- Jest: `/jestjs/jest`
- NestJS: `/nestjs/nest`

### Frontend/Visualization
- Bootstrap 5.3: `/websites/getbootstrap_5_3`
- D3.js: `/d3/d3`
- Three.js: `/mrdoob/three.js`
- Chart.js: `/chartjs/chart.js`

### Database/Search
- Elasticsearch: `/elastic/elasticsearch`
- OpenSearch: `/opensearch-project/opensearch`
- Redis (docs): `/redis/docs`
- Redis (website): `/websites/redis_io`

### Infrastructure/DevOps
- Kubernetes: `/kubernetes/kubernetes`
- Kubernetes (website): `/websites/kubernetes_io`
- Docker: `/docker/docs`
- Nginx: `/nginx/nginx`
- Nginx (website): `/websites/nginx_en`
- Jenkins: `/jenkinsci/jenkins`
- n8n: `/n8n-io/n8n-docs`

### Auth/Security
- Keycloak: `/keycloak/keycloak`
