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
- LlamaIndex: `/run-llama/llama_index`
- Langfuse: `/langfuse/langfuse-docs`
- Langflow: `/langflow-ai/langflow`
- FastMCP: `/jlowin/fastmcp`
- OpenAI Platform: `/websites/platform_openai`

### Python
- FastAPI: `/fastapi/fastapi`
- Django: `/django/django`
- Flask: `/pallets/flask`
- PyTorch: `/pytorch/pytorch`
- Pandas: `/pandas-dev/pandas`
- SQLAlchemy: `/sqlalchemy/sqlalchemy`
- Streamlit: `/streamlit/streamlit`
- HTTPX: `/encode/httpx`
- Tenacity: `/jd/tenacity`
- structlog: `/hynek/structlog`
- Boto3: `/boto/boto3`
- aiomysql: `/aio-libs/aiomysql`
- asynch: `/long2ice/asynch`
- python-jose: `/mpdavis/python-jose`
- Python 3.11: `/websites/python_3_11`
- Python 3.12: `/websites/python_3_12`
- Python 3.13: `/websites/python_3_13`
- Python 3.14: `/websites/python_3_14`
- Python 3.15: `/websites/python_3_15`

### Java/Spring
- Spring Framework: `/spring-projects/spring-framework`
- Spring Boot: `/spring-projects/spring-boot`
- Spring AI: `/spring-projects/spring-ai`
- Spring Security: `/spring-projects/spring-security`
- Spring Batch: `/spring-projects/spring-batch`
- Spring Integration: `/spring-projects/spring-integration`
- Spring Kafka: `/spring-projects/spring-kafka`
- Spring Data JPA: `/spring-projects/spring-data-jpa`
- Spring Data Redis: `/spring-projects/spring-data-redis`
- Spring Data MongoDB: `/spring-projects/spring-data-mongodb`
- Guava: `/google/guava`
- Feign: `/openfeign/feign`
- QueryDSL: `/openfeign/querydsl`
- jOOQ: `/jooq/jooq`
- Kotlin JDSL: `/line/kotlin-jdsl`
- Flyway: `/flyway/flyway`
- Spring REST Docs: `/spring-projects/spring-restdocs`
- Netty: `/netty/netty`
- Armeria: `/line/armeria`

### JavaScript/Node.js
- Next.js: `/vercel/next.js`
- Node.js: `/nodejs/node`
- Deno: `/denoland/deno`
- NestJS: `/nestjs/nest`
- Axios: `/axios/axios`
- TanStack Query: `/tanstack/query`
- Lodash: `/lodash/lodash`
- jQuery: `/jquery/jquery`
- Day.js: `/iamkun/dayjs`
- Jest: `/jestjs/jest`

### Frontend/Visualization
- Bootstrap 5.3: `/websites/getbootstrap_5_3`
- Tailwind CSS: `/websites/tailwindcss`
- Shadcn UI: `/websites/ui_shadcn`
- D3.js: `/d3/d3`
- Three.js: `/mrdoob/three.js`
- Chart.js: `/chartjs/chart.js`

### Database/Search
- Elasticsearch: `/elastic/elasticsearch`
- OpenSearch: `/opensearch-project/opensearch`
- Qdrant: `/qdrant/qdrant`
- Redis (docs): `/redis/docs`
- Redis (website): `/websites/redis_io`

### Infrastructure/DevOps
- Kubernetes: `/kubernetes/kubernetes`
- Kubernetes (website): `/websites/kubernetes_io`
- Docker: `/docker/docs`
- Nginx: `/nginx/nginx`
- Nginx (website): `/websites/nginx_en`
- Jenkins: `/jenkinsci/jenkins`
- n8n: `/n8n-io/n8n`
- n8n (docs): `/n8n-io/n8n-docs`
- ArgoCD: `/argoproj/argo-cd`
- Helm: `/helm/helm`
- Helm (website): `/websites/helm_sh`
- Istio: `/istio/istio`
- Istio (website): `/websites/istio_io`
- Envoy: `/envoyproxy/envoy`
- Kong: `/kong/kong`
- Harbor: `/goharbor/harbor`
- Fluentd: `/fluent/fluentd`
- containerd: `/containerd/containerd`
- Cilium: `/cilium/cilium`
- Cilium (website): `/websites/cilium_io-en-stable`
- gRPC: `/grpc/grpc`

### Monitoring/Observability
- Prometheus: `/prometheus/prometheus`
- Prometheus (docs): `/prometheus/docs`
- Sentry (JavaScript): `/getsentry/sentry-javascript`
- Sentry (Java): `/getsentry/sentry-java`
- Sentry (Python): `/getsentry/sentry-python`

### GIS
- GeoServer: `/geoserver/geoserver`

### Data Engineering
- Apache Airflow: `/apache/airflow`
- Apache Spark: `/apache/spark`

### Auth/Security
- Keycloak: `/keycloak/keycloak`
