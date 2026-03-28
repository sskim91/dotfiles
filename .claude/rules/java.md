# Java Dependency Installation

Always check the latest version on Maven Central before adding dependencies:

```bash
curl -s "https://search.maven.org/solrsearch/select?q=g:<groupId>%20AND%20a:<artifactId>&rows=1&wt=json" | jq -r '.response.docs[0].latestVersion'
```
